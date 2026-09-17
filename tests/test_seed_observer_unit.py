"""Unit tests for font loading in src.seed and watcher startup in src.observer."""

from __future__ import annotations

from pathlib import Path
import shutil
from unittest.mock import MagicMock, patch

from PIL import ImageFont
import pytest

import src.observer as observer_mod
import src.seed as seed_mod


def _a_system_ttf() -> Path | None:
    """Any real .ttf on this machine, or None if the box has no fonts."""
    for root in ("/usr/share/fonts", "/System/Library/Fonts", "/Windows/Fonts"):
        base = Path(root)
        if base.exists():
            for f in base.rglob("*.ttf"):
                return f
    return None


# ── seed._load_font ─────────────────────────────────────────────────


def test_load_font_uses_custom_ttf(tmp_path: Path, monkeypatch):
    src_font = _a_system_ttf()
    if src_font is None:
        pytest.skip("no system .ttf available to copy")

    font_dir = tmp_path / "fonts"
    font_dir.mkdir()
    shutil.copy(src_font, font_dir / "custom.ttf")
    monkeypatch.setattr(seed_mod.settings, "font_dir", str(font_dir), raising=False)

    font = seed_mod._load_font(24)
    assert isinstance(font, ImageFont.FreeTypeFont)
    assert font.size == 24


def test_load_font_skips_unreadable_custom_fonts(tmp_path: Path, monkeypatch):
    """A corrupt .ttf/.ttc must be skipped rather than raising."""
    font_dir = tmp_path / "fonts"
    font_dir.mkdir()
    (font_dir / "broken.ttf").write_bytes(b"not a font")
    (font_dir / "broken.ttc").write_bytes(b"not a font either")
    monkeypatch.setattr(seed_mod.settings, "font_dir", str(font_dir), raising=False)

    font = seed_mod._load_font(18)
    assert font is not None  # fell through to a system font or the default


def test_load_font_uses_custom_ttc(tmp_path: Path, monkeypatch):
    """A .ttc is tried after .ttf files are exhausted."""
    src_font = _a_system_ttf()
    if src_font is None:
        pytest.skip("no system .ttf available to copy")

    font_dir = tmp_path / "fonts"
    font_dir.mkdir()
    shutil.copy(src_font, font_dir / "collection.ttc")
    monkeypatch.setattr(seed_mod.settings, "font_dir", str(font_dir), raising=False)

    assert seed_mod._load_font(20) is not None


def test_load_font_ignores_missing_custom_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(seed_mod.settings, "font_dir", str(tmp_path / "nope"), raising=False)
    assert seed_mod._load_font(12) is not None


def test_load_font_falls_back_to_default_without_any_font(monkeypatch):
    """With no custom dir and no system font dirs, Pillow's default is used."""
    monkeypatch.setattr(seed_mod.settings, "font_dir", "", raising=False)

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
    assert seed_mod._load_font(14) is not None


# ── observer.start_watching ─────────────────────────────────────────


def test_start_watching_skips_missing_images_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        observer_mod.settings, "seed_dir_str", str(tmp_path / "absent"), raising=False
    )
    obs = observer_mod.start_watching(MagicMock())
    assert obs.is_alive() is False  # never started
    assert not getattr(obs, "_watches", None)


def test_start_watching_schedules_and_starts(tmp_path: Path, monkeypatch):
    images = tmp_path / "images"
    images.mkdir()
    monkeypatch.setattr(observer_mod.settings, "seed_dir_str", str(images), raising=False)

    obs = observer_mod.start_watching(MagicMock())
    try:
        assert obs.is_alive() is True
    finally:
        obs.stop()
        obs.join(timeout=5)


def test_start_watching_survives_schedule_failure(tmp_path: Path, monkeypatch):
    """A watcher that cannot start must not take the app down with it."""
    images = tmp_path / "images"
    images.mkdir()
    monkeypatch.setattr(observer_mod.settings, "seed_dir_str", str(images), raising=False)

    with patch.object(
        observer_mod.Observer, "schedule", side_effect=OSError("inotify limit reached")
    ):
        obs = observer_mod.start_watching(MagicMock())

    assert obs.is_alive() is False
