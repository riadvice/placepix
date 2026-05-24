from __future__ import annotations

import logging
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


SEED_CATEGORIES = [
    ("nature", "Nature", "Beautiful nature and landscapes"),
    ("animals", "Animals", "Cute and wild animals"),
    ("architecture", "Architecture", "Buildings and structures"),
    ("abstract", "Abstract", "Colorful abstract patterns"),
    ("food", "Food", "Delicious food photography"),
]


def _random_gradient(width: int, height: int) -> Image.Image:
    """Generate a random colored gradient image."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Two random colors
    c1 = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
    c2 = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))

    for y in range(height):
        ratio = y / height
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


def _add_sample_text(img: Image.Image, text: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    font_size = min(img.width, img.height) // 10
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (img.width - text_width) // 2
    y = (img.height - text_height) // 2

    # Shadow
    draw.text((x + 2, y + 2), text, fill=(0, 0, 0), font=font)
    # Text
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    return img


def seed_images(images_dir: Path, count_per_category: int = 5) -> None:
    """Generate sample images if the directory is empty."""
    images_dir.mkdir(parents=True, exist_ok=True)
    
    if any(images_dir.iterdir()):
        logger.info(f"Directory {images_dir} already has content, skipping seed")
        return  # already has content

    logger.info(f"Seeding sample images in {images_dir}")

    for slug, name, desc in SEED_CATEGORIES:
        cat_dir = images_dir / slug
        cat_dir.mkdir(parents=True, exist_ok=True)

        # Write category metadata
        import json
        meta = {"name": name, "description": desc}
        (cat_dir / "category.json").write_text(json.dumps(meta, indent=2))

        for i in range(count_per_category):
            w = random.choice([800, 1200, 1600])
            h = random.choice([600, 800, 1200])
            img = _random_gradient(w, h)
            img = _add_sample_text(img, f"{name} {i + 1}")
            img.save(cat_dir / f"sample_{i + 1}.jpg", quality=85)

    logger.info(f"Seeded {len(SEED_CATEGORIES) * count_per_category} sample images")
