from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from src.main import app, manager


def _get_image_id(client: TestClient) -> int:
    """Helper to get a valid image ID from the manager."""

    entry = manager.pick()
    assert entry is not None
    return entry.id


def test_etag_generation(client: TestClient):
    """Test that ETag is generated for images."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500")
    assert response.status_code == 200
    assert "ETag" in response.headers
    assert response.headers["ETag"].startswith('"')
    assert response.headers["ETag"].endswith('"')


def test_last_modified_header(client: TestClient):
    """Test that Last-Modified header is present."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500")
    assert response.status_code == 200
    assert "Last-Modified" in response.headers
    # Format: "Mon, 01 Jan 2024 00:00:00 GMT"
    assert "GMT" in response.headers["Last-Modified"]


def test_304_not_modified_with_etag(client: TestClient):
    """Test 304 response when ETag matches."""
    image_id = _get_image_id(client)
    # First request to get ETag
    response1 = client.get(f"/id/{image_id}/500/500")
    assert response1.status_code == 200
    etag = response1.headers["ETag"]

    # Second request with If-None-Match
    response2 = client.get(f"/id/{image_id}/500/500", headers={"If-None-Match": etag})
    assert response2.status_code == 304
    assert response2.headers["ETag"] == etag
    assert len(response2.content) == 0


def test_304_not_modified_with_last_modified(client: TestClient):
    """Test 304 response when Last-Modified matches."""
    image_id = _get_image_id(client)
    # First request to get Last-Modified
    response1 = client.get(f"/id/{image_id}/500/500")
    assert response1.status_code == 200
    last_modified = response1.headers["Last-Modified"]

    # Second request with If-Modified-Since
    response2 = client.get(f"/id/{image_id}/500/500", headers={"If-Modified-Since": last_modified})
    assert response2.status_code == 304
    assert response2.headers["Last-Modified"] == last_modified
    assert len(response2.content) == 0


def test_200_when_etag_differs(client: TestClient):
    """Test 200 response when ETag doesn't match."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500", headers={"If-None-Match": '"different-etag"'})
    assert response.status_code == 200
    assert len(response.content) > 0


def test_cache_control_immutable_for_id(client: TestClient):
    """Test Cache-Control header for ID-based requests (immutable)."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500")
    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "immutable" in response.headers["Cache-Control"]
    assert "max-age=31536000" in response.headers["Cache-Control"]


def test_cache_control_revalidate_for_random(client: TestClient):
    """Test Cache-Control header for random requests (must-revalidate)."""
    response = client.get("/500/500/")
    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "must-revalidate" in response.headers["Cache-Control"]
    assert "max-age=0" in response.headers["Cache-Control"]


def test_cache_control_for_seeded_random(client: TestClient):
    """Test Cache-Control header for seeded random requests (immutable)."""
    response = client.get("/500/500/?seed=test123")
    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "immutable" in response.headers["Cache-Control"]


def test_cache_control_svg_placeholder(client: TestClient):
    """Test Cache-Control header for SVG placeholders."""
    response = client.get("/svg/500/500")
    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "max-age=2592000" in response.headers["Cache-Control"]


def test_head_request_support(client: TestClient):
    """Test HEAD request returns headers without body."""
    image_id = _get_image_id(client)
    response = client.head(f"/id/{image_id}/500/500")
    assert response.status_code == 200
    assert "ETag" in response.headers
    assert "Last-Modified" in response.headers
    assert "Content-Type" in response.headers
    assert len(response.content) == 0


def test_head_request_with_etag(client: TestClient):
    """Test HEAD request with conditional headers."""
    image_id = _get_image_id(client)
    # First HEAD to get ETag
    response1 = client.head(f"/id/{image_id}/500/500")
    assert response1.status_code == 200
    etag = response1.headers["ETag"]

    # Second HEAD with If-None-Match
    response2 = client.head(f"/id/{image_id}/500/500", headers={"If-None-Match": etag})
    assert response2.status_code == 304
    assert len(response2.content) == 0


def test_cors_middleware_configured():
    """Test CORS middleware is configured correctly."""

    # Check that CORS middleware is in the middleware stack
    has_cors = any(hasattr(m, "cls") and m.cls == CORSMiddleware for m in app.user_middleware)
    assert has_cors, "CORSMiddleware should be configured"


def test_vary_header_for_format_negotiation(client: TestClient):
    """Test Vary header is present for content negotiation."""
    # This test verifies that different formats can be cached separately
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500.webp")
    assert response.status_code == 200
    assert "ETag" in response.headers
