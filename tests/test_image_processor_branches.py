"""Unit tests for the remaining ImageProcessor branches."""

from __future__ import annotations

import io
from pathlib import Path
import shutil
from unittest.mock import MagicMock, patch

from PIL import Image, ImageFont
import pytest

import src.image_processor as ip
from src.image_processor import ImageProcessor


@pytest.fixture
def proc() -> ImageProcessor:
    return ImageProcessor()


@pytest.fixture
def img() -> Image.Image:
    return Image.new("RGB", (120, 90), (90, 120, 150))


def _a_system_ttf() -> Path | None:
    for root in ("/usr/share/fonts", "/System/Library/Fonts", "/Windows/Fonts"):
        base = Path(root)
        if base.exists():
            for f in base.rglob("*.ttf"):
                return f
    return None


# ── _load_font ──────────────────────────────────────────────────────


def test_load_font_uses_custom_dir(tmp_path: Path, monkeypatch):
    src_font = _a_system_ttf()
    if src_font is None:
        pytest.skip("no system .ttf available to copy")

    fonts = tmp_path / "fonts"
    fonts.mkdir()
    shutil.copy(src_font, fonts / "brand.ttf")
    monkeypatch.setattr(ip.settings, "font_dir", str(fonts), raising=False)

    font = ip._load_font(22)
    assert isinstance(font, ImageFont.FreeTypeFont)
    assert font.size == 22


def test_load_font_skips_broken_custom_fonts(tmp_path: Path, monkeypatch):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "broken.ttf").write_bytes(b"nope")
    (fonts / "broken.ttc").write_bytes(b"nope")
    monkeypatch.setattr(ip.settings, "font_dir", str(fonts), raising=False)

    assert ip._load_font(14) is not None


# ── rounded corners ─────────────────────────────────────────────────


def test_apply_radius_rounds_corners(proc: ImageProcessor, img: Image.Image):
    out = proc._apply_radius(img, 20)
    assert out.size == img.size
    assert out.mode == "RGB"
    # Corner is composited onto white
    assert out.getpixel((0, 0)) == (255, 255, 255)


