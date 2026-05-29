"""Direct tests for ImageProcessor class methods."""

from __future__ import annotations

from pathlib import Path
import tempfile

from PIL import Image
import pytest

from src.image_processor import ImageProcessor


@pytest.fixture
def test_image():
    """Create a test image with gradient for better compression testing."""
    from PIL import ImageDraw

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (800, 600))
        draw = ImageDraw.Draw(img)
        # Create gradient for better compression testing
        for i in range(600):
            color = int(i / 600 * 255)
            draw.line([(0, i), (800, i)], fill=(color, 100, 255 - color))
        img.save(f.name)
        yield Path(f.name)
        Path(f.name).unlink()


def test_processor_initialization():
    """Test ImageProcessor initialization."""
    processor = ImageProcessor()
    assert processor.min_width == 8
    assert processor.max_width == 2000
    assert processor.min_height == 8
    assert processor.max_height == 2000


def test_processor_custom_limits():
    """Test ImageProcessor with custom limits."""
    processor = ImageProcessor(min_width=10, max_width=1000, min_height=10, max_height=1000)
    assert processor.min_width == 10
    assert processor.max_width == 1000


def test_clamp_size():
    """Test size clamping."""
    processor = ImageProcessor()

    # Within limits
    w, h = processor.clamp_size(500, 300)
    assert w == 500
    assert h == 300

    # Too large
    w, h = processor.clamp_size(5000, 5000)
    assert w == 2000
    assert h == 2000

    # Too small
    w, h = processor.clamp_size(1, 1)
    assert w == 8
    assert h == 8

    # Zero values
    w, h = processor.clamp_size(0, 0)
    assert w == 0
    assert h == 0


def test_normalize_format():
    """Test format normalization."""
    processor = ImageProcessor()

    assert processor._normalize_format("jpeg") == "jpeg"
    assert processor._normalize_format("jpg") == "jpeg"
    assert processor._normalize_format("png") == "png"
    assert processor._normalize_format("webp") == "webp"
    assert processor._normalize_format("avif") == "avif"
    assert processor._normalize_format("unknown") == "jpeg"


def test_process_basic(test_image):
    """Test basic image processing."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_process_grayscale(test_image):
    """Test grayscale conversion."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, grayscale=True)
    assert isinstance(result, bytes)


def test_process_sepia(test_image):
    """Test sepia effect."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, sepia=True)
    assert isinstance(result, bytes)


def test_process_tint(test_image):
    """Test tint effect."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, tint="ff0000")
    assert isinstance(result, bytes)


def test_process_blur(test_image):
    """Test blur effect."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, blur=5)
    assert isinstance(result, bytes)


def test_process_brightness(test_image):
    """Test brightness adjustment."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, brightness=1.5)
    assert isinstance(result, bytes)


def test_process_contrast(test_image):
    """Test contrast adjustment."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, contrast=1.5)
    assert isinstance(result, bytes)


def test_process_saturation(test_image):
    """Test saturation adjustment."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, saturation=0.5)
    assert isinstance(result, bytes)


def test_process_all_fit_modes(test_image):
    """Test all fit modes."""
    processor = ImageProcessor()

    for fit_mode in ["crop", "scale", "contain", "cover", "smart"]:
        result = processor.process(test_image, width=400, height=300, fit=fit_mode)
        assert isinstance(result, bytes)


def test_process_text_overlay(test_image):
    """Test text overlay."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, text="Test Text")
    assert isinstance(result, bytes)


def test_process_border(test_image):
    """Test border application."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, border="10")
    assert isinstance(result, bytes)


def test_process_border_with_color(test_image):
    """Test border with color."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, border="10,ff0000")
    assert isinstance(result, bytes)


def test_process_padding(test_image):
    """Test padding."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, padding=20)
    assert isinstance(result, bytes)


def test_process_noise(test_image):
    """Test noise effect."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, noise=30)
    assert isinstance(result, bytes)


def test_process_pixelate(test_image):
    """Test pixelate effect."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, pixelate=10)
    assert isinstance(result, bytes)


