from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from src.config import Settings
from src.image_manager import ImageManager


@pytest.fixture
def s3_test_image_bytes() -> bytes:
    """Create a small test image in memory."""
    buffer = io.BytesIO()
    img = Image.new("RGB", (640, 480), color=(0, 128, 255))
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def s3_settings(test_images_dir: Path, tmp_path: Path, s3_test_image_bytes: bytes) -> Settings:
    """Settings with S3 enabled."""
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
        s3_enabled=True,
        s3_endpoint="https://s3.rbx.io.cloud.ovh.net",
        s3_access_key="test-key",
        s3_secret_key="test-secret",
        s3_bucket="test-bucket",
        s3_prefix="photos/",
        s3_region="rbx",
    )


@pytest.fixture
def s3_client(
    s3_settings: Settings, monkeypatch, s3_test_image_bytes: bytes
) -> tuple[TestClient, "ImageManager", MagicMock]:
    """Create a test client with S3 mocked."""
    monkeypatch.setattr("src.config.settings", s3_settings)
    monkeypatch.setattr("src.main.settings", s3_settings)
    monkeypatch.setattr("src.image_manager.settings", s3_settings)

    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_pages = [
        {
            "Contents": [
                {"Key": "photos/nature/forest.jpg"},
                {"Key": "photos/beach.jpg"},
                {"Key": "photos/nature/mountain.jpg"},
            ]
        }
    ]
    mock_paginator.paginate.return_value = mock_pages
    mock_client.get_paginator.return_value = mock_paginator

    mock_body = MagicMock()
    mock_body.read.return_value = s3_test_image_bytes
    mock_client.get_object.return_value = {"Body": mock_body}

    with (
        patch("src.image_manager.boto3.client", return_value=mock_client),
        patch("src.main.boto3.client", return_value=mock_client),
    ):
        from src.image_manager import ImageManager
        from src.main import app

        manager = ImageManager()
        monkeypatch.setattr("src.main.manager", manager)

        yield TestClient(app), manager, mock_client


@pytest.mark.slow
def test_s3_scan_merges_categories(s3_client):
    """Test that S3 images are merged into categories."""
    _client, manager, _mock = s3_client

    categories = manager.list_categories()
    cat_names = {c["name"] for c in categories}

    assert "nature" in cat_names
    assert "__root" in cat_names


@pytest.mark.slow
def test_s3_image_served(s3_client):
    """Test that S3 images are served correctly."""
    client, manager, _mock = s3_client

    response = client.get("/500/500/nature/forest.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


@pytest.mark.slow
def test_s3_info_endpoint(s3_client):
    """Test that S3 images show up in info endpoint."""
    client, manager, _mock = s3_client

    response = client.get("/500/500/nature/forest.jpg?info")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "nature"


@pytest.mark.slow
def test_s3_disabled_falls_back_to_local_only(test_images_dir, monkeypatch):
    """Test that when S3 is disabled, only local images are used."""
    from src.config import Settings

    settings = Settings(
        host="127.0.0.1:3000",
        dir=str(test_images_dir),
        cache=True,
        cdn="",
        min_width=8,
        min_height=8,
        max_width=2400,
        max_height=2400,
        upload_enabled=True,
        s3_enabled=False,
    )
    monkeypatch.setattr("src.config.settings", settings)
    monkeypatch.setattr("src.main.settings", settings)
    monkeypatch.setattr("src.image_manager.settings", settings)

    from src.image_manager import ImageManager

    manager = ImageManager()
    monkeypatch.setattr("src.main.manager", manager)

    # Should only have local test images
    categories = manager.list_categories()
    cat_names = {c["name"] for c in categories}
    assert len(cat_names) == 1  # Only __root


@pytest.mark.slow
def test_local_image_still_works_with_s3_enabled(s3_client):
    """Test that local images are still served when S3 is enabled."""
    client, manager, _mock = s3_client

    entry = manager.get_entry("__root", "test1.jpg")
    assert entry is not None
    assert entry.s3_key == ""
    assert entry.path is not None

    response = client.get(f"/id/{entry.id}/200/150")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0
