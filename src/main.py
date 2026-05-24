from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import io
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, UploadFile, Header

try:
    import boto3
    from botocore.config import Config
    _BOTO3_AVAILABLE = True
except Exception:
    _BOTO3_AVAILABLE = False
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    _APSCHEDULER_AVAILABLE = True
except Exception:
    _APSCHEDULER_AVAILABLE = False

from src.config import settings
from src.image_manager import ImageEntry, ImageManager
from src.image_processor import ImageProcessor
from src.metrics import MetricsTracker
from src.observer import start_watching
from src.seed import seed_images

# ── Logging Setup ───────────────────────────────────────────────────
def setup_logging():
    """Configure logging with console output only."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | [PID:%(process)d] | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# ── Git version ────────────────────────────────────────────────────
def _get_git_version() -> str:
    env_version = os.environ.get("GIT_VERSION")
    if env_version and env_version != "dev":
        return env_version
    try:
        import subprocess
        # git describe gives: <tag>-<commits-since-tag>-g<short-hash>
        # e.g. 0.9-87-g929a1dad — falls back to just short hash if no tags
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "dev"

_git_version = _get_git_version()

# ── Request Coalescing (thundering herd protection) ─────────────────
# Deduplicate identical in-flight image processing requests
_inflight: dict[str, asyncio.Event] = {}
_inflight_lock = asyncio.Lock()


async def _claim_inflight(key: str) -> asyncio.Event | None:
    """Claim responsibility for processing a request. Returns None if already claimed."""
    async with _inflight_lock:
        if key in _inflight:
            return _inflight[key]
        event = asyncio.Event()
        _inflight[key] = event
        return None


async def _release_inflight(key: str) -> None:
    """Signal completion and remove the in-flight key."""
    async with _inflight_lock:
        event = _inflight.pop(key, None)
        if event is not None:
            event.set()


# ── Setup ───────────────────────────────────────────────────────────
app = FastAPI(title="PlacePix", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "HEAD", "OPTIONS", "POST"],
    allow_headers=["*"],
    expose_headers=["ETag", "Last-Modified", "Content-Length", "Cache-Control"],
    max_age=86400,
)

# Seed images if enabled
if settings.seed_enabled:
    logger.info(f"Seeding sample images in: {settings.seed_dir}")
    seed_images(settings.seed_dir)
else:
    logger.info("Seed images disabled")

# In-memory image registry
logger.info(f"Loading image registry from: {settings.images_dir} and {settings.seed_dir}")
manager = ImageManager()
logger.info(f"Registry loaded: {manager.total} images in {len(manager.categories)} categories")

processor = ImageProcessor(
    min_width=settings.min_width,
    max_width=settings.max_width,
    min_height=settings.min_height,
    max_height=settings.max_height,
)

# Watchdog hot-reload (only start in leader worker)
if manager._is_leader:
    logger.info("Starting file watcher for hot-reload")
    _observer = start_watching(manager)
else:
    logger.info("File watcher skipped (not leader worker)")
    _observer = None

# Cache cleaner class for TTL-based cleanup
class CacheCleaner:
    """Remove cached files older than a configurable TTL."""

    def __init__(self, cache_dir: Path, ttl_hours: int) -> None:
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours

    def run(self) -> None:
        if self.ttl_hours <= 0:
            return
        cutoff = time.time() - (self.ttl_hours * 3600)
        removed = 0
        freed_bytes = 0
        for subdir in self.cache_dir.iterdir():
            if not subdir.is_dir() or len(subdir.name) != 2:
                continue
            for file_path in subdir.iterdir():
                if not file_path.is_file():
                    continue
                try:
                    mtime = file_path.stat().st_mtime
                    if mtime < cutoff:
                        freed_bytes += file_path.stat().st_size
                        file_path.unlink()
                        removed += 1
                except Exception:
                    pass
            # Remove empty subdirs
            try:
                if not any(subdir.iterdir()):
                    subdir.rmdir()
            except Exception:
                pass
        if removed:
            logger.info(
                f"Cache cleanup: removed {removed} stale files, freed {freed_bytes / 1024 / 1024:.2f} MB"
            )

# Scheduler (only start in leader worker)
_scheduler = None
if manager._is_leader and _APSCHEDULER_AVAILABLE:
    _scheduler = BackgroundScheduler()

    if settings.cache_ttl_hours > 0:
        logger.info(
            f"Starting cache cleanup scheduler (TTL: {settings.cache_ttl_hours}h, "
            f"interval: {settings.cache_cleanup_interval_minutes}m)"
        )
        _cache_cleaner = CacheCleaner(settings.cache_dir, settings.cache_ttl_hours)
        _scheduler.add_job(
            _cache_cleaner.run,
            "interval",
            minutes=settings.cache_cleanup_interval_minutes,
        )

    # One-time color scan at startup (slight delay so the server is responsive first)
    logger.info("Scheduling one-time background color scan")
    _scheduler.add_job(
        manager.scan_colors,
        "date",
        run_date=datetime.now() + timedelta(seconds=5),
    )
    _scheduler.start()

# Upload directory writability check
_upload_writable = False
if settings.upload_enabled:
    if not os.access(settings.images_dir, os.W_OK):
        logger.warning(
            f"Uploads are enabled but the image directory is not writable: {settings.images_dir}. "
            "Upload functionality will be hidden in the UI."
        )
        _upload_writable = False
    else:
        logger.info(f"Upload directory is writable: {settings.images_dir}")
        _upload_writable = True

# Metrics tracker (always enabled)
logger.info("Metrics tracking enabled")
metrics_tracker = MetricsTracker()

# Templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("Static files mounted at /static")

logger.info(f"PlacePix ready - listening on {settings.bind_host}:{settings.bind_port}")


# ── Metrics Middleware ──────────────────────────────────────────────
class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log the request
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {response_time_ms:.2f}ms"
        )
        
        # Extract metadata from request
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        
        # Try to extract image metadata from path
        category = None
        width = None
        height = None
        format_ext = None
        cache_hit = response.headers.get("X-Cache-Hit") == "true"
        
        # Parse path for metadata
        path_parts = endpoint.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0].isdigit() and path_parts[1].isdigit():
            width = int(path_parts[0])
            height = int(path_parts[1])
            if len(path_parts) > 2:
                category = path_parts[2].split(".")[0]
                if "." in path_parts[2]:
                    format_ext = path_parts[2].split(".")[1]
        
        # Log the request
        try:
            metrics_tracker.log_request(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                category=category,
                width=width,
                height=height,
                format=format_ext,
                cache_hit=cache_hit,
            )
        except Exception:
            pass  # Don't fail requests if metrics logging fails
        
        return response


if metrics_tracker:
    app.add_middleware(MetricsMiddleware)


# ── Helpers ─────────────────────────────────────────────────────────
# Preset dimensions for common use cases
PRESETS = {
    # Social media
    "facebook-cover": (820, 312),
    "twitter-header": (1500, 500),
    "instagram-square": (1080, 1080),
    "instagram-portrait": (1080, 1350),
    "youtube-thumbnail": (1280, 720),
    # Ad sizes
    "leaderboard": (728, 90),
    "banner": (468, 60),
    "skyscraper": (160, 600),
    "rectangle": (300, 250),
    # Screen sizes
    "mobile": (375, 667),
    "tablet": (768, 1024),
    "desktop": (1920, 1080),
    "4k": (3840, 2160),
}


def _parse_aspect_ratio(ratio_str: str, height: int) -> tuple[int, int]:
    """Parse aspect ratio string like '16:9' and calculate width."""
    try:
        parts = ratio_str.split(":")
        if len(parts) != 2:
            return 0, 0
        w_ratio = float(parts[0])
        h_ratio = float(parts[1])
        width = int(height * (w_ratio / h_ratio))
        return width, height
    except (ValueError, ZeroDivisionError):
        return 0, 0


def _cache_path(
    entry: ImageEntry,
    width: int,
    height: int,
    fmt: str,
    grayscale: bool,
    blur: int,
    text: str,
    fit: str,
    tint: str = "",
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sepia: bool = False,
    border: str = "",
    padding: int = 0,
    noise: int = 0,
    pixelate: int = 0,
    quality: int = 85,
    lqip: bool = False,
    watermark: str = "",
    watermark_config: dict | None = None,
) -> Path:
    """Build a deterministic flat cache file path using SHA256 hash."""
    hash_input: dict[str, Any] = {
        "image_id": entry.id,
        "width": width,
        "height": height,
        "fmt": fmt,
        "grayscale": grayscale,
        "blur": blur,
        "text": text,
        "fit": fit,
        "tint": tint,
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "sepia": sepia,
        "border": border,
        "padding": padding,
        "noise": noise,
        "pixelate": pixelate,
        "quality": quality,
        "lqip": lqip,
        "watermark": watermark,
    }
    if watermark_config:
        hash_input["watermark_config"] = {
            "image": watermark_config.get("watermark_image", ""),
            "text": watermark_config.get("watermark_text", ""),
            "position": watermark_config.get("watermark_position", ""),
            "opacity": watermark_config.get("watermark_opacity", 0.5),
        }

    # Include source file mtime for local files to auto-invalidate when source changes
    if entry.path is not None and entry.path.exists():
        hash_input["source_mtime"] = entry.path.stat().st_mtime
    elif entry.s3_key:
        hash_input["s3_key"] = entry.s3_key

    # Deterministic JSON serialization
    hash_str = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(hash_str.encode()).hexdigest()

    # Flat layout: .cache/<first_2_hex>/<full_hash>.<fmt>
    cache_subdir = settings.cache_dir / digest[:2]
    cache_subdir.mkdir(parents=True, exist_ok=True)
    return cache_subdir / f"{digest}.{fmt}"


def _read_cached(cache_path: Path) -> bytes | None:
    try:
        return cache_path.read_bytes()
    except Exception:
        return None


def _write_cache(cache_path: Path, data: bytes) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)


def _generate_etag(content: bytes) -> str:
    """Generate ETag from content hash."""
    return f'"{hashlib.md5(content).hexdigest()}"'


def _get_last_modified(path: Path) -> str:
    """Get Last-Modified header from file mtime."""
    mtime = path.stat().st_mtime
    dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def _check_not_modified(
    if_none_match: str | None,
    if_modified_since: str | None,
    etag: str,
    last_modified: str,
) -> bool:
    """Check if client cache is still valid."""
    if if_none_match:
        return if_none_match == etag
    if if_modified_since:
        return if_modified_since == last_modified
    return False


def _resolve_image_source(entry: ImageEntry) -> Path | io.BytesIO:
    """Return local path or download S3 object into a BytesIO buffer."""
    if entry.s3_key and _BOTO3_AVAILABLE and settings.s3_enabled:
        logger.debug(f"Loading S3 image: {entry.s3_key}")
        try:
            client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region or "auto",
                config=Config(signature_version="s3v4"),
            )
            response = client.get_object(Bucket=settings.s3_bucket, Key=entry.s3_key)
            return io.BytesIO(response["Body"].read())
        except Exception as e:
            logger.error(f"Failed to load S3 image {entry.s3_key}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load S3 image: {e}")
    if entry.path is None:
        raise HTTPException(status_code=500, detail="image has no local path or S3 key")
    return entry.path


# ── Image serving ───────────────────────────────────────────────────
def _build_process_key(
    entry: ImageEntry,
    width: int,
    height: int,
    output_format: str,
    grayscale: bool,
    blur: int,
    text: str,
    fit: str,
    tint: str,
    brightness: float,
    contrast: float,
    saturation: float,
    sepia: bool,
    border: str,
    padding: int,
    noise: int,
    pixelate: int,
    quality: int,
    lqip: bool,
    watermark: str,
    watermark_config: dict | None,
) -> str:
    """Build a deterministic key for request coalescing (no filesystem side effects)."""
    hash_input: dict[str, Any] = {
        "image_id": entry.id,
        "width": width,
        "height": height,
        "fmt": output_format,
        "grayscale": grayscale,
        "blur": blur,
        "text": text,
        "fit": fit,
        "tint": tint,
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "sepia": sepia,
        "border": border,
        "padding": padding,
        "noise": noise,
        "pixelate": pixelate,
        "quality": quality,
        "lqip": lqip,
        "watermark": watermark,
    }
    if watermark_config:
        hash_input["watermark_config"] = {
            "image": watermark_config.get("watermark_image", ""),
            "text": watermark_config.get("watermark_text", ""),
            "position": watermark_config.get("watermark_position", ""),
            "opacity": watermark_config.get("watermark_opacity", 0.5),
        }
    if entry.path is not None and entry.path.exists():
        hash_input["source_mtime"] = entry.path.stat().st_mtime
    elif entry.s3_key:
        hash_input["s3_key"] = entry.s3_key
    hash_str = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(hash_str.encode()).hexdigest()


async def _serve_entry(
    entry: ImageEntry,
    width: int,
    height: int,
    ext: str = "",
    grayscale: bool = False,
    blur: int = 0,
    text: str = "",
    fit: str = "crop",
    output_format: str = "",
    tint: str = "",
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sepia: bool = False,
    border: str = "",
    padding: int = 0,
    noise: int = 0,
    pixelate: int = 0,
    quality: int = 85,
    lqip: bool = False,
    watermark: str = "",
    if_none_match: str | None = None,
    if_modified_since: str | None = None,
    is_random: bool = False,
    as_base64: bool = False,
) -> Response:
    """Process and serve a single image entry with coalescing and base64 support."""
    # Validate size
    width, height = processor.clamp_size(width, height)
    if width == 0 and height == 0:
        width, height = 500, 500

    # Determine output format
    output_format = output_format or ext.lstrip(".") or "jpeg"
    output_format = output_format.lower()
    if output_format not in ("jpeg", "jpg", "png", "webp", "avif"):
        output_format = "jpeg"
    if output_format == "jpg":
        output_format = "jpeg"

    # Validate base64 size limit
    if as_base64:
        if width > settings.base64_max_size or height > settings.base64_max_size:
            raise HTTPException(
                status_code=400,
                detail=f"base64 images limited to {settings.base64_max_size}x{settings.base64_max_size} px",
            )

    # Prepare watermark config
    watermark_config = None
    if watermark and settings.watermark_enabled:
        watermark_config = {
            "watermark_image": settings.watermark_image,
            "watermark_text": settings.watermark_text,
            "watermark_position": settings.watermark_position,
            "watermark_opacity": settings.watermark_opacity,
        }

    # Build cache key
    cache_path = None
    if settings.cache:
        cache_path = _cache_path(
            entry, width, height, output_format, grayscale, blur, text, fit,
            tint, brightness, contrast, saturation, sepia,
            border, padding, noise, pixelate, quality, lqip, watermark,
            watermark_config,
        )
        cached = _read_cached(cache_path)
        if cached is not None:
            logger.debug(f"Cache hit: {entry.filename} at {width}x{height}")
            if settings.cdn:
                return RedirectResponse(url=f"{settings.cdn}/{cache_path.relative_to(settings.cache_dir)}")

            # Generate cache headers
            etag = _generate_etag(cached)
            last_modified = _get_last_modified(cache_path)

            # Check if client cache is still valid
            if _check_not_modified(if_none_match, if_modified_since, etag, last_modified):
                logger.debug(f"Client cache valid: {entry.filename}")
                return Response(status_code=304, headers={"ETag": etag, "Last-Modified": last_modified})

            return _build_image_response(
                cached, output_format, entry.category, width, height, is_random, as_base64
            )

    # Build coalescing key
    inflight_key = _build_process_key(
        entry, width, height, output_format, grayscale, blur, text, fit,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        watermark_config,
    )

    # Request coalescing: wait if another identical request is already processing
    existing_event = await _claim_inflight(inflight_key)
    if existing_event is not None:
        logger.debug(f"Coalescing request for {entry.filename} ({width}x{height})")
        await existing_event.wait()
        # After waiting, check cache again
        if settings.cache and cache_path is not None:
            cached = _read_cached(cache_path)
            if cached is not None:
                return _build_image_response(
                    cached, output_format, entry.category, width, height, is_random, as_base64
                )
        # Cache miss after waiting (evicted or error) — fall through to process ourselves
        logger.debug(f"Cache miss after coalescing, processing: {entry.filename}")
        # Re-claim since previous claim was released
        second_claim = await _claim_inflight(inflight_key)
        if second_claim is not None:
            await second_claim.wait()
            if settings.cache and cache_path is not None:
                cached = _read_cached(cache_path)
                if cached is not None:
                    return _build_image_response(
                        cached, output_format, entry.category, width, height, is_random, as_base64
                    )

    try:
        # Resolve image source
        image_source = _resolve_image_source(entry)

        # Process image
        logger.debug(f"Processing image: {entry.filename} -> {width}x{height} {output_format}")
        processed = processor.process(
            image_path=image_source,
            width=width,
            height=height,
            grayscale=grayscale,
            blur=blur,
            text=text,
            fit=fit,
            output_format=output_format,
            tint=tint,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sepia=sepia,
            border=border,
            padding=padding,
            noise=noise,
            pixelate=pixelate,
            quality=quality,
            lqip=lqip,
            watermark=watermark,
            watermark_config=watermark_config,
        )

        # Cache if enabled
        if settings.cache and cache_path is not None:
            _write_cache(cache_path, processed)
            logger.debug(f"Cached processed image: {cache_path}")
            if settings.cdn:
                return RedirectResponse(url=f"{settings.cdn}/{cache_path.relative_to(settings.cache_dir)}")
    finally:
        await _release_inflight(inflight_key)

    # Generate cache headers for new content
    etag = _generate_etag(processed)
    if entry.path is not None:
        last_modified = _get_last_modified(entry.path)
    else:
        last_modified = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Check if client cache is still valid
    if _check_not_modified(if_none_match, if_modified_since, etag, last_modified):
        return Response(status_code=304, headers={"ETag": etag, "Last-Modified": last_modified})

    return _build_image_response(
        processed, output_format, entry.category, width, height, is_random, as_base64,
        etag=etag, last_modified=last_modified,
    )


def _build_image_response(
    image_bytes: bytes,
    output_format: str,
    category: str,
    width: int,
    height: int,
    is_random: bool,
    as_base64: bool = False,
    etag: str | None = None,
    last_modified: str | None = None,
) -> Response:
    """Build the final response, optionally as base64 JSON."""
    if as_base64:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:image/{output_format};base64,{b64}"
        return JSONResponse({
            "data": data_url,
            "width": width,
            "height": height,
            "format": output_format,
        })

    content_type = f"image/{output_format}"
    filename = f"placepix-{category}-{width}x{height}.{output_format}"
    cache_control = "public, max-age=31536000, immutable" if not is_random else "public, max-age=0, must-revalidate"
    headers: dict[str, str] = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Cache-Control": cache_control,
    }
    if etag:
        headers["ETag"] = etag
    if last_modified:
        headers["Last-Modified"] = last_modified

    return Response(
        content=image_bytes,
        media_type=content_type,
        headers=headers,
    )


@app.get("/id/{image_id:int}/{width:int}/{height:int}")
@app.head("/id/{image_id:int}/{width:int}/{height:int}")
@app.get("/id/{image_id:int}/{width:int}/{height:int}.{ext}")
@app.head("/id/{image_id:int}/{width:int}/{height:int}.{ext}")
async def serve_by_id(
    image_id: int,
    width: int,
    height: int,
    ext: str = "",
    grayscale: bool = False,
    blur: int = 0,
    text: str = "",
    fit: str = "crop",
    format: str = "",  # noqa: A002
    tint: str = "",
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sepia: bool = False,
    border: str = "",
    padding: int = 0,
    noise: int = 0,
    pixelate: int = 0,
    quality: int = 85,
    lqip: bool = False,
    watermark: str = "",
    base64: bool = False,
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    logger.debug(f"Serving image by ID #{image_id} at {width}x{height}")
    entry = manager.get_by_id(image_id)
    if entry is None:
        logger.warning(f"Image not found: ID #{image_id}")
        raise HTTPException(status_code=404, detail="image not found")
    return await _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random=False, as_base64=base64,
    )


@app.get("/ratio/{ratio}/{height:int}")
@app.head("/ratio/{ratio}/{height:int}")
@app.get("/ratio/{ratio}/{height:int}/{category}")
@app.head("/ratio/{ratio}/{height:int}/{category}")
@app.get("/ratio/{ratio}/{height:int}.{ext}")
@app.head("/ratio/{ratio}/{height:int}.{ext}")
@app.get("/ratio/{ratio}/{height:int}/{category}.{ext}")
@app.head("/ratio/{ratio}/{height:int}/{category}.{ext}")
async def serve_by_ratio(
    ratio: str,
    height: int,
    ext: str = "",
    category: str = "",
    grayscale: bool = False,
    blur: int = 0,
    seed: str = "",
    text: str = "",
    fit: str = "crop",
    format: str = "",  # noqa: A002
    tint: str = "",
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sepia: bool = False,
    color: str = "",
    border: str = "",
    padding: int = 0,
    noise: int = 0,
    pixelate: int = 0,
    quality: int = 85,
    lqip: bool = False,
    watermark: str = "",
    base64: bool = False,
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    """Serve image with aspect ratio (e.g., /ratio/16:9/1080)."""
    logger.debug(f"Serving image by ratio: {ratio} at height {height}")
    width, height = _parse_aspect_ratio(ratio, height)
    if width == 0 or height == 0:
        logger.warning(f"Invalid aspect ratio format: {ratio}")
        raise HTTPException(status_code=400, detail="invalid aspect ratio format")
    
    if color:
        entry = manager.pick_by_color(color, category or None)
    else:
        entry = manager.pick(category or None, seed or None)
    if entry is None:
        logger.warning(f"Category not found for ratio: {category or 'all'}")
        raise HTTPException(status_code=404, detail="category not found")
    
    is_random = not seed
    return await _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random, as_base64=base64,
    )


@app.get("/preset/{preset_name}")
@app.head("/preset/{preset_name}")
@app.get("/preset/{preset_name}/{category}")
@app.head("/preset/{preset_name}/{category}")
@app.get("/preset/{preset_name}.{ext}")
@app.head("/preset/{preset_name}.{ext}")
@app.get("/preset/{preset_name}/{category}.{ext}")
@app.head("/preset/{preset_name}/{category}.{ext}")
async def serve_by_preset(
    preset_name: str,
    ext: str = "",
    category: str = "",
    grayscale: bool = False,
    blur: int = 0,
    seed: str = "",
    text: str = "",
    fit: str = "crop",
    format: str = "",  # noqa: A002
    tint: str = "",
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sepia: bool = False,
    color: str = "",
    border: str = "",
    padding: int = 0,
    noise: int = 0,
    pixelate: int = 0,
    quality: int = 85,
    lqip: bool = False,
    watermark: str = "",
    base64: bool = False,
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    """Serve image with preset dimensions (e.g., /preset/instagram-square)."""
    logger.debug(f"Serving image by preset: {preset_name}")
    if preset_name not in PRESETS:
        logger.warning(f"Unknown preset: {preset_name}")
        raise HTTPException(status_code=404, detail=f"unknown preset: {preset_name}")
    
    width, height = PRESETS[preset_name]
    
    if color:
        entry = manager.pick_by_color(color, category or None)
    else:
        entry = manager.pick(category or None, seed or None)
    if entry is None:
        logger.warning(f"Category not found for preset: {category or 'all'}")
        raise HTTPException(status_code=404, detail="category not found")
    
    is_random = not seed
    return await _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random, as_base64=base64,
    )


@app.get("/solid/{width:int}x{height:int}/{bg_color}")
@app.get("/solid/{width:int}x{height:int}/{bg_color}/{fg_color}")
async def solid_color_placeholder(
    width: int,
    height: int,
    bg_color: str,
    fg_color: str = "ffffff",
    text: str = "",
) -> Response:
    """Generate solid color placeholder with optional text."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Clamp size
    width = max(1, min(width, 5000))
    height = max(1, min(height, 5000))
    
    # Parse colors
    def _parse_hex(color: str) -> tuple[int, int, int]:
        h = color.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6 or not all(c in "0123456789abcdefABCDEF" for c in h):
            return (204, 204, 204)  # Default gray
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    
    bg_rgb = _parse_hex(bg_color)
    fg_rgb = _parse_hex(fg_color)
    
    # Create image
    img = Image.new("RGB", (width, height), bg_rgb)
    
    # Add text if provided
    if text:
        draw = ImageDraw.Draw(img)
        font_size = max(12, min(width, height) // 10)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), text, fill=fg_rgb, font=font)
    
    # Convert to bytes
    import io
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    content = buffer.getvalue()
    
    return Response(
        content=content,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=2592000, immutable",
            "ETag": _generate_etag(content),
        },
    )


