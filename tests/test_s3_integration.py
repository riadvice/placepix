from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.config import Settings


@pytest.fixture
def s3_test_image_bytes() -> bytes:
    """Create a small test image in memory."""
    buffer = io.BytesIO()
    img = Image.new("RGB", (640, 480), color=(0, 128, 255))
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def s3_settings(
    test_images_dir: Path, tmp_path: Path, s3_test_image_bytes: bytes
) -> Settings:
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
        max_width=2000,
        max_height=2000,
        upload_enabled=True,
        admin_password="",
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

    with patch("src.image_manager.boto3.client", return_value=mock_client), patch(
        "src.main.boto3.client", return_value=mock_client
    ):
        from src.image_manager import ImageManager
        from src.main import app

        manager = ImageManager()
        monkeypatch.setattr("src.main.manager", manager)

        yield TestClient(app), manager, mock_client


def test_s3_scan_merges_categories(s3_client):
    """Test that S3 images are merged into categories."""
    _client, manager, _mock = s3_client

    categories = manager.list_categories()
    cat_names = {c["name"] for c in categories}

    assert "nature" in cat_names
    assert "__root" in cat_names

    nature_cat = next(c for c in categories if c["name"] == "nature")
    # Local test3.jpg + S3 forest.jpg + S3 mountain.jpg
    assert nature_cat["count"] == 3


def test_s3_image_served(s3_client):
    """Test that an S3-sourced image can be served."""
    client, manager, _mock = s3_client

    entry = manager.get_entry("nature", "forest.jpg")
    assert entry is not None
    assert entry.s3_key == "photos/nature/forest.jpg"

    response = client.get(f"/id/{entry.id}/200/150")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


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


def test_s3_info_endpoint(s3_client):
    """Test that the info endpoint works for S3 images."""
    client, manager, _mock = s3_client

    entry = manager.get_entry("nature", "forest.jpg")
    assert entry is not None

    response = client.get(f"/api/info/id/{entry.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "forest.jpg"
    assert data["category"] == "nature"
    assert data["width"] == 640
    assert data["height"] == 480


def test_s3_disabled_falls_back_to_local_only(test_images_dir, monkeypatch):
    """Test that when S3_ENABLED=false, only local images are scanned."""
    settings = Settings(
        host="127.0.0.1:3000",
        dir=str(test_images_dir),
        cache=True,
        s3_enabled=False,
    )
    monkeypatch.setattr("src.config.settings", settings)
    monkeypatch.setattr("src.image_manager.settings", settings)

    from src.image_manager import ImageManager

    manager = ImageManager()
    total = manager.total
    for cat in manager.categories.values():
        for entry in cat.entries:
            assert entry.s3_key == ""
    assert total > 0
