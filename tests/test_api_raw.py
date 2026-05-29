"""Tests for /api/raw endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def _get_test1_id() -> int:
    """Look up the ID of test1.jpg in the root category."""
    from src.main import manager

    entry = manager.get_by_filename("test1.jpg")
    assert entry is not None, "test1.jpg not found in manager"
    return entry.id


def test_api_raw_by_id_success(client: TestClient):
    """Test serving raw image by ID returns original file."""
    image_id = _get_test1_id()
    response = client.get(f"/api/raw/id/{image_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert "Content-Disposition" in response.headers
    assert 'inline; filename="test1.jpg"' in response.headers["Content-Disposition"]
    assert response.content is not None
    assert len(response.content) > 0


def test_api_raw_by_id_etag_caching(client: TestClient):
    """Test raw image returns 304 when ETag matches."""
    image_id = _get_test1_id()
    response = client.get(f"/api/raw/id/{image_id}")
    assert response.status_code == 200
    etag = response.headers["ETag"]

    response2 = client.get(f"/api/raw/id/{image_id}", headers={"If-None-Match": etag})
    assert response2.status_code == 304


def test_api_raw_by_id_not_found(client: TestClient):
    """Test serving raw image by non-existent ID returns 404."""
    response = client.get("/api/raw/id/99999")
    assert response.status_code == 404


def test_api_raw_by_path_success(client: TestClient):
    """Test serving raw image by category and filename."""
    response = client.get("/api/raw/nature/test3.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert "Content-Disposition" in response.headers
    assert 'inline; filename="test3.jpg"' in response.headers["Content-Disposition"]
    assert response.content is not None
    assert len(response.content) > 0


def test_api_raw_by_path_not_found(client: TestClient):
    """Test serving raw image by non-existent path returns 404."""
    response = client.get("/api/raw/nature/nonexistent.jpg")
    assert response.status_code == 404


def test_api_raw_by_path_category_not_found(client: TestClient):
    """Test serving raw image by non-existent category returns 404."""
    response = client.get("/api/raw/unknown/test.jpg")
    assert response.status_code == 404


def test_api_raw_unmodified_matches_processed(client: TestClient, test_images_dir: Path):
    """Test raw image bytes match the original file on disk."""
    image_id = _get_test1_id()
    response = client.get(f"/api/raw/id/{image_id}")
    assert response.status_code == 200
    original = (test_images_dir / "test1.jpg").read_bytes()
    assert response.content == original


def test_api_raw_head_request(client: TestClient):
    """Test HEAD request returns headers without body."""
    image_id = _get_test1_id()
    response = client.head(f"/api/raw/id/{image_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b""
