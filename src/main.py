from __future__ import annotations

import hashlib
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
_upload_writable = True
if settings.upload_enabled:
    if not os.access(settings.images_dir, os.W_OK):
        logger.warning(
            f"Uploads are enabled but the image directory is not writable: {settings.images_dir}. "
            "Upload functionality will be hidden in the UI."
        )
        _upload_writable = False
    else:
        logger.info(f"Upload directory is writable: {settings.images_dir}")

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
def _serve_entry(
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
) -> Response:
    """Process and serve a single image entry."""
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

            content_type = f"image/{output_format}"
            filename = f"placepix-{entry.category}-{width}x{height}.{output_format}"
            cache_control = "public, max-age=31536000, immutable" if not is_random else "public, max-age=0, must-revalidate"

            return Response(
                content=cached,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{filename}"',
                    "Cache-Control": cache_control,
                    "ETag": etag,
                    "Last-Modified": last_modified,
                },
            )

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

    # Generate cache headers for new content
    etag = _generate_etag(processed)
    if entry.path is not None:
        last_modified = _get_last_modified(entry.path)
    else:
        last_modified = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Check if client cache is still valid
    if _check_not_modified(if_none_match, if_modified_since, etag, last_modified):
        return Response(status_code=304, headers={"ETag": etag, "Last-Modified": last_modified})
    
    content_type = f"image/{output_format}"
    filename = f"placepix-{entry.category}-{width}x{height}.{output_format}"
    cache_control = "public, max-age=31536000, immutable" if not is_random else "public, max-age=0, must-revalidate"
    
    return Response(
        content=processed,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": cache_control,
            "ETag": etag,
            "Last-Modified": last_modified,
        },
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
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    logger.debug(f"Serving image by ID #{image_id} at {width}x{height}")
    entry = manager.get_by_id(image_id)
    if entry is None:
        logger.warning(f"Image not found: ID #{image_id}")
        raise HTTPException(status_code=404, detail="image not found")
    return _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random=False,
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
    return _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random,
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
    return _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random,
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
    return _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random,
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
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    logger.debug(f"Serving image by color: {hex_color} at {width}x{height}")
    entry = manager.pick_by_color(hex_color)
    if entry is None:
        logger.warning(f"No image matching color: {hex_color}")
        raise HTTPException(status_code=404, detail="no image matching that color")
    return _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        border, padding, noise, pixelate, quality, lqip, watermark,
        if_none_match, if_modified_since, is_random=True,
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
    categories = manager.list_categories()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "categories": categories,
            "total": manager.total,
            "ga_tracking_id": settings.ga_tracking_id,
            "upload_enabled": settings.upload_enabled and _upload_writable,
        },
    )