def test_apply_radius_zero_is_noop(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_radius(img, 0) is img


def test_apply_radius_clamps_to_half_the_shortest_side(proc: ImageProcessor, img: Image.Image):
    out = proc._apply_radius(img, 10_000)
    assert out.size == img.size


# ── colour parsing ──────────────────────────────────────────────────


def test_add_text_accepts_shorthand_and_invalid_colors(proc: ImageProcessor, img: Image.Image):
    """_parse_color expands #abc and falls back to the default on garbage."""
    shorthand = proc._add_text(img.copy(), "hi", text_color="f00", text_bg="0f0")
    invalid = proc._add_text(img.copy(), "hi", text_color="zzz-not-a-color")
    assert shorthand.size == img.size
    assert invalid.size == img.size


@pytest.mark.parametrize(
    "position", ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
)
def test_add_text_positions(proc: ImageProcessor, img: Image.Image, position: str):
    assert proc._add_text(img.copy(), "hi", position=position).size == img.size


@pytest.mark.parametrize(
    "position", ["top-left", "top-right", "bottom-left", "bottom-right", "center", "unknown"]
)
def test_get_watermark_position_variants(proc: ImageProcessor, position: str):
    x, y = proc._get_watermark_position(position, 200, 100, 40, 20)
    assert isinstance(x, int) and isinstance(y, int)


def test_duotone_parses_shorthand_and_invalid_hex(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_duotone(img, "f00", "00f").size == img.size
    assert proc._apply_duotone(img, "nope", "alsonope").size == img.size


# ── gradients ───────────────────────────────────────────────────────


def test_generate_gradient_rejects_invalid_hex(proc: ImageProcessor):
    with pytest.raises(ValueError, match="invalid hex color"):
        proc.generate_gradient(100, 100, "12345", "ffffff")


def test_generate_gradient_expands_shorthand_hex(proc: ImageProcessor):
    data = proc.generate_gradient(60, 40, "f00", "00f")
    assert Image.open(io.BytesIO(data)).size == (60, 40)


def test_generate_gradient_defaults_size_when_zero(proc: ImageProcessor):
    data = proc.generate_gradient(0, 0, "ffffff", "000000")
    assert Image.open(io.BytesIO(data)).size == (500, 300)


def test_generate_gradient_radial(proc: ImageProcessor):
    data = proc.generate_gradient(50, 50, "ffffff", "000000", gradient_type="radial")
    assert Image.open(io.BytesIO(data)).size == (50, 50)


@pytest.mark.parametrize("angle", [0, 45, 90, 180, 270])
def test_generate_gradient_angles(proc: ImageProcessor, angle: int):
    data = proc.generate_gradient(40, 40, "ff0000", "0000ff", angle=angle)
    assert Image.open(io.BytesIO(data)).size == (40, 40)


# ── filters with defaulted arguments ────────────────────────────────


def test_posterize_defaults_invalid_levels(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_posterize(img, 0).size == img.size


def test_sharpen_zero_is_noop(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_sharpen(img, 0) is img


def test_sharpen_clamps_large_amounts(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_sharpen(img, 99.0).size == img.size


def test_halftone_defaults_small_dot_size(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_halftone(img, 1).size == img.size


def test_emboss(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_emboss(img).size == img.size


def test_invert(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_invert(img).size == img.size


def test_vignette_zero_intensity_is_noop(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_vignette(img, 0) is img


def test_vignette_applies(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_vignette(img, 0.8).size == img.size


def test_pencil_sketch(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_pencil_sketch(img).size == img.size


def test_cartoon(proc: ImageProcessor, img: Image.Image):
    assert proc._apply_cartoon(img).size == img.size


def test_oil_painting_falls_back_on_error(proc: ImageProcessor, img: Image.Image):
    """xphoto is an optional OpenCV module; failure must degrade, not crash."""
    with patch.object(ip.cv2, "cvtColor", side_effect=RuntimeError("no xphoto")):
        out = proc._apply_oil_painting(img)
    assert out.size == img.size


# ── smart crop face detection ───────────────────────────────────────


def test_smart_crop_uses_detected_face(proc: ImageProcessor, tmp_path: Path, monkeypatch):
    """This OpenCV build ships no cascade XML, so the file is faked here."""
    source = Image.new("RGB", (200, 100), (10, 10, 10))

    cascade_dir = tmp_path / "cascades"
    cascade_dir.mkdir()
    (cascade_dir / "haarcascade_frontalface_default.xml").write_text("<opencv_storage/>")
    monkeypatch.setattr(ip.cv2.data, "haarcascades", str(cascade_dir) + "/", raising=False)

    cascade = MagicMock()
    cascade.detectMultiScale.return_value = [(80, 20, 40, 40)]

    with patch.object(ip.cv2, "CascadeClassifier", return_value=cascade):
        out = proc._smart_crop(source, 50, 50)

    assert out.size == (50, 50)
    assert cascade.detectMultiScale.call_count == 1


def test_smart_crop_survives_detection_errors(proc: ImageProcessor, img: Image.Image):
    with patch.object(ip.cv2, "cvtColor", side_effect=RuntimeError("bad array")):
        out = proc._smart_crop(img, 40, 40)
    assert out.size == (40, 40)


def test_smart_crop_skips_detection_with_explicit_focal_point(
    proc: ImageProcessor, img: Image.Image
):
    with patch.object(ip.cv2, "CascadeClassifier") as cascade:
        out = proc._smart_crop(img, 40, 40, focal_x=0.2, focal_y=0.8)
    assert out.size == (40, 40)
    assert cascade.call_count == 0


# ── progressive JPEG ────────────────────────────────────────────────


def test_process_writes_jpeg_with_rounded_corners(proc: ImageProcessor, tmp_path: Path):
    """radius runs the rounded-corner path inside process()."""
    source = tmp_path / "in.jpg"
    Image.new("RGB", (100, 80), (1, 2, 3)).save(source)

    data = proc.process(source, 60, 40, output_format="jpeg", quality=70, radius=12)

    out = Image.open(io.BytesIO(data))
    assert out.size == (60, 40)
    assert out.format == "JPEG"
