"""AI image generation via OVHcloud AI Endpoints with rate limiting."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import logging
from pathlib import Path
import re
import time
from typing import Any

import requests

from src.config import settings

logger = logging.getLogger(__name__)

# Rate limiting state
_rate_limit_lock = asyncio.Lock()
_rate_limit_last: dict[str, float] = {}


def _get_client_ip(request_headers: dict[str, str], client_host: str | None) -> str:
    """Extract real client IP, respecting X-Forwarded-For."""
    forwarded = request_headers.get("x-forwarded-for", "")
    if forwarded:
        # Take the first IP in the chain (closest to client)
        return forwarded.split(",")[0].strip()
    return client_host or "unknown"


async def check_rate_limit(client_ip: str) -> tuple[bool, float]:
    """Check if client IP is within rate limit (1 req/second).
    Returns (allowed, retry_after_seconds).
    """
    async with _rate_limit_lock:
        now = time.time()
        last = _rate_limit_last.get(client_ip, 0)
        if now - last < 1.0:
            retry_after = 1.0 - (now - last)
            return False, retry_after
        _rate_limit_last[client_ip] = now
        return True, 0.0


def _cleanup_rate_limit() -> None:
    """Purge stale IPs from rate limit dict (call periodically)."""
    now = time.time()
    stale = [ip for ip, t in _rate_limit_last.items() if now - t > 60]
    for ip in stale:
        del _rate_limit_last[ip]


def _slugify(text: str) -> str:
    """Convert prompt to filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-")


@dataclass
class GenerationResult:
    success: bool
    path: Path | None = None
    s3_key: str | None = None
    filename: str = ""
    category: str = ""
    id: int = 0
    prompt: str = ""
    error: str = ""


def generate_image(
    prompt: str,
    category: str,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 768,
    seed: int | None = None,
    steps: int | None = None,
    cfg_scale: float | None = None,
) -> GenerationResult:
    """Generate an image via OVHcloud AI Endpoints and save locally.

    This is a synchronous blocking function (runs in a thread).
    Call it via asyncio.to_thread() in async contexts.
    """
    if not settings.ai_generation_enabled:
        return GenerationResult(
            success=False,
            error="AI generation is experimental and currently disabled. Set AI_GENERATION_ENABLED=true to enable.",
        )

    if not settings.ovh_ai_endpoints_token:
        return GenerationResult(
            success=False,
            error="AI generation enabled but OVH_AI_ENDPOINTS_TOKEN is not configured.",
        )

    steps = steps or settings.ai_default_steps
    cfg_scale = cfg_scale or settings.ai_default_cfg_scale

    # Cap dimensions to reasonable limits for SDXL
    width = max(256, min(width, 2048))
    height = max(256, min(height, 2048))

    # Ensure AI directory exists
    ai_dir = settings.images_dir / "ai-generated" / category
    ai_dir.mkdir(parents=True, exist_ok=True)

    # Check cap
    existing = list(ai_dir.iterdir())
    if len(existing) >= settings.ai_max_images_per_category:
        return GenerationResult(
            success=False,
            error=f"Category '{category}' has reached the AI image cap ({settings.ai_max_images_per_category}). Delete some images to generate more.",
        )

    # Build filename from slugified prompt
    slug = _slugify(prompt)
    timestamp = int(time.time())
    filename = f"{slug}_{timestamp}.png"
    local_path = ai_dir / filename

    # Call OVHcloud AI Endpoints
    try:
        url = f"{settings.ovh_ai_endpoints_url}/image-generation"
        headers = {
            "Authorization": f"Bearer {settings.ovh_ai_endpoints_token}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": "stable-diffusion-xl",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_inference_steps": steps,
            "guidance_scale": cfg_scale,
            "num_images_per_prompt": 1,
        }
        if seed is not None:
            payload["seed"] = seed

        logger.info(f"Calling OVHcloud AI Endpoints: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        # OVHcloud SDXL returns base64-encoded image in images[0].b64_json
        images_data = data.get("images", [])
        if not images_data:
            return GenerationResult(success=False, error="No image returned from AI endpoint.")

        b64_image = images_data[0].get("b64_json", "")
        if not b64_image:
            return GenerationResult(success=False, error="Empty image data from AI endpoint.")

        image_bytes = base64.b64decode(b64_image)

        # Save locally
        with open(local_path, "wb") as f:
            f.write(image_bytes)

        logger.info(f"AI image saved: {local_path}")

        # Optional S3 upload
        s3_key = None
        if settings.ai_s3_upload_enabled and settings.s3_enabled:
            s3_key = _upload_to_s3(image_bytes, f"ai-generated/{category}/{filename}")

        return GenerationResult(
            success=True,
            path=local_path,
            s3_key=s3_key,
            filename=filename,
            category=category,
            prompt=prompt,
        )

    except requests.RequestException as e:
        logger.error(f"OVHcloud AI request failed: {e}")
        return GenerationResult(success=False, error=f"AI generation request failed: {e}")
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        return GenerationResult(success=False, error=f"AI generation failed: {e}")


def _upload_to_s3(image_bytes: bytes, s3_key: str) -> str | None:
    """Upload image bytes to S3. Returns the S3 key on success, None on failure."""
    try:
        import boto3
        from botocore.config import Config

        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region or "auto",
            config=Config(signature_version="s3v4"),
        )
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Body=image_bytes,
            ContentType="image/png",
        )
        logger.info(f"AI image uploaded to S3: {s3_key}")
        return s3_key
    except Exception as e:
        logger.warning(f"S3 upload failed for AI image: {e}")
        return None