@app.get("/svg/{width:int}/{height:int}")
async def svg_placeholder(
    width: int,
    height: int,
    bg: str = "ccc",
    fg: str = "fff",
    text: str = "",
) -> Response:
    """Return a lightweight SVG placeholder — zero Pillow processing."""
    # Clamp to sane limits
    width = max(1, min(width, 5000))
    height = max(1, min(height, 5000))

    display_text = text or f"{width}x{height}"

    # Sanitize hex colors (allow 3, 4, 6, 8 digit hex)
    def _clean_hex(raw: str, fallback: str) -> str:
        h = raw.lstrip("#")
        if all(c in "0123456789abcdefABCDEF" for c in h) and len(h) in (3, 4, 6, 8):
            return f"#{h}"
        return fallback

    bg_color = _clean_hex(bg, "#ccc")
    fg_color = _clean_hex(fg, "#fff")

    # Pick font size proportional to the smaller dimension
    font_size = min(width, height) // 8
    font_size = max(10, min(font_size, 120))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="{bg_color}"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
        fill="{fg_color}" font-family="system-ui, -apple-system, sans-serif"
        font-size="{font_size}px" font-weight="500">{display_text}</text>
</svg>"""

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=2592000, stale-while-revalidate=60, immutable",
        },
    )


@app.get("/gradient/{width:int}x{height:int}/{from_color}/{to_color}")
@app.get("/gradient/{width:int}x{height:int}/{from_color}/{to_color}.{ext}")
async def gradient_placeholder(
    width: int,
    height: int,
    from_color: str,
    to_color: str,
    ext: str = "",
    angle: int = 0,
    gradient_type: str = "linear",
) -> Response:
    """Generate gradient placeholder image (linear or radial)."""
    try:
        gradient_bytes = processor.generate_gradient(
            width, height, from_color, to_color, angle, gradient_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Determine format from extension or default to PNG
    output_format = ext.lstrip(".").lower() or "png"
    if output_format not in ("png", "jpeg", "jpg", "webp"):
        output_format = "png"

    # Re-encode if not PNG (gradient generator outputs PNG)
    if output_format != "png":
        from PIL import Image
        img = Image.open(io.BytesIO(gradient_bytes))
        buffer = io.BytesIO()
        img.save(buffer, format=output_format.upper(), optimize=True)
        gradient_bytes = buffer.getvalue()

    content_type = f"image/{output_format}"
    filename = f"placepix-gradient-{width}x{height}.{output_format}"

    return Response(
        content=gradient_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=2592000, immutable",
            "ETag": _generate_etag(gradient_bytes),
        },
    )


@app.get("/{width:int}/{height:int}/{category}")
@app.head("/{width:int}/{height:int}/{category}")
@app.get("/{width:int}/{height:int}/{category}.{ext}")
@app.head("/{width:int}/{height:int}/{category}.{ext}")
@app.get("/{width:int}/{height:int}/")
@app.head("/{width:int}/{height:int}/")
async def serve_image(
    width: int,
    height: int,
    category: str = "",
    ext: str = "",
    grayscale: bool = False,
    blur: int = 0,
    seed: str = "",
    text: str = "",
    fit: str = "crop",
    format: str = "",  # noqa: A002
    tint: str = "",
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sepia: bool = False,
    color: str = "",
    border: str = "",
    padding: int = 0,
    noise: int = 0,
    pixelate: int = 0,
    quality: int = 85,
    lqip: bool = False,
    watermark: str = "",
    base64: bool = False,
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    cat_display = category or "all"
    seed_display = seed or "random"
    logger.debug(f"Serving {width}x{height} from category '{cat_display}' (seed: {seed_display})")
    if color:
        entry = manager.pick_by_color(color, category or None)
    else:
        entry = manager.pick(category or None, seed or None)
    if entry is None:
        logger.warning(f"Category not found: {category or 'all'}")
        raise HTTPException(status_code=404, detail="category not found")
    # Random images should not be cached long-term
    is_random = not seed
    return await _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random, as_base64=base64,
    )


@app.get("/color/{hex_color}/{width:int}/{height:int}")
@app.head("/color/{hex_color}/{width:int}/{height:int}")
@app.get("/color/{hex_color}/{width:int}/{height:int}.{ext}")
@app.head("/color/{hex_color}/{width:int}/{height:int}.{ext}")
async def serve_by_color(
    hex_color: str,
    width: int,
    height: int,
    ext: str = "",
    grayscale: bool = False,
    blur: int = 0,
    text: str = "",
    fit: str = "crop",
    format: str = "",  # noqa: A002
    tint: str = "",
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sepia: bool = False,
    border: str = "",
    padding: int = 0,
    noise: int = 0,
    pixelate: int = 0,
    quality: int = 85,
    lqip: bool = False,
    watermark: str = "",
    base64: bool = False,
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    logger.debug(f"Serving image by color: {hex_color} at {width}x{height}")
    entry = manager.pick_by_color(hex_color)
    if entry is None:
        logger.warning(f"No image matching color: {hex_color}")
        raise HTTPException(status_code=404, detail="no image matching that color")
    return await _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random=True, as_base64=base64,
    )


# ── Random from all (no dimensions) ────────────────────────────────
@app.get("/random/{category:path}")
async def random_image(category: str = "", color: str = "") -> RedirectResponse:
    if color:
        entry = manager.pick_by_color(color, category or None)
    else:
        entry = manager.pick(category or None)
    if entry is None:
        raise HTTPException(status_code=404, detail="category not found")
    return RedirectResponse(url=f"/500/500/{entry.category}?seed={os.urandom(4).hex()}")


# ── Raw image serving ───────────────────────────────────────────────
_CONTENT_TYPES: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".avif": "image/avif",
    ".svg": "image/svg+xml",
}


def _serve_raw(
    entry: ImageEntry,
    if_none_match: str | None = None,
    if_modified_since: str | None = None,
) -> Response:
    """Serve the original unprocessed image file."""
    source = _resolve_image_source(entry)

    if isinstance(source, Path):
        content = source.read_bytes()
        last_modified = _get_last_modified(source)
        ext = source.suffix.lower()
    else:
        content = source.getvalue()
        last_modified = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        ext = os.path.splitext(entry.filename)[1].lower()

    etag = _generate_etag(content)

    if _check_not_modified(if_none_match, if_modified_since, etag, last_modified):
        return Response(status_code=304, headers={"ETag": etag, "Last-Modified": last_modified})

    media_type = _CONTENT_TYPES.get(ext, "application/octet-stream")

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{entry.filename}"',
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": etag,
            "Last-Modified": last_modified,
        },
    )


@app.get("/api/raw/id/{image_id:int}")
@app.head("/api/raw/id/{image_id:int}")
async def serve_raw_by_id(
    image_id: int,
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    """Serve the original unprocessed image by ID."""
    entry = manager.get_by_id(image_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="image not found")
    return _serve_raw(entry, if_none_match, if_modified_since)


@app.get("/api/raw/{category}/{filename}")
@app.head("/api/raw/{category}/{filename}")
async def serve_raw_by_path(
    category: str,
    filename: str,
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    """Serve the original unprocessed image by category and filename."""
    entry = manager.get_entry(category, filename)
    if entry is None:
        raise HTTPException(status_code=404, detail="image not found")
    return _serve_raw(entry, if_none_match, if_modified_since)


# ── Web UI ──────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> Any:
    import time
    t0 = time.perf_counter()
    categories = manager.list_categories()
    render_time = f"{(time.perf_counter() - t0) * 1000:.1f}"
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "categories": categories,
            "total": manager.total,
            "ga_tracking_id": settings.ga_tracking_id,
            "upload_enabled": settings.upload_enabled and _upload_writable,
            "git_version": _git_version,
            "render_time": render_time,
        },
    )


@app.get("/url-builder", response_class=HTMLResponse)
async def url_builder(request: Request) -> Any:
    """Interactive URL builder and feature explorer."""
    return templates.TemplateResponse(
        request,
        "url-builder.html",
        {
            "ga_tracking_id": settings.ga_tracking_id,
            "upload_enabled": settings.upload_enabled and _upload_writable,
        },
    )


@app.get("/features")
async def features_redirect() -> RedirectResponse:
    """Redirect old /features URL to /url-builder."""
    return RedirectResponse(url="/url-builder", status_code=301)


# ── API metadata ──────────────────────────────────────────────────
@app.get("/api/images")
async def api_images() -> JSONResponse:
    return JSONResponse({
        "categories": manager.list_categories(),
        "total": manager.total,
    })


@app.get("/api/categories")
async def api_categories() -> JSONResponse:
    """Get list of available image categories with metadata."""
    categories_detailed = manager.list_categories()
    category_names = [cat["name"] for cat in categories_detailed]
    
    return JSONResponse({
        "categories": category_names,
        "count": len(category_names),
        "detailed": categories_detailed,
    })


@app.get("/api/info/id/{image_id:int}")
async def image_info_by_id(image_id: int) -> JSONResponse:
    entry = manager.get_by_id(image_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="image not found")

    from PIL import Image

    source = _resolve_image_source(entry)
    with Image.open(source) as img:
        width, height = img.size
        fmt = img.format.lower() if img.format else "unknown"

    if isinstance(source, Path):
        size = source.stat().st_size
    else:
        size = len(source.getvalue())

    return JSONResponse({
        "id": entry.id,
        "filename": entry.filename,
        "category": entry.category,
        "width": width,
        "height": height,
        "format": fmt,
        "size": size,
        "colors": manager.get_colors(entry.id),
        "serve_url": f"/id/{entry.id}/500/500",
    })


@app.get("/api/info/{category}/{filename}")
async def image_info(category: str, filename: str) -> JSONResponse:
    entry = manager.get_entry(category, filename)
    if entry is None:
        raise HTTPException(status_code=404, detail="image not found")

    from PIL import Image

    source = _resolve_image_source(entry)
    with Image.open(source) as img:
        width, height = img.size
        fmt = img.format.lower() if img.format else "unknown"

    if isinstance(source, Path):
        size = source.stat().st_size
    else:
        size = len(source.getvalue())

    return JSONResponse({
        "id": entry.id,
        "filename": entry.filename,
        "category": entry.category,
        "width": width,
        "height": height,
        "format": fmt,
        "size": size,
        "colors": manager.get_colors(entry.id),
        "serve_url": f"/id/{entry.id}/500/500",
    })


@app.get("/api/color/{hex_color}")
async def api_color_match(hex_color: str) -> JSONResponse:
    matches = manager.find_by_color(hex_color)
    return JSONResponse({
        "query": hex_color,
        "count": len(matches),
        "images": [
            {
                "id": e.id,
                "filename": e.filename,
                "category": e.category,
                "colors": manager.get_colors(e.id),
                "url": f"/id/{e.id}/500/500",
            }
            for e in matches
        ],
    })


# ── Favicon ───────────────────────────────────────────────────────
@app.get("/favicon.svg")
async def favicon() -> Response:
    svg_path = Path("static/logo.svg")
    if svg_path.exists():
        return Response(content=svg_path.read_bytes(), media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="favicon not found")


# ── Health & Readiness (Docker/Kubernetes) ─────────────────────────
@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint (liveness probe)."""
    return JSONResponse({"status": "ok"})


