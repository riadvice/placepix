"""Tests for config module."""

from __future__ import annotations

from pathlib import Path

from src.config import Settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings(_env_file=None)
    assert settings.host == "127.0.0.1:3000"
    assert settings.dir == "./data"
    assert settings.cache is True
    assert settings.cdn == ""
    assert settings.min_width == 8
    assert settings.min_height == 8
    assert settings.max_width == 2400
    assert settings.max_height == 2400
    assert settings.upload_enabled is True
    assert settings.watermark_enabled is True
    assert settings.watermark_image == "static/watermark.png"
    assert settings.watermark_text == ""
    assert settings.watermark_position == "bottom-right"
    assert settings.watermark_opacity == 0.5


def test_bind_host_with_port():
    """Test bind_host property with port."""
    settings = Settings(host="0.0.0.0:3000")
    assert settings.bind_host == "0.0.0.0"


def test_bind_host_without_port():
    """Test bind_host property without port."""
    settings = Settings(host="localhost")
    assert settings.bind_host == "localhost"


def test_bind_port_with_port():
    """Test bind_port property with port."""
    settings = Settings(host="127.0.0.1:5000")
    assert settings.bind_port == 5000


def test_bind_port_without_port():
    """Test bind_port property defaults to 3000."""
    settings = Settings(host="localhost")
    assert settings.bind_port == 3000


def test_bind_port_custom():
    """Test bind_port with various ports."""
    settings = Settings(host="0.0.0.0:9999")
    assert settings.bind_port == 9999


def test_images_dir_property():
    """Test images_dir property returns resolved Path."""
    settings = Settings(dir="./test_images")
    assert isinstance(settings.images_dir, Path)
    assert settings.images_dir.is_absolute()


def test_cache_dir_property():
    """Test cache_dir property returns resolved Path."""
    settings = Settings()
    assert isinstance(settings.cache_dir, Path)
    assert settings.cache_dir.is_absolute()
    assert settings.cache_dir.name == ".cache"


def test_settings_from_env(monkeypatch):
    """Test settings can be loaded from environment variables."""
    monkeypatch.setenv("HOST", "0.0.0.0:8000")
    monkeypatch.setenv("DATA_DIR", "/custom/images")
    monkeypatch.setenv("CACHE", "false")
    monkeypatch.setenv("MAX_WIDTH", "4000")
    monkeypatch.setenv("WATERMARK_IMAGE", "/custom/watermark.png")

    settings = Settings()
    assert settings.host == "0.0.0.0:8000"
    assert settings.dir == "/custom/images"
    assert settings.cache is False
    assert settings.max_width == 4000
    assert settings.watermark_image == "/custom/watermark.png"


def test_watermark_settings():
    """Test watermark-related settings."""
    settings = Settings(
        watermark_enabled=True,
        watermark_text="© Test",
        watermark_position="top-left",
        watermark_opacity=0.8,
    )
    assert settings.watermark_enabled is True
    assert settings.watermark_text == "© Test"
    assert settings.watermark_position == "top-left"
    assert settings.watermark_opacity == 0.8


def test_size_limits():
    """Test custom size limits."""
    settings = Settings(min_width=16, min_height=16, max_width=5000, max_height=5000)
    assert settings.min_width == 16
    assert settings.min_height == 16
    assert settings.max_width == 5000
    assert settings.max_height == 5000


def test_cdn_setting():
    """Test CDN URL setting."""
    settings = Settings(cdn="https://cdn.example.com")
    assert settings.cdn == "https://cdn.example.com"


def test_upload_enabled_setting():
    """Test upload_enabled setting."""
    settings = Settings(upload_enabled=False)
    assert settings.upload_enabled is False
