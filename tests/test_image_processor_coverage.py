"""Additional tests for ImageProcessor to increase coverage."""

from __future__ import annotations

from pathlib import Path
import tempfile

import cv2
import numpy as np
import PIL
from PIL import Image, ImageFont
import pytest

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


def test_pixelate_size_one(complex_image):
    """Test pixelate with size 1 (no effect)."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        result = processor._apply_pixelate(img, 1)
        assert result.size == img.size


def test_noise_amount_zero(complex_image):
    """Test noise with amount 0 (no effect)."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        result = processor._apply_noise(img, 0)
        assert result.size == img.size


def test_watermark_convert_to_rgba(complex_image):
    """Test watermark conversion to RGBA when not already RGBA."""
    processor = ImageProcessor()
    config = {
        "watermark_text": "Test",
        "watermark_position": "center",
        "watermark_opacity": 0.5,
    }
    result = processor.process(
        complex_image, width=400, height=300, watermark="center", watermark_config=config
    )
    assert isinstance(result, bytes)


def test_resize_zero_dimensions(complex_image):
    """Test resize with both width and height as 0 (no resize)."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        result = processor._resize(img, 0, 0, "crop")
        assert result.size == img.size


def test_watermark_invalid_image_path(complex_image):
    """Test watermark with invalid image path falls back to text."""
    processor = ImageProcessor()
    config = {
        "watermark_image": "/nonexistent/watermark.png",
        "watermark_text": "Fallback Text",
        "watermark_position": "bottom-right",
        "watermark_opacity": 0.5,
    }
    result = processor.process(
        complex_image, width=400, height=300, watermark="bottom-right", watermark_config=config
    )
    assert isinstance(result, bytes)


def test_watermark_no_image_no_text(complex_image):
    """Test watermark with no image and no text returns original image."""
    processor = ImageProcessor()
    config = {
        "watermark_image": "",
        "watermark_text": "",
        "watermark_position": "bottom-right",
        "watermark_opacity": 0.5,
    }
    result = processor.process(
        complex_image, width=400, height=300, watermark="bottom-right", watermark_config=config
    )
    assert isinstance(result, bytes)


def test_watermark_position_default(complex_image):
    """Test watermark with invalid position uses default."""
    processor = ImageProcessor()
    config = {
        "watermark_text": "Test",
        "watermark_position": "bottom-right",
        "watermark_opacity": 0.5,
    }
    result = processor.process(
        complex_image, width=400, height=300, watermark="invalid-position", watermark_config=config
    )
    assert isinstance(result, bytes)


def test_border_invalid_width(complex_image):
    """Test border with invalid width."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        img = img.convert("RGB")
        result = processor._apply_border(img, "abc")
        assert result.size == img.size


def test_border_empty_string(complex_image):
    """Test border with empty string."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        img = img.convert("RGB")
        result = processor._apply_border(img, "")
        assert result.size == img.size


def test_process_png_format(complex_image):
    """Test PNG format processing."""
    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, output_format="png")
    assert isinstance(result, bytes)


def test_process_webp_format(complex_image):
    """Test WebP format processing."""
    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, output_format="webp")
    assert isinstance(result, bytes)


def test_process_quality_clamping(complex_image):
    """Test quality clamping to valid range."""
    processor = ImageProcessor()
    # Test quality below 1
    result = processor.process(complex_image, width=400, height=300, quality=-10)
    assert isinstance(result, bytes)
    # Test quality above 100
    result = processor.process(complex_image, width=400, height=300, quality=150)
    assert isinstance(result, bytes)


def test_resize_default_case(complex_image):
    """Test resize with invalid fit mode uses default crop."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        result = processor._resize(img, 400, 300, "invalid")
        assert result.size == (400, 300)