@app.get("/ready")
async def readiness() -> JSONResponse:
    """Readiness check endpoint (ready when images are scanned)."""
    # Check if manager has scanned images
    if manager.total == 0:
        return JSONResponse(
            {"status": "not_ready", "images_loaded": 0, "categories": 0},
            status_code=503,
        )
    return JSONResponse({
        "status": "ready",
        "images_loaded": manager.total,
        "categories": len(manager.categories),
    })


# ── Image Explorer ────────────────────────────────────────────────
@app.get("/images")
async def image_explorer(page: int = 1) -> Response:
    per_page = 20
    entries, total = manager.list_entries(page=page, per_page=per_page)
    total_pages = max((total + per_page - 1) // per_page, 1)
    page = max(1, min(page, total_pages))

    cards = ""
    for entry in entries:
        thumb_url = f"/id/{entry.id}/200/150"
        view_url = f"/id/{entry.id}/800/600"
        info_url = f"/api/info/id/{entry.id}"
        cards += f"""
        <div class="card">
            <a href="{view_url}" target="_blank"><img src="{thumb_url}" alt="{entry.filename}" loading="lazy"></a>
            <div class="info">
                <div class="id">ID: <a href="{view_url}" target="_blank">{entry.id}</a></div>
                <div class="meta">{entry.category} / {entry.filename}</div>
                <div class="links">
                    <a href="{view_url}" target="_blank">view</a>
                    <a href="{info_url}" target="_blank">info</a>
                </div>
            </div>
        </div>
        """

    # Smart pagination - show limited page numbers with ellipsis
    def get_smart_pagination(current: int, total: int) -> str:
        if total <= 7:
            # Show all pages if 7 or fewer
            return "".join(
                f'<span class="page-link active">{p}</span>' if p == current
                else f'<a class="page-link" href="/images?page={p}">{p}</a>'
                for p in range(1, total + 1)
            )
        
        pages = []
        # Always show first page
        pages.append(f'<span class="page-link active">1</span>' if current == 1 else f'<a class="page-link" href="/images?page=1">1</a>')
        
        # Show ellipsis if gap after first page
        if current > 3:
            pages.append('<span class="page-link disabled">...</span>')
        
        # Show pages around current
        start = max(2, current - 1)
        end = min(total - 1, current + 1)
        for p in range(start, end + 1):
            if p == current:
                pages.append(f'<span class="page-link active">{p}</span>')
            else:
                pages.append(f'<a class="page-link" href="/images?page={p}">{p}</a>')
        
        # Show ellipsis if gap before last page
        if current < total - 2:
            pages.append('<span class="page-link disabled">...</span>')
        
        # Always show last page
        pages.append(f'<span class="page-link active">{total}</span>' if current == total else f'<a class="page-link" href="/images?page={total}">{total}</a>')
        
        return "".join(pages)
    
    prev_link = f'<a class="page-link" href="/images?page={page - 1}">Previous</a>' if page > 1 else '<span class="page-link disabled">Previous</span>'
    next_link = f'<a class="page-link" href="/images?page={page + 1}">Next</a>' if page < total_pages else '<span class="page-link disabled">Next</span>'
    page_numbers = get_smart_pagination(page, total_pages)

    return templates.TemplateResponse(
        "explorer.html",
        {
            "request": None,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "cards": cards,
            "prev_link": prev_link,
            "page_numbers": page_numbers,
            "next_link": next_link,
            "upload_enabled": settings.upload_enabled,
            "upload_writable": _upload_writable,
        }
    )


# ── Color Palette ───────────────────────────────────────────────
@app.get("/palette")
async def color_palette(
    page: int = 1,
    per_page: int = 24,
    category: str = "",
    search: str = "",
) -> Response:
    try:
        all_colors = manager.list_colors(category=category, search=search)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    safe_category = html.escape(category, quote=True)
    safe_search = html.escape(search, quote=True)
    total = len(all_colors)
    total_pages = max((total + per_page - 1) // per_page, 1)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    colors = all_colors[start:end]

    swatches = ""
    for item in colors:
        hex_color = item["hex"]
        count = item["count"]
        sample_images = ""
        for sid in item["sample_ids"][:2]:
            sample_images += f'<img src="/id/{sid}/100/75" alt="" loading="lazy">'
        swatches += f"""
        <div class="swatch">
            <a href="/color/{hex_color.lstrip('#')}/400/300" target="_blank">
                <div class="color-block" style="background: {hex_color};"></div>
            </a>
            <div class="color-info">
                <code class="hex">{hex_color}</code>
                <span class="count">{count} image{"s" if count > 1 else ""}</span>
            </div>
            <div class="samples">{sample_images}</div>
        </div>
        """

    # Category filters with colored dot badges
    hue_cats = [
        ("Red", "#ef4444"), ("Orange", "#f97316"), ("Yellow", "#eab308"),
        ("Green", "#22c55e"), ("Cyan", "#06b6d4"), ("Blue", "#3b82f6"),
        ("Purple", "#a855f7"), ("Pink", "#ec4899"), ("Brown", "#a0522d"),
        ("White", "#f8fafc"), ("Gray", "#94a3b8"), ("Black", "#0f172a"),
    ]
    cat_buttons = ""
    for cat, dot_color in hue_cats:
        active = "active" if category == cat else ""
        border = "border: 1px solid #cbd5e1;" if cat in ("White", "Gray") else ""
        cat_buttons += f'<a class="cat-btn {active}" href="/palette?category={cat}&search={safe_search}"><span class="dot" style="background: {dot_color}; {border}"></span>{cat}</a>'
    all_active = "" if category else "active"
    cat_buttons = f'<a class="cat-btn {all_active}" href="/palette?search={safe_search}">All</a>' + cat_buttons

    # Smart pagination - show limited page numbers with ellipsis
    def get_smart_pagination(current: int, total: int, base_url: str) -> str:
        if total <= 7:
            # Show all pages if 7 or fewer
            return "".join(
                f'<span class="page-link active">{p}</span>' if p == current
                else f'<a class="page-link" href="{base_url}&page={p}">{p}</a>'
                for p in range(1, total + 1)
            )
        
        pages = []
        # Always show first page
        pages.append(f'<span class="page-link active">1</span>' if current == 1 else f'<a class="page-link" href="{base_url}&page=1">1</a>')
        
        # Show ellipsis if gap after first page
        if current > 3:
            pages.append('<span class="page-link disabled">...</span>')
        
        # Show pages around current
        start = max(2, current - 1)
        end = min(total - 1, current + 1)
        for p in range(start, end + 1):
            if p == current:
                pages.append(f'<span class="page-link active">{p}</span>')
            else:
                pages.append(f'<a class="page-link" href="{base_url}&page={p}">{p}</a>')
        
        # Show ellipsis if gap before last page
        if current < total - 2:
            pages.append('<span class="page-link disabled">...</span>')
        
        # Always show last page
        pages.append(f'<span class="page-link active">{total}</span>' if current == total else f'<a class="page-link" href="{base_url}&page={total}">{total}</a>')
        
        return "".join(pages)
    
    base = f"/palette?search={safe_search}"
    if safe_category:
        base += f"&category={safe_category}"
    prev_link = f'<a class="page-link" href="{base}&page={page - 1}">Previous</a>' if page > 1 else '<span class="page-link disabled">Previous</span>'
    next_link = f'<a class="page-link" href="{base}&page={page + 1}">Next</a>' if page < total_pages else '<span class="page-link disabled">Next</span>'
    page_numbers = get_smart_pagination(page, total_pages, base)

    pager = f'<div class="pager">{prev_link}{page_numbers}{next_link}</div>' if total_pages > 1 else ""

    scan_banner = ""
    if manager._scanning_colors:
        scan_banner = '<div class="scan-banner">Color scan in progress — new colors will appear shortly.</div>'

    return templates.TemplateResponse(
        "palette.html",
        {
            "request": None,
            "total": total,
            "safe_category": safe_category,
            "safe_search": safe_search,
            "cat_buttons": cat_buttons,
            "scan_banner": scan_banner,
            "swatches": swatches,
            "pager": pager,
            "upload_enabled": settings.upload_enabled,
            "upload_writable": _upload_writable,
        }
    )


# ── Upload ────────────────────────────────────────────────────────
from fastapi import Form

@app.post("/api/upload")
async def upload_image(
    file: UploadFile,
    category: str = Form(default=""),
) -> JSONResponse:
    cat_display = category or "__root"
    logger.info(f"Upload request: {file.filename} to category '{cat_display}'")
    
    if not settings.upload_enabled or not _upload_writable:
        logger.warning("Upload blocked: uploads are disabled or directory is not writable")
        raise HTTPException(status_code=403, detail="uploads are disabled")

    if not file.filename:
        logger.warning("Upload failed: no filename provided")
        raise HTTPException(status_code=400, detail="no file provided")

    target_dir = settings.images_dir
    if category:
        target_dir = target_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)

    dest = target_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)
    logger.info(f"File saved: {dest} ({len(content)} bytes)")

    # Trigger rescan
    manager.rescan()
    logger.info("Registry rescanned after upload")

    return JSONResponse({
        "success": True,
        "filename": file.filename,
        "category": category or "__root",
        "path": str(dest),
    })


