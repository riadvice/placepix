from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, UploadFile, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.image_manager import ImageEntry, ImageManager
from src.image_processor import ImageProcessor
from src.metrics import MetricsTracker
from src.observer import start_watching
from src.seed import seed_images

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

# Seed images if empty
seed_images(settings.images_dir)

# In-memory image registry
manager = ImageManager()
processor = ImageProcessor(
    min_width=settings.min_width,
    max_width=settings.max_width,
    min_height=settings.min_height,
    max_height=settings.max_height,
)

# Watchdog hot-reload
_observer = start_watching(manager)

# Metrics tracker (only if admin password is set)
metrics_tracker = MetricsTracker() if settings.admin_password else None

# Templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Metrics Middleware ──────────────────────────────────────────────
class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics."""

    async def dispatch(self, request: Request, call_next):
        if not metrics_tracker:
            return await call_next(request)
        
        start_time = time.time()
        response = await call_next(request)
        response_time_ms = (time.time() - start_time) * 1000
        
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
) -> Path:
    """Build a deterministic cache file path."""
    suffix = f".{fmt}"
    base = entry.filename
    if "." in base:
        base = base.rsplit(".", 1)[0]
    base += suffix

    # Include processing params in path
    parts = [f"{width}x{height}"]
    if grayscale:
        parts.append("gray")
    if sepia:
        parts.append("sepia")
    if blur:
        parts.append(f"blur{blur}")
    if text:
        parts.append(f"txt{hashlib.sha256(text.encode()).hexdigest()[:8]}")
    if fit != "crop":
        parts.append(fit)
    if tint:
        parts.append(f"tint{tint.lstrip('#')}")
    if brightness != 1.0:
        parts.append(f"bri{brightness}")
    if contrast != 1.0:
        parts.append(f"con{contrast}")
    if saturation != 1.0:
        parts.append(f"sat{saturation}")

    cache_subdir = settings.cache_dir / "_".join(parts) / entry.category
    cache_subdir.mkdir(parents=True, exist_ok=True)
    return cache_subdir / base


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

    # Build cache key
    cache_path = None
    if settings.cache:
        cache_path = _cache_path(
            entry, width, height, output_format, grayscale, blur, text, fit,
            tint, brightness, contrast, saturation, sepia,
        )
        cached = _read_cached(cache_path)
        if cached is not None:
            if settings.cdn:
                return RedirectResponse(url=f"{settings.cdn}/{cache_path.relative_to(settings.cache_dir)}")
            
            # Generate cache headers
            etag = _generate_etag(cached)
            last_modified = _get_last_modified(cache_path)
            
            # Check if client cache is still valid
            if _check_not_modified(if_none_match, if_modified_since, etag, last_modified):
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

    # Process image
    processed = processor.process(
        image_path=entry.path,
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
    )

    # Cache if enabled
    if settings.cache and cache_path is not None:
        _write_cache(cache_path, processed)
        if settings.cdn:
            return RedirectResponse(url=f"{settings.cdn}/{cache_path.relative_to(settings.cache_dir)}")

    # Generate cache headers for new content
    etag = _generate_etag(processed)
    last_modified = _get_last_modified(entry.path)
    
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
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    entry = manager.get_by_id(image_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="image not found")
    return _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
        if_none_match, if_modified_since, is_random=False,
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
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    if color:
        entry = manager.pick_by_color(color, category or None)
    else:
        entry = manager.pick(category or None, seed or None)
    if entry is None:
        raise HTTPException(status_code=404, detail="category not found")
    # Random images should not be cached long-term
    is_random = not seed
    return _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
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
    if_none_match: str | None = Header(default=None),
    if_modified_since: str | None = Header(default=None),
) -> Response:
    entry = manager.pick_by_color(hex_color)
    if entry is None:
        raise HTTPException(status_code=404, detail="no image matching that color")
    return _serve_entry(
        entry, width, height, ext, grayscale, blur, text, fit, format,
        tint, brightness, contrast, saturation, sepia,
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
        },
    )


# ── API metadata ──────────────────────────────────────────────────
@app.get("/api/images")
async def api_images() -> JSONResponse:
    return JSONResponse({
        "categories": manager.list_categories(),
        "total": manager.total,
    })


@app.get("/api/info/id/{image_id:int}")
async def image_info_by_id(image_id: int) -> JSONResponse:
    entry = manager.get_by_id(image_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="image not found")

    from PIL import Image

    with Image.open(entry.path) as img:
        width, height = img.size
        fmt = img.format.lower() if img.format else "unknown"

    size = entry.path.stat().st_size

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

    with Image.open(entry.path) as img:
        width, height = img.size
        fmt = img.format.lower() if img.format else "unknown"

    size = entry.path.stat().st_size

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
    if not settings.upload_enabled:
        raise HTTPException(status_code=403, detail="uploads are disabled")

    if not file.filename:
        raise HTTPException(status_code=400, detail="no file provided")

    target_dir = settings.images_dir
    if category:
        target_dir = target_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)

    dest = target_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)

    # Trigger rescan
    manager.rescan()

    return JSONResponse({
        "success": True,
        "filename": file.filename,
        "category": category or "__root",
        "path": str(dest),
    })


# ── Admin & Metrics ─────────────────────────────────────────────────
def verify_admin_password(password: str = Header(alias="X-Admin-Password")) -> bool:
    """Verify admin password from header."""
    if not settings.admin_password:
        raise HTTPException(status_code=404, detail="not found")
    if password != settings.admin_password:
        raise HTTPException(status_code=403, detail="invalid password")
    return True


@app.get("/admin/stats")
async def admin_stats_page(
    request: Request,
    _: bool = Depends(verify_admin_password),
) -> Response:
    """Admin dashboard page."""
    if not metrics_tracker:
        raise HTTPException(status_code=404, detail="not found")
    
    stats = metrics_tracker.get_stats_summary()
    
    # Build stats cards
    cards_html = f"""
    <div class="stat-card">
        <div class="stat-value">{stats['total_requests']:,}</div>
        <div class="stat-label">Total Requests</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats['cache_hit_rate']}%</div>
        <div class="stat-label">Cache Hit Rate</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats['avg_response_time_ms']:.1f}ms</div>
        <div class="stat-label">Avg Response Time</div>
    </div>
    """
    
    # Popular sizes table
    sizes_rows = ""
    for item in stats['popular_sizes'][:10]:
        sizes_rows += f"<tr><td>{item['width']}x{item['height']}</td><td>{item['count']:,}</td></tr>"
    
    # Popular categories table
    categories_rows = ""
    for item in stats['popular_categories'][:10]:
        categories_rows += f"<tr><td>{item['category']}</td><td>{item['count']:,}</td></tr>"
    
    # Popular formats table
    formats_rows = ""
    for item in stats['popular_formats'][:10]:
        formats_rows += f"<tr><td>{item['format'].upper()}</td><td>{item['count']:,}</td></tr>"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PlacePix Admin - Stats</title>
    <style>
        :root {{ --bg: #f8fafc; --card: #fff; --text: #1e293b; --muted: #64748b; --accent: #3b82f6; --border: #e2e8f0; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; padding: 2rem; }}
        h1 {{ margin-bottom: 2rem; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .stat-card {{ background: var(--card); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border); }}
        .stat-value {{ font-size: 2rem; font-weight: 700; color: var(--accent); }}
        .stat-label {{ color: var(--muted); margin-top: 0.5rem; }}
        .tables-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }}
        .table-card {{ background: var(--card); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border); }}
        .table-card h2 {{ font-size: 1.1rem; margin-bottom: 1rem; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ font-weight: 600; color: var(--muted); font-size: 0.875rem; }}
        tr:last-child td {{ border-bottom: none; }}
    </style>
</head>
<body>
    <h1>📊 PlacePix Admin Dashboard</h1>
    <div class="stats-grid">{cards_html}</div>
    <div class="tables-grid">
        <div class="table-card">
            <h2>Popular Sizes</h2>
            <table>
                <thead><tr><th>Size</th><th>Requests</th></tr></thead>
                <tbody>{sizes_rows}</tbody>
            </table>
        </div>
        <div class="table-card">
            <h2>Popular Categories</h2>
            <table>
                <thead><tr><th>Category</th><th>Requests</th></tr></thead>
                <tbody>{categories_rows}</tbody>
            </table>
        </div>
        <div class="table-card">
            <h2>Popular Formats</h2>
            <table>
                <thead><tr><th>Format</th><th>Requests</th></tr></thead>
                <tbody>{formats_rows}</tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
    
    return Response(content=html, media_type="text/html")


@app.get("/api/admin/stats")
async def api_admin_stats(
    _: bool = Depends(verify_admin_password),
) -> JSONResponse:
    """Get stats as JSON."""
    if not metrics_tracker:
        raise HTTPException(status_code=404, detail="not found")
    
    return JSONResponse(metrics_tracker.get_stats_summary())


@app.get("/api/admin/popular-sizes")
async def api_admin_popular_sizes(
    limit: int = 10,
    _: bool = Depends(verify_admin_password),
) -> JSONResponse:
    """Get popular sizes."""
    if not metrics_tracker:
        raise HTTPException(status_code=404, detail="not found")
    
    return JSONResponse(metrics_tracker.get_popular_sizes(limit))


@app.get("/api/admin/popular-categories")
async def api_admin_popular_categories(
    limit: int = 10,
    _: bool = Depends(verify_admin_password),
) -> JSONResponse:
    """Get popular categories."""
    if not metrics_tracker:
        raise HTTPException(status_code=404, detail="not found")
    
    return JSONResponse(metrics_tracker.get_popular_categories(limit))


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