def test_process_lqip(test_image):
    """Test LQIP generation."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, lqip=True)
    assert isinstance(result, bytes)


def test_process_quality(test_image):
    """Test quality parameter."""
    processor = ImageProcessor()

    # High quality
    high = processor.process(test_image, width=400, height=300, quality=95)
    assert isinstance(high, bytes)

    # Low quality
    low = processor.process(test_image, width=400, height=300, quality=10)
    assert isinstance(low, bytes)

    # Low quality should be smaller
    assert len(low) < len(high)


def test_process_watermark_without_config(test_image):
    """Test watermark without config (should be ignored)."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, watermark="true")
    assert isinstance(result, bytes)


def test_process_watermark_with_config(test_image):
    """Test watermark with config."""
    processor = ImageProcessor()
    config = {
        "watermark_text": "Test Watermark",
        "watermark_position": "bottom-right",
        "watermark_opacity": 0.5,
    }
    result = processor.process(
        test_image, width=400, height=300, watermark="bottom-right", watermark_config=config
    )
    assert isinstance(result, bytes)


def test_process_png_format(test_image):
    """Test PNG output format."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, output_format="png")
    assert isinstance(result, bytes)
    # PNG signature
    assert result[:8] == b"\x89PNG\r\n\x1a\n"


def test_process_webp_format(test_image):
    """Test WebP output format."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=300, output_format="webp")
    assert isinstance(result, bytes)


def test_process_width_only(test_image):
    """Test processing with width only."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=400, height=0)
    assert isinstance(result, bytes)


def test_process_height_only(test_image):
    """Test processing with height only."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=0, height=300)
    assert isinstance(result, bytes)


def test_process_no_resize(test_image):
    """Test processing without resize."""
    processor = ImageProcessor()
    result = processor.process(test_image, width=0, height=0)
    assert isinstance(result, bytes)


def test_resize_crop_center(test_image):
    """Test crop center resize mode."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        result = processor._crop_center(img, 400, 300)
        assert result.size == (400, 300)


def test_resize_scale(test_image):
    """Test scale resize mode."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        result = processor._resize(img, 400, 300, "scale")
        assert result.size == (400, 300)


def test_resize_contain(test_image):
    """Test contain resize mode."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        result = processor._resize(img, 400, 300, "contain")
        # Should fit within bounds
        assert result.width <= 400
        assert result.height <= 300


def test_resize_cover(test_image):
    """Test cover resize mode."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        result = processor._resize(img, 400, 300, "cover")
        # Should cover the area
        assert result.width >= 400 or result.height >= 300


def test_apply_sepia(test_image):
    """Test sepia filter application."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._apply_sepia(img)
        assert result.mode == "RGB"
        assert result.size == img.size


def test_apply_tint(test_image):
    """Test tint application."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._apply_tint(img, "ff0000")
        assert result.mode == "RGB"
        assert result.size == img.size


def test_apply_tint_short_hex(test_image):
    """Test tint with 3-digit hex."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._apply_tint(img, "f00")
        assert result.mode == "RGB"


def test_apply_border(test_image):
    """Test border application."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._apply_border(img, "10")
        # Border adds to size
        assert result.width > img.width
        assert result.height > img.height


def test_apply_border_with_color(test_image):
    """Test border with custom color."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._apply_border(img, "10,00ff00")
        assert result.width > img.width


def test_apply_noise(test_image):
    """Test noise application."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._apply_noise(img, 50)
        assert result.size == img.size


def test_apply_pixelate(test_image):
    """Test pixelate effect."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._apply_pixelate(img, 10)
        assert result.size == img.size


def test_generate_lqip(test_image):
    """Test LQIP generation."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._generate_lqip(img)
        # LQIP should be much smaller
        assert result.width < img.width
        assert result.height < img.height


def test_smart_crop_fallback(test_image):
    """Test smart crop falls back to center crop."""
    processor = ImageProcessor()
    with Image.open(test_image) as img:
        img = img.convert("RGB")
        result = processor._smart_crop(img, 400, 300)
        assert result.size == (400, 300)


def test_combined_effects(test_image):
    """Test combining multiple effects."""
    processor = ImageProcessor()
    result = processor.process(
        test_image,
        width=400,
        height=300,
        grayscale=True,
        blur=3,
        sepia=True,
        border="5",
        padding=10,
        noise=20,
        pixelate=5,
        quality=90,
        text="Test",
    )
    assert isinstance(result, bytes)
