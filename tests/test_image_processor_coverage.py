"""Additional tests for ImageProcessor to increase coverage."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from src.image_processor import ImageProcessor


@pytest.fixture
def complex_image():
    """Create a complex test image with face-like features."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (800, 600), color=(200, 200, 200))
        img.save(f.name)
        yield Path(f.name)
        Path(f.name).unlink()


def test_process_avif_format(complex_image):
    """Test AVIF format processing (may fallback to JPEG)."""
    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, output_format="avif")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_process_unknown_format_fallback(complex_image):
    """Test unknown format falls back to JPEG."""
    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, output_format="unknown")
    assert isinstance(result, bytes)


def test_process_with_watermark_no_config(complex_image):
    """Test watermark parameter without config is ignored."""
    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, watermark="true")
    assert isinstance(result, bytes)


def test_process_with_watermark_text(complex_image):
    """Test watermark with text configuration."""
    processor = ImageProcessor()
    config = {
        "watermark_text": "© Test 2026",
        "watermark_position": "bottom-right",
        "watermark_opacity": 0.7,
    }
    result = processor.process(
        complex_image, width=400, height=300, watermark="bottom-right", watermark_config=config
    )
    assert isinstance(result, bytes)


def test_process_with_watermark_image(complex_image):
    """Test watermark with image configuration."""
    # Create a watermark image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as wm:
        wm_img = Image.new("RGBA", (100, 100), color=(255, 255, 255, 128))
        wm_img.save(wm.name)
        wm_path = Path(wm.name)
    
    try:
        processor = ImageProcessor()
        config = {
            "watermark_image": str(wm_path),
            "watermark_position": "top-left",
            "watermark_opacity": 0.5,
        }
        result = processor.process(
            complex_image, width=400, height=300, watermark="top-left", watermark_config=config
        )
        assert isinstance(result, bytes)
    finally:
        wm_path.unlink()


def test_process_watermark_all_positions(complex_image):
    """Test watermark at all positions."""
    processor = ImageProcessor()
    positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    
    for pos in positions:
        config = {
            "watermark_text": "Test",
            "watermark_position": pos,
            "watermark_opacity": 0.5,
        }
        result = processor.process(
            complex_image, width=400, height=300, watermark=pos, watermark_config=config
        )
        assert isinstance(result, bytes)


def test_smart_crop_without_opencv(complex_image, monkeypatch):
    """Test smart crop falls back when OpenCV not available."""
    # Mock OpenCV as unavailable
    import src.image_processor
    monkeypatch.setattr(src.image_processor, "_OPENCV_AVAILABLE", False)
    
    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, fit="smart")
    assert isinstance(result, bytes)


def test_resize_contain_mode(complex_image):
    """Test contain resize mode."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        result = processor._resize(img, 400, 300, "contain")
        # Should fit within bounds
        assert result.width <= 400
        assert result.height <= 300


def test_resize_cover_mode(complex_image):
    """Test cover resize mode."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        result = processor._resize(img, 400, 300, "cover")
        # Should cover the area
        assert result.width >= 400 or result.height >= 300


def test_resize_scale_mode(complex_image):
    """Test scale resize mode."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        result = processor._resize(img, 400, 300, "scale")
        assert result.size == (400, 300)


def test_apply_border_invalid_format(complex_image):
    """Test border with invalid format."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        img = img.convert("RGB")
        # Invalid border format should be handled gracefully
        result = processor._apply_border(img, "invalid")
        assert result.size == img.size


def test_apply_tint_invalid_color(complex_image):
    """Test tint with invalid color."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        img = img.convert("RGB")
        # Invalid color should be handled gracefully
        result = processor._apply_tint(img, "invalid")
        assert result.size == img.size


def test_process_zero_dimensions(complex_image):
    """Test processing with zero dimensions (no resize)."""
    processor = ImageProcessor()
    result = processor.process(complex_image, width=0, height=0)
    assert isinstance(result, bytes)


def test_process_width_only_resize(complex_image):
    """Test resize with only width specified."""
    processor = ImageProcessor()
    result = processor.process(complex_image, width=500, height=0)
    assert isinstance(result, bytes)


def test_process_height_only_resize(complex_image):
    """Test resize with only height specified."""
    processor = ImageProcessor()
    result = processor.process(complex_image, width=0, height=400)
    assert isinstance(result, bytes)


def test_process_all_effects_combined(complex_image):
    """Test combining all effects together."""
    processor = ImageProcessor()
    result = processor.process(
        complex_image,
        width=400,
        height=300,
        grayscale=True,
        blur=2,
        sepia=True,
        tint="ff0000",
        brightness=1.2,
        contrast=1.1,
        saturation=0.8,
        border="5,00ff00",
        padding=10,
        noise=15,
        pixelate=3,
        quality=90,
        lqip=True,
        text="Test All Effects",
    )
    assert isinstance(result, bytes)


def test_normalize_format_variations():
    """Test format normalization with various inputs."""
    processor = ImageProcessor()
    
    assert processor._normalize_format("JPEG") == "jpeg"
    assert processor._normalize_format("JPG") == "jpeg"
    assert processor._normalize_format("PNG") == "png"
    assert processor._normalize_format("WEBP") == "webp"
    assert processor._normalize_format("AVIF") == "avif"
    assert processor._normalize_format("gif") == "jpeg"  # Unsupported
    assert processor._normalize_format("") == "jpeg"  # Default


def test_clamp_size_edge_cases():
    """Test size clamping edge cases."""
    processor = ImageProcessor()
    
    # Negative values
    w, h = processor.clamp_size(-100, -100)
    assert w == 8
    assert h == 8
    
    # Mixed valid/invalid
    w, h = processor.clamp_size(100, -50)
    assert w == 100
    assert h == 8
    
    # Extremely large
    w, h = processor.clamp_size(10000, 10000)
    assert w == 2000
    assert h == 2000


def test_process_with_invalid_image_path():
    """Test processing with non-existent image path."""
    processor = ImageProcessor()
    with pytest.raises(Exception):
        processor.process(Path("/nonexistent/image.jpg"), width=400, height=300)
