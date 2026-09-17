"""Unit tests for src.avatar_generator: parsing, palettes and render options."""

from __future__ import annotations

import io
from pathlib import Path
import shutil

from PIL import Image, ImageFont
import pytest

import src.avatar_generator as av
from src.avatar_generator import AvatarGenerator


@pytest.fixture
def gen() -> AvatarGenerator:
    return AvatarGenerator()


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
    monkeypatch.setattr(av.settings, "font_dir", str(fonts), raising=False)

    font = av._load_font(28)
    assert isinstance(font, ImageFont.FreeTypeFont)
    assert font.size == 28


def test_load_font_skips_broken_custom_fonts(tmp_path: Path, monkeypatch):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "broken.ttf").write_bytes(b"nope")
    (fonts / "broken.ttc").write_bytes(b"nope")
    monkeypatch.setattr(av.settings, "font_dir", str(fonts), raising=False)

    assert av._load_font(16) is not None


def test_load_font_default_when_no_font_dirs(monkeypatch):
    monkeypatch.setattr(av.settings, "font_dir", "", raising=False)
    real_exists = Path.exists

    def fake_exists(self):
        if str(self) in {
            "/usr/share/fonts/truetype",
            "/usr/share/fonts",
            "/System/Library/Fonts",
            "/Windows/Fonts",
        }:
            return False
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    assert av._load_font(12) is not None


# ── palette resolution ──────────────────────────────────────────────


def test_resolve_palette_defaults_to_flatui():
    assert AvatarGenerator._resolve_palette(None) == av._PALETTES["flatui"]


def test_resolve_palette_by_name_is_case_insensitive():
    name = next(iter(av._PALETTES))
    assert AvatarGenerator._resolve_palette(name.upper()) == av._PALETTES[name]


def test_resolve_palette_rejects_unknown_name():
    with pytest.raises(ValueError, match="Unknown palette"):
        AvatarGenerator._resolve_palette("not-a-palette")


def test_resolve_palette_accepts_raw_list():
    custom = [(1, 2, 3), (4, 5, 6)]
    assert AvatarGenerator._resolve_palette(custom) == custom


# ── initials ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Ada Lovelace", "AL"),
        ("ada lovelace", "AL"),
        ("Ada", "A"),
        ("  ", "?"),
        ("Ada Byron King Lovelace", "AB"),  # capped at max_letters
    ],
)
def test_extract_initials(name: str, expected: str):
    assert AvatarGenerator.extract_initials(name) == expected


def test_extract_initials_single_letter_mode():
    assert AvatarGenerator.extract_initials("Ada Lovelace", single=True) == "A"


def test_extract_initials_preserves_case_when_not_uppercase():
    assert AvatarGenerator.extract_initials("ada lovelace", uppercase=False) == "al"
    assert AvatarGenerator.extract_initials("ada", single=True, uppercase=False) == "a"


def test_extract_initials_falls_back_for_non_alpha_names():
    """A name with no letters still yields something renderable."""
    assert AvatarGenerator.extract_initials("123") == "1"
    assert AvatarGenerator.extract_initials("123", uppercase=False) == "1"


def test_extract_initials_respects_max_letters():
    assert AvatarGenerator.extract_initials("Ada Byron King", max_letters=3) == "ABK"


# ── colors and sizes ────────────────────────────────────────────────


def test_pick_color_is_deterministic(gen: AvatarGenerator):
    assert gen.pick_color("Ada") == gen.pick_color("Ada")


def test_pick_color_empty_name_uses_first_entry(gen: AvatarGenerator):
    assert gen.pick_color("") == gen.palette[0]


def test_private_pick_color_empty_name(gen: AvatarGenerator):
    palette = [(9, 9, 9), (1, 1, 1)]
    assert gen._pick_color("", palette) == (9, 9, 9)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("#ff0000", (255, 0, 0)),
        ("00ff00", (0, 255, 0)),
        ("#abc", (170, 187, 204)),  # 3-char shorthand expands
        ("zzzzzz", (204, 204, 204)),  # invalid hex -> grey
        ("ff", (204, 204, 204)),  # wrong length -> grey
    ],
)
def test_parse_hex(value: str, expected: tuple[int, int, int]):
    assert AvatarGenerator._parse_hex(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("100", (100, 100)),
        ("100x150", (100, 150)),
        (" 64X32 ", (64, 32)),
        ("abc", (80, 80)),  # unparseable -> default
        ("100xabc", (80, 80)),  # bad height -> default
    ],
)
def test_parse_size(value: str, expected: tuple[int, int]):
    assert AvatarGenerator._parse_size(value) == expected


