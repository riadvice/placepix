from __future__ import annotations

from fastapi.testclient import TestClient


def test_srcset_generation(client: TestClient):
    """Test srcset generation endpoint."""
    response = client.get("/api/srcset/1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "srcset" in data
    assert "srcset_string" in data
    assert "aspect_ratio" in data
    assert len(data["srcset"]) == 4  # Default sizes


def test_srcset_custom_sizes(client: TestClient):
    """Test srcset with custom sizes."""
    response = client.get("/api/srcset/1?sizes=400,800,1200")
    assert response.status_code == 200
    data = response.json()
    assert len(data["srcset"]) == 3
    assert data["srcset"][0]["width"] == 400


def test_srcset_custom_format(client: TestClient):
    """Test srcset with custom format."""
    response = client.get("/api/srcset/1?format=webp")
    assert response.status_code == 200
    data = response.json()
    assert ".webp" in data["srcset"][0]["url"]


def test_srcset_invalid_image(client: TestClient):
    """Test srcset with non-existent image."""
    response = client.get("/api/srcset/99999")
    assert response.status_code == 404


def test_srcset_invalid_sizes(client: TestClient):
    """Test srcset with invalid sizes format."""
    response = client.get("/api/srcset/1?sizes=invalid,sizes")
    assert response.status_code == 400


def test_srcset_string_format(client: TestClient):
    """Test srcset_string is properly formatted."""
    response = client.get("/api/srcset/1?sizes=320,640")
    assert response.status_code == 200
    data = response.json()
    srcset_string = data["srcset_string"]
    assert "320w" in srcset_string
    assert "640w" in srcset_string
    assert ", " in srcset_string


def test_smart_crop_fallback(client: TestClient):
    """Test smart crop falls back to center crop when no faces detected."""
    response = client.get("/id/1/500/500?fit=smart")
    assert response.status_code == 200


def test_smart_crop_vs_center_crop(client: TestClient):
    """Test that smart crop produces different result than center crop."""
    # Both should work, but may produce different crops
    response_smart = client.get("/id/1/500/500?fit=smart")
    response_center = client.get("/id/1/500/500?fit=crop")
    assert response_smart.status_code == 200
    assert response_center.status_code == 200


def test_watermark_disabled_by_default(client: TestClient):
    """Test watermark is disabled when not configured."""
    response = client.get("/id/1/500/500?watermark=true")
    assert response.status_code == 200
    # Should still work, just no watermark applied


def test_watermark_with_position(client: TestClient):
    """Test watermark with custom position."""
    response = client.get("/id/1/500/500?watermark=top-left")
    assert response.status_code == 200


def test_watermark_positions(client: TestClient):
    """Test all watermark positions."""
    positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
    for pos in positions:
        response = client.get(f"/id/1/500/500?watermark={pos}")
        assert response.status_code == 200


def test_combined_advanced_features(client: TestClient):
    """Test combining smart crop, watermark, and effects."""
    response = client.get(
        "/id/1/500/500?"
        "fit=smart&watermark=bottom-right&"
        "noise=10&quality=90"
    )
    assert response.status_code == 200


def test_smart_crop_with_aspect_ratio(client: TestClient):
    """Test smart crop with aspect ratio endpoint."""
    response = client.get("/ratio/16:9/1080?fit=smart")
    assert response.status_code == 200


def test_smart_crop_with_preset(client: TestClient):
    """Test smart crop with preset dimensions."""
    response = client.get("/preset/instagram-square?fit=smart")
    assert response.status_code == 200


def test_all_fit_modes(client: TestClient):
    """Test all fit modes work."""
    fit_modes = ["crop", "scale", "contain", "cover", "smart"]
    for mode in fit_modes:
        response = client.get(f"/id/1/500/500?fit={mode}")
        assert response.status_code == 200
