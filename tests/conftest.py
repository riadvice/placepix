from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from src.config import Settings
from src.image_manager import ImageManager
from src.main import app


@pytest.fixture
def test_images_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with test images."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    # Create a test image
    img = Image.new("RGB", (800, 600), color=(255, 0, 0))
    img.save(images_dir / "test1.jpg", "JPEG")

    img2 = Image.new("RGB", (1024, 768), color=(0, 255, 0))
    img2.save(images_dir / "test2.jpg", "JPEG")

    # Create a category
    category_dir = images_dir / "nature"
    category_dir.mkdir()
    img3 = Image.new("RGB", (640, 480), color=(0, 0, 255))
    img3.save(category_dir / "test3.jpg", "JPEG")

    return images_dir


@pytest.fixture
def test_settings(test_images_dir: Path, tmp_path: Path) -> Settings:
    """Create test settings."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    return Settings(
        host="127.0.0.1:3000",
        dir=str(test_images_dir),
        cache=True,
        cdn="",
        min_width=8,
        min_height=8,
        max_width=2400,
        max_height=2400,
        upload_enabled=True,
    )


@pytest.fixture
def client(test_settings: Settings, monkeypatch) -> TestClient:
    """Create a test client with test settings."""
    monkeypatch.setattr("src.config.settings", test_settings)
    monkeypatch.setattr("src.main.settings", test_settings)
    monkeypatch.setattr("src.image_manager.settings", test_settings)

    # Reinitialize manager with test settings

    manager = ImageManager()
    monkeypatch.setattr("src.main.manager", manager)

    return TestClient(app)