@app.get("/features", response_class=HTMLResponse)
async def feature_explorer(request: Request) -> Any:
    """Interactive feature explorer and URL constructor."""
    return templates.TemplateResponse(
        request,
        "features.html",
        {"ga_tracking_id": settings.ga_tracking_id},
    )


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

    # Pagination
    prev_link = f'<a class="page-link" href="/images?page={page - 1}">Previous</a>' if page > 1 else '<span class="page-link disabled">Previous</span>'
    next_link = f'<a class="page-link" href="/images?page={page + 1}">Next</a>' if page < total_pages else '<span class="page-link disabled">Next</span>'
    page_numbers = ""
    for p in range(1, total_pages + 1):
        if p == page:
            page_numbers += f'<span class="page-link active">{p}</span>'
        else:
            page_numbers += f'<a class="page-link" href="/images?page={p}">{p}</a>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PlacePix Image Explorer</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <style>
        :root {{ --bg: #f8fafc; --card: #fff; --text: #1e293b; --muted: #64748b; --accent: #3b82f6; --border: #e2e8f0; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; padding-bottom: 2rem; }}
        nav {{ display: flex; align-items: center; justify-content: space-between; max-width: 1400px; margin: 0 auto; padding: .75rem 1.5rem; }}
        .logo {{ display: flex; align-items: center; gap: .5rem; text-decoration: none; color: var(--text); }}
        .logo img {{ width: 28px; height: 28px; }}
        .logo span {{ font-weight: 700; font-size: 1.1rem; }}
        .nav-links {{ display: flex; gap: 1.25rem; font-size: .9rem; }}
        .nav-links a {{ color: var(--muted); text-decoration: none; }}
        .nav-links a:hover {{ color: var(--accent); }}
        h1 {{ text-align: center; margin-bottom: .25rem; font-size: 1.75rem; }}
        .subtitle {{ text-align: center; color: var(--muted); margin-bottom: 1.5rem; font-size: .95rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1.25rem; max-width: 1400px; margin: 0 auto; padding: 0 1.5rem; }}
        .card {{ background: var(--card); border-radius: 12px; overflow: hidden; transition: transform .15s, box-shadow .15s; border: 1px solid var(--border); }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.08); }}
        .card img {{ width: 100%; height: 150px; object-fit: cover; display: block; }}
        .info {{ padding: .75rem 1rem; }}
        .id {{ font-weight: 600; font-size: 1rem; margin-bottom: .25rem; }}
        .id a {{ color: var(--text); text-decoration: none; }}
        .id a:hover {{ color: var(--accent); }}
        .meta {{ font-size: .8rem; color: var(--muted); margin-bottom: .5rem; }}
        .links {{ display: flex; gap: .75rem; font-size: .85rem; }}
        .links a {{ color: var(--accent); text-decoration: none; }}
        .links a:hover {{ text-decoration: underline; }}
        .pager {{ display: flex; justify-content: center; align-items: center; gap: .4rem; margin-top: 2.5rem; flex-wrap: wrap; padding: 0 1rem; }}
        .page-link {{ display: inline-block; padding: .4rem .8rem; border-radius: 8px; background: var(--card); color: var(--text); text-decoration: none; font-size: .9rem; min-width: 2.2rem; text-align: center; border: 1px solid var(--border); }}
        .page-link.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
        .page-link.disabled {{ color: var(--muted); cursor: default; }}
    </style>
</head>
<body>
    <nav>
        <a href="/" class="logo"><img src="/static/logo.svg" alt=""><span>PlacePix</span></a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/images">Explorer</a>
            <a href="/palette">Palette</a>
            <a href="/docs" target="_blank">Docs</a>
        </div>
    </nav>
    <h1>Image Explorer</h1>
    <p class="subtitle">{total} images &mdash; Page {page} of {total_pages}</p>
    <div class="grid">{cards}</div>
    <div class="pager">{prev_link}{page_numbers}{next_link}</div>
