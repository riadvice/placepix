"""Tests for seed module."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from PIL import Image

from src.seed import SEED_CATEGORIES, _add_sample_text, _random_gradient, seed_images


def test_seed_categories_constant():
    """Test SEED_CATEGORIES constant is defined correctly."""
    assert len(SEED_CATEGORIES) == 5
    assert SEED_CATEGORIES[0] == ("nature", "Nature", "Beautiful nature and landscapes")
    assert SEED_CATEGORIES[1] == ("animals", "Animals", "Cute and wild animals")


def test_random_gradient():
    """Test random gradient generation."""
    img = _random_gradient(800, 600)
    assert img.size == (800, 600)
    assert img.mode == "RGB"


def test_random_gradient_different_sizes():
    """Test gradient with various sizes."""
    sizes = [(100, 100), (500, 300), (1920, 1080)]
    for width, height in sizes:
        img = _random_gradient(width, height)
        assert img.size == (width, height)


def test_add_sample_text():
    """Test adding text to image."""
    img = Image.new("RGB", (800, 600), color=(100, 100, 100))
    result = _add_sample_text(img, "Test Text")
    assert result.size == (800, 600)
    assert result.mode == "RGB"


def test_add_sample_text_various_sizes():
    """Test text on different image sizes."""
    sizes = [(200, 200), (1000, 500), (1920, 1080)]
    for width, height in sizes:
        img = Image.new("RGB", (width, height))
        result = _add_sample_text(img, "Sample")
        assert result.size == (width, height)


def test_add_sample_text_long_text():
    """Test adding long text."""
    img = Image.new("RGB", (800, 600))
    result = _add_sample_text(img, "This is a very long text message")
    assert result.size == (800, 600)


def test_seed_images_empty_directory():
    """Test seeding images in empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = Path(tmpdir)
        seed_images(images_dir, count_per_category=2)

        # Check categories were created
        for slug, name, desc in SEED_CATEGORIES:
            cat_dir = images_dir / slug
            assert cat_dir.exists()
            assert cat_dir.is_dir()

            # Check category.json
            meta_file = cat_dir / "category.json"
            assert meta_file.exists()
            meta = json.loads(meta_file.read_text())
            assert meta["name"] == name
            assert meta["description"] == desc

            # Check sample images
            images = list(cat_dir.glob("sample_*.jpg"))
            assert len(images) == 2

            # Verify images are valid
            for img_path in images:
                with Image.open(img_path) as img:
                    assert img.format == "JPEG"
                    assert img.size[0] in [800, 1200, 1600]
                    assert img.size[1] in [600, 800, 1200]


def test_seed_images_non_empty_directory():
    """Test that seeding skips non-empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = Path(tmpdir)

        # Create a file to make directory non-empty
        (images_dir / "existing.txt").write_text("test")

        # Should not seed
        seed_images(images_dir)

        # Should only have the existing file
        files = list(images_dir.rglob("*"))
        assert len([f for f in files if f.is_file()]) == 1


def test_seed_images_custom_count():
    """Test seeding with custom count per category."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = Path(tmpdir)
        seed_images(images_dir, count_per_category=3)

        # Check each category has 3 images
        for slug, _, _ in SEED_CATEGORIES:
            cat_dir = images_dir / slug
            images = list(cat_dir.glob("sample_*.jpg"))
            assert len(images) == 3


def test_seed_images_single_image():
    """Test seeding with single image per category."""
    with tempfile.TemporaryDirectory() as tmpdir:
        images_dir = Path(tmpdir)
        seed_images(images_dir, count_per_category=1)

        for slug, _, _ in SEED_CATEGORIES:
            cat_dir = images_dir / slug
            images = list(cat_dir.glob("sample_*.jpg"))
            assert len(images) == 1
            assert images[0].name == "sample_1.jpg"
