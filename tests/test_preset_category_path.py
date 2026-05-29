"""Tests for preset and ratio endpoints with category in path."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _get_available_category(client: TestClient) -> str:
    """Helper to get an available category from the manager."""
    from src.main import manager

    categories = list(manager.categories.keys())
    return categories[0] if categories else ""


def test_preset_with_category_in_path(client: TestClient):
    """Test preset endpoint with category in URL path."""
    category = _get_available_category(client)
    if not category:
        return  # Skip if no categories available
    response = client.get(f"/preset/instagram-square/{category}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_preset_with_category_and_extension(client: TestClient):
    """Test preset with category and file extension."""
    category = _get_available_category(client)
    if not category:
        return  # Skip if no categories available
    response = client.get(f"/preset/youtube-thumbnail/{category}.webp")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"


def test_preset_with_category_and_seed(client: TestClient):
    """Test preset with category in path and seed parameter."""
    category = _get_available_category(client)
    if not category:
        return  # Skip if no categories available
    response = client.get(f"/preset/facebook-cover/{category}?seed=test123")
    assert response.status_code == 200


def test_ratio_with_category_in_path(client: TestClient):
    """Test ratio endpoint with category in URL path."""
    category = _get_available_category(client)
    if not category:
        return  # Skip if no categories available
    response = client.get(f"/ratio/16:9/1080/{category}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_ratio_with_category_and_extension(client: TestClient):
    """Test ratio with category and file extension."""
    category = _get_available_category(client)
    if not category:
        return  # Skip if no categories available
    response = client.get(f"/ratio/4:3/768/{category}.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_ratio_with_category_and_seed(client: TestClient):
    """Test ratio with category in path and seed parameter."""
    category = _get_available_category(client)
    if not category:
        return  # Skip if no categories available
    response = client.get(f"/ratio/1:1/1080/{category}?seed=test456")
    assert response.status_code == 200


def test_preset_category_with_filters(client: TestClient):
    """Test preset with category and various filters."""
    category = _get_available_category(client)
    if not category:
        return  # Skip if no categories available
    response = client.get(f"/preset/instagram-square/{category}?grayscale=true&blur=3&quality=90")
    assert response.status_code == 200


def test_ratio_category_with_filters(client: TestClient):
    """Test ratio with category and various filters."""
    category = _get_available_category(client)
    if not category:
        return  # Skip if no categories available
    response = client.get(f"/ratio/16:9/1080/{category}?sepia=true&border=5&padding=10")
    assert response.status_code == 200


def test_preset_without_category_still_works(client: TestClient):
    """Test that preset without category still works (backward compatibility)."""
    response = client.get("/preset/mobile")
    assert response.status_code == 200


def test_ratio_without_category_still_works(client: TestClient):
    """Test that ratio without category still works (backward compatibility)."""
    response = client.get("/ratio/21:9/1080")
    assert response.status_code == 200