</body>
</html>"""

    return Response(content=html, media_type="text/html")


# ── Color Palette ───────────────────────────────────────────────
@app.get("/palette")
async def color_palette(
    page: int = 1,
    per_page: int = 24,
    category: str = "",
    search: str = "",
) -> Response:
    all_colors = manager.list_colors(category=category, search=search)
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
        cat_buttons += f'<a class="cat-btn {active}" href="/palette?category={cat}&search={search}"><span class="dot" style="background: {dot_color}; {border}"></span>{cat}</a>'
    all_active = "" if category else "active"
    cat_buttons = f'<a class="cat-btn {all_active}" href="/palette?search={search}">All</a>' + cat_buttons

    # Pagination
    base = f"/palette?search={search}"
    if category:
        base += f"&category={category}"
    prev_link = f'<a class="page-link" href="{base}&page={page - 1}">Previous</a>' if page > 1 else '<span class="page-link disabled">Previous</span>'
    next_link = f'<a class="page-link" href="{base}&page={page + 1}">Next</a>' if page < total_pages else '<span class="page-link disabled">Next</span>'
    page_numbers = ""
    for p in range(1, total_pages + 1):
        active = "active" if p == page else ""
        page_numbers += f'<a class="page-link {active}" href="{base}&page={p}">{p}</a>'

    pager = f'<div class="pager">{prev_link}{page_numbers}{next_link}</div>' if total_pages > 1 else ""

    scan_banner = ""
    if manager._scanning_colors:
        scan_banner = '<div class="scan-banner">Color scan in progress — new colors will appear shortly.</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PlacePix Color Palette</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <style>
        :root {{ --bg: #f8fafc; --card: #fff; --text: #1e293b; --muted: #64748b; --accent: #3b82f6; --border: #e2e8f0; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; padding-bottom: 2rem; }}
        nav {{ display: flex; align-items: center; justify-content: space-between; max-width: 1400px; margin: 0 auto; padding: .75rem 1.5rem; }}
        .logo {{ display: flex; align-items: center; gap: .5rem; text-decoration: none; color: var(--text); }}
        .logo img {{ width: 28px; height: 28px; }}
        .logo span {{ font-weight: 700; font-size: 1.1rem; }}
        .nav-links {{ display: flex; gap: 1.25rem; font-size: .9rem; }}
        .nav-links a {{ color: var(--muted); text-decoration: none; }}
        .nav-links a:hover {{ color: var(--accent); }}
        h1 {{ text-align: center; margin-bottom: .25rem; font-size: 1.75rem; }}
        .subtitle {{ text-align: center; color: var(--muted); margin-bottom: 1rem; font-size: .95rem; }}
        .controls {{ max-width: 1400px; margin: 0 auto 1.5rem; padding: 0 1.5rem; }}
        .search-bar {{ display: flex; gap: .5rem; margin-bottom: .75rem; }}
        .search-bar input {{ flex: 1; padding: .6rem 1rem; border: 1px solid var(--border); border-radius: 8px; font-size: .9rem; }}
        .search-bar button {{ padding: .6rem 1.2rem; background: var(--accent); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: .9rem; }}
        .cat-row {{ display: flex; flex-wrap: wrap; gap: .4rem; }}
        .cat-btn {{ display: inline-flex; align-items: center; gap: .4rem; padding: .35rem .75rem; border-radius: 6px; background: var(--card); border: 1px solid var(--border); color: var(--text); text-decoration: none; font-size: .85rem; }}
        .cat-btn.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
        .cat-btn:hover {{ background: #f1f5f9; }}
        .cat-btn .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 1.25rem; max-width: 1400px; margin: 0 auto; padding: 0 1.5rem; }}
        .swatch {{ background: var(--card); border-radius: 12px; overflow: hidden; border: 1px solid var(--border); transition: transform .15s, box-shadow .15s; }}
        .swatch:hover {{ transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.08); }}
        .color-block {{ width: 100%; height: 120px; display: block; }}
        .color-info {{ padding: .6rem .8rem; }}
        .hex {{ font-family: ui-monospace, monospace; font-size: .85rem; font-weight: 600; display: block; }}
        .count {{ font-size: .75rem; color: var(--muted); }}
        .samples {{ display: flex; gap: 2px; padding: 0 .8rem .8rem; }}
        .samples img {{ width: 48px; height: 36px; object-fit: cover; border-radius: 4px; }}
        .pager {{ display: flex; justify-content: center; align-items: center; gap: .4rem; margin-top: 2.5rem; flex-wrap: wrap; padding: 0 1rem; }}
        .page-link {{ display: inline-block; padding: .4rem .8rem; border-radius: 8px; background: var(--card); color: var(--text); text-decoration: none; font-size: .9rem; min-width: 2.2rem; text-align: center; border: 1px solid var(--border); }}
        .page-link.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
        .page-link.disabled {{ color: var(--muted); cursor: default; }}
        .scan-banner {{ max-width: 1400px; margin: 0 auto 1.25rem; padding: .6rem 1rem; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; color: #1d4ed8; font-size: .9rem; text-align: center; }}
    </style>
</head>
<body>
    <nav>
        <a href="/" class="logo"><img src="/static/logo.svg" alt=""><span>PlacePix</span></a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/images">Explorer</a>
            <a href="/palette">Palette</a>
            <a href="/docs" target="_blank">Docs</a>
        </div>
    </nav>
    <h1>Color Palette</h1>
    <p class="subtitle">{total} dominant colors &mdash; click any to preview matching images</p>
    <div class="controls">
        <form class="search-bar" method="get" action="/palette">
            <input type="hidden" name="category" value="{category}">
            <input type="text" name="search" placeholder="Search hex color (e.g. 3b82f6)" value="{search}">
            <button type="submit">Search</button>
        </form>
        <div class="cat-row">{cat_buttons}</div>
    </div>
    {scan_banner}
    <div class="grid">{swatches}</div>
    {pager}
</body>
</html>"""

    return Response(content=html, media_type="text/html")


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