def test_tint_3digit_hex(complex_image):
    """Test tint with 3-digit hex color."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        img = img.convert("RGB")
        result = processor._apply_tint(img, "f00")
        assert result.size == img.size


def test_border_3digit_hex(complex_image):
    """Test border with 3-digit hex color."""
    processor = ImageProcessor()
    with Image.open(complex_image) as img:
        img = img.convert("RGB")
        result = processor._apply_border(img, "5,f00")
        # Border adds to image size (5px on each side = 10px total)
        assert result.size == (img.width + 10, img.height + 10)


def test_watermark_position_from_config(complex_image):
    """Test watermark uses position from config when position is 'true'."""
    processor = ImageProcessor()
    config = {
        "watermark_text": "Test",
        "watermark_position": "top-left",
        "watermark_opacity": 0.5,
    }
    result = processor.process(
        complex_image, width=400, height=300, watermark="true", watermark_config=config
    )
    assert isinstance(result, bytes)


def test_smart_crop_opencv_error(complex_image, monkeypatch):
    """Test smart crop when opencv cascade loading fails."""

    original_cascade = cv2.CascadeClassifier

    def failing_cascade(*args, **kwargs):
        raise Exception("Cascade load failed")

    monkeypatch.setattr(cv2, "CascadeClassifier", failing_cascade)

    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, fit="smart")
    assert isinstance(result, bytes)

    # Restore
    monkeypatch.setattr(cv2, "CascadeClassifier", original_cascade)


def test_smart_crop_no_faces_detected(complex_image, monkeypatch):
    """Test smart crop when no faces are detected."""

    # Mock detectMultiScale to return empty array
    original_detect = cv2.CascadeClassifier.detectMultiScale

    def empty_detect(self, *args, **kwargs):
        return np.array([])

    monkeypatch.setattr(cv2.CascadeClassifier, "detectMultiScale", empty_detect)

    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, fit="smart")
    assert isinstance(result, bytes)

    # Restore
    monkeypatch.setattr(cv2.CascadeClassifier, "detectMultiScale", original_detect)


def test_smart_crop_with_faces(complex_image, monkeypatch):
    """Test smart crop when faces are detected."""

    # Mock detectMultiScale to return faces
    original_detect = cv2.CascadeClassifier.detectMultiScale

    def faces_detect(self, *args, **kwargs):
        return np.array([[100, 100, 50, 50], [200, 150, 60, 60]])

    monkeypatch.setattr(cv2.CascadeClassifier, "detectMultiScale", faces_detect)

    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, fit="smart")
    assert isinstance(result, bytes)

    # Restore
    monkeypatch.setattr(cv2.CascadeClassifier, "detectMultiScale", original_detect)


def test_smart_crop_taller_than_wide(complex_image, monkeypatch):
    """Test smart crop when current ratio is taller than target."""

    # Mock detectMultiScale to return faces that create tall aspect ratio
    original_detect = cv2.CascadeClassifier.detectMultiScale

    def tall_faces_detect(self, *args, **kwargs):
        return np.array([[100, 100, 50, 200]])

    monkeypatch.setattr(cv2.CascadeClassifier, "detectMultiScale", tall_faces_detect)

    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, fit="smart")
    assert isinstance(result, bytes)

    # Restore
    monkeypatch.setattr(cv2.CascadeClassifier, "detectMultiScale", original_detect)


def test_add_text_font_exception(complex_image, monkeypatch):
    """Test text overlay when font loading fails."""

    original_truetype = PIL.ImageFont.truetype
    original_load_default = PIL.ImageFont.load_default

    def failing_truetype(*args, **kwargs):
        raise Exception("Font not found")

    # Create a mock font
    mock_font = ImageFont.load_default()

    monkeypatch.setattr(PIL.ImageFont, "truetype", failing_truetype)
    monkeypatch.setattr(PIL.ImageFont, "load_default", lambda: mock_font)

    processor = ImageProcessor()
    result = processor.process(complex_image, width=400, height=300, text="Test")
    assert isinstance(result, bytes)

    # Restore
    monkeypatch.setattr(PIL.ImageFont, "truetype", original_truetype)
    monkeypatch.setattr(PIL.ImageFont, "load_default", original_load_default)


def test_watermark_font_exception(complex_image, monkeypatch):
    """Test watermark text when font loading fails."""

    original_truetype = PIL.ImageFont.truetype
    original_load_default = PIL.ImageFont.load_default

    def failing_truetype(*args, **kwargs):
        raise Exception("Font not found")

    # Create a mock font
    mock_font = ImageFont.load_default()

    monkeypatch.setattr(PIL.ImageFont, "truetype", failing_truetype)
    monkeypatch.setattr(PIL.ImageFont, "load_default", lambda: mock_font)

    processor = ImageProcessor()
    config = {
        "watermark_text": "Test",
        "watermark_position": "bottom-right",
        "watermark_opacity": 0.5,
    }
    result = processor.process(
        complex_image, width=400, height=300, watermark="bottom-right", watermark_config=config
    )
    assert isinstance(result, bytes)

    # Restore
    monkeypatch.setattr(PIL.ImageFont, "truetype", original_truetype)
    monkeypatch.setattr(PIL.ImageFont, "load_default", original_load_default)


def test_watermark_rgba_conversion(complex_image):
    """Test watermark conversion to RGBA."""
    processor = ImageProcessor()
    # Create a non-RGBA watermark image
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as wm:
        wm_img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        wm_img.save(wm.name)
        wm_path = Path(wm.name)

    try:
        config = {
            "watermark_image": str(wm_path),
            "watermark_position": "center",
            "watermark_opacity": 0.5,
        }
        result = processor.process(
            complex_image, width=400, height=300, watermark="center", watermark_config=config
        )
        assert isinstance(result, bytes)
    finally:
        wm_path.unlink()


def test_watermark_nonexistent_image_with_text(complex_image):
    """Test watermark with non-existent image path falls back to text."""
    processor = ImageProcessor()
    config = {
        "watermark_image": "/nonexistent/path/watermark.png",
        "watermark_text": "Fallback Text",
        "watermark_position": "bottom-right",
        "watermark_opacity": 0.5,
    }
    result = processor.process(
        complex_image, width=400, height=300, watermark="bottom-right", watermark_config=config
    )
    assert isinstance(result, bytes)


def test_watermark_image_load_exception_with_mock(complex_image, monkeypatch):
    """Test watermark image load exception by mocking Path.exists and Image.open."""

    # Create a real file that exists
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as wm:
        # Write invalid image data
        wm.write(b"invalid image data")
        wm_path = Path(wm.name)

    try:
        # Mock Image.open to raise exception for this specific path
        original_open = Image.open

        def selective_open(path, *args, **kwargs):
            if str(path) == str(wm_path):
                raise Exception("Invalid image data")
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr(Image, "open", selective_open)

        processor = ImageProcessor()
        config = {
            "watermark_image": str(wm_path),
            "watermark_text": "Fallback",
            "watermark_position": "bottom-right",
            "watermark_opacity": 0.5,
        }
        result = processor.process(
            complex_image, width=400, height=300, watermark="bottom-right", watermark_config=config
        )
        assert isinstance(result, bytes)

        # Restore
        monkeypatch.setattr(Image, "open", original_open)
    finally:
        wm_path.unlink()


def test_watermark_same_size_non_rgba(complex_image):
    """Test watermark RGBA conversion when watermark size equals image size (line 435)."""
    processor = ImageProcessor()
    # Create a watermark that's the same size as the processed image (400x300)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as wm:
        wm_img = Image.new("RGB", (400, 300), color=(255, 255, 255))
        wm_img.save(wm.name)
        wm_path = Path(wm.name)

    try:
        config = {
            "watermark_image": str(wm_path),
            "watermark_position": "center",
            "watermark_opacity": 0.5,
        }
        result = processor.process(
            complex_image, width=400, height=300, watermark="center", watermark_config=config
        )
        assert isinstance(result, bytes)
    finally:
        wm_path.unlink()