# ── PNG rendering ───────────────────────────────────────────────────


def _png_size(data: bytes) -> tuple[int, int]:
    return Image.open(io.BytesIO(data)).size


def test_generate_png_default(gen: AvatarGenerator):
    data = gen.generate_png("Ada Lovelace")
    assert _png_size(data) == (80, 80)


def test_generate_png_with_explicit_background_and_circle(gen: AvatarGenerator):
    data = gen.generate_png("Ada", size_str="120", bg="112233", circle=True)
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    assert img.size == (120, 120)
    assert img.getpixel((60, 60))[3] == 255  # centre is painted


def test_generate_png_with_rectangular_background(gen: AvatarGenerator):
    data = gen.generate_png("Ada", size_str="100x60", bg="abcdef")
    assert _png_size(data) == (100, 60)


def test_generate_png_with_circular_border(gen: AvatarGenerator):
    data = gen.generate_png("Ada", size_str="100", circle=True, border=6, border_color="ff0000")
    assert _png_size(data) == (100, 100)


def test_generate_png_with_rectangular_border(gen: AvatarGenerator):
    data = gen.generate_png("Ada", size_str="100", border=4, border_color="00ff00")
    assert _png_size(data) == (100, 100)


def test_generate_png_clamps_extreme_sizes(gen: AvatarGenerator):
    assert _png_size(gen.generate_png("Ada", size_str="1")) == (8, 8)
    assert _png_size(gen.generate_png("Ada", size_str="99999")) == (5000, 5000)


def test_generate_png_accepts_palette_override(gen: AvatarGenerator):
    data = gen.generate_png("Ada", palette=[(10, 20, 30)])
    assert _png_size(data) == (80, 80)


def test_generate_png_long_text_still_fits(gen: AvatarGenerator):
    """A tiny canvas with wide text exercises the font-fitting fallback."""
    data = gen.generate_png("Wm Wm", size_str="12", max_letters=2)
    assert _png_size(data) == (12, 12)


# ── SVG rendering ───────────────────────────────────────────────────


def test_generate_svg_structure(gen: AvatarGenerator):
    svg = gen.generate_svg("Ada Lovelace", size_str="90")
    assert svg.startswith("<svg") or "<svg" in svg
    assert 'width="90"' in svg
    assert "AL" in svg


def test_generate_svg_with_six_digit_background(gen: AvatarGenerator):
    svg = gen.generate_svg("Ada", bg="123456")
    assert "#123456" in svg


def test_generate_svg_with_shorthand_background(gen: AvatarGenerator):
    svg = gen.generate_svg("Ada", bg="abc")
    assert "#abcabc" in svg


def test_generate_svg_circle_with_border(gen: AvatarGenerator):
    svg = gen.generate_svg("Ada", size_str="100", circle=True, border=8, border_color="ff0000")
    assert "<circle" in svg
    assert 'stroke="#ff0000"' in svg
    assert 'stroke-width="8"' in svg


def test_generate_svg_rect_with_border(gen: AvatarGenerator):
    svg = gen.generate_svg("Ada", size_str="100", border=10, border_color="00ff00")
    assert "<rect" in svg
    assert 'stroke="#00ff00"' in svg


def test_generate_svg_without_bg_draws_no_background(gen: AvatarGenerator):
    """The palette colour is only painted when a background is explicitly asked for."""
    svg = gen.generate_svg("Ada", palette=[(1, 2, 3)])
    assert "<svg" in svg
    assert ">A</text>" in svg
    assert "<rect" not in svg
    assert "#010203" not in svg


def test_generate_svg_circle_background(gen: AvatarGenerator):
    """A circular background is drawn as <circle>, not <rect>."""
    svg = gen.generate_svg("Ada", size_str="100", bg="123456", circle=True)
    assert "<circle" in svg
    assert "<rect" not in svg
    assert "#123456" in svg