# ── Srcset Generation ──────────────────────────────────────────────
@app.get("/api/srcset/{image_id:int}")
async def generate_srcset(
    image_id: int,
    sizes: str = "320,640,1024,1920",
    format: str = "jpeg",  # noqa: A002
) -> JSONResponse:
    """Generate srcset URLs for responsive images."""
    entry = manager.get_by_id(image_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="image not found")
    
    # Parse sizes
    try:
        size_list = [int(s.strip()) for s in sizes.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid sizes format")
    
    # Calculate aspect ratio from original image
    from PIL import Image
    source = _resolve_image_source(entry)
    with Image.open(source) as img:
        aspect_ratio = img.width / img.height
    
    # Generate srcset entries
    srcset_entries = []
    for width in size_list:
        height = int(width / aspect_ratio)
        url = f"/id/{image_id}/{width}/{height}.{format}"
        srcset_entries.append({
            "url": url,
            "width": width,
            "height": height,
            "descriptor": f"{width}w",
        })
    
    # Generate srcset string
    srcset_string = ", ".join(f"{e['url']} {e['descriptor']}" for e in srcset_entries)
    
    return JSONResponse({
        "id": image_id,
        "srcset": srcset_entries,
        "srcset_string": srcset_string,
        "aspect_ratio": round(aspect_ratio, 3),
    })


# ── Entry point ─────────────────────────────────────────────────────
def run() -> None:
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.bind_host,
        port=settings.bind_port,
        reload=True,
        reload_dirs=["src"],
    )


if __name__ == "__main__":
    run()
