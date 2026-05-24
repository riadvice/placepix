from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import settings
from src.image_manager import ImageEntry, ImageManager
from src.image_processor import ImageProcessor
from src.observer import start_watching
from src.seed import seed_images

# ── Setup ───────────────────────────────────────────────────────────
app = FastAPI(title="PlacePix", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
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

# Templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Helpers ─────────────────────────────────────────────────────────
def _cache_path(entry: ImageEntry, width: int, height: int, fmt: str, grayscale: bool, blur: int, text: str, fit: str) -> Path:
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
    if blur:
        parts.append(f"blur{blur}")
    if text:
        parts.append(f"txt{hashlib.sha256(text.encode()).hexdigest()[:8]}")
    if fit != "crop":
        parts.append(fit)

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
) -> Response:
    """Process and serve a single image entry."""
    # Validate size
    width, height = processor.clamp_size(width, height)
    if width == 0 and height == 0:
        width, height = 500, 500

    # Determine output format
    output_format = output_format or ext.lstrip(".") or "jpeg"
    output_format = output_format.lower()
    if output_format not in ("jpeg", "jpg", "png", "webp"):
        output_format = "jpeg"
    if output_format == "jpg":
        output_format = "jpeg"

    # Build cache key
    cache_path = None
    if settings.cache:
        cache_path = _cache_path(entry, width, height, output_format, grayscale, blur, text, fit)
        cached = _read_cached(cache_path)
        if cached is not None:
            if settings.cdn:
                return RedirectResponse(url=f"{settings.cdn}/{cache_path.relative_to(settings.cache_dir)}")
            content_type = f"image/{output_format}"
            filename = f"placepix-{entry.category}-{width}x{height}.{output_format}"
            return Response(
                content=cached,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{filename}"',
                    "Cache-Control": "public, max-age=2592000, stale-while-revalidate=60, immutable",
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
    )

    # Cache if enabled
    if settings.cache and cache_path is not None:
        _write_cache(cache_path, processed)
        if settings.cdn:
            return RedirectResponse(url=f"{settings.cdn}/{cache_path.relative_to(settings.cache_dir)}")

    content_type = f"image/{output_format}"
    filename = f"placepix-{entry.category}-{width}x{height}.{output_format}"
    return Response(
        content=processed,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=2592000, stale-while-revalidate=60, immutable",
        },
    )


@app.get("/id/{image_id:int}/{width:int}/{height:int}")
@app.get("/id/{image_id:int}/{width:int}/{height:int}.{ext}")
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
) -> Response:
    entry = manager.get_by_id(image_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="image not found")
    return _serve_entry(entry, width, height, ext, grayscale, blur, text, fit, format)


@app.get("/{width:int}/{height:int}/{category}")
@app.get("/{width:int}/{height:int}/{category}.{ext}")
@app.get("/{width:int}/{height:int}/")
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
) -> Response:
    entry = manager.pick(category or None, seed or None)
    if entry is None:
        raise HTTPException(status_code=404, detail="category not found")
    return _serve_entry(entry, width, height, ext, grayscale, blur, text, fit, format)


# ── Random from all (no dimensions) ────────────────────────────────
@app.get("/random/{category:path}")
async def random_image(category: str = "") -> RedirectResponse:
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
        "serve_url": f"/id/{entry.id}/500/500",
    })


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
