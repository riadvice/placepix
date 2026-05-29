"""Tests for /api/categories endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_api_categories_endpoint(client: TestClient):
    """Test /api/categories endpoint returns category list."""
    response = client.get("/api/categories")
    assert response.status_code == 200

    data = response.json()
    assert "categories" in data
    assert "count" in data
    assert isinstance(data["categories"], list)
    assert isinstance(data["count"], int)
    assert data["count"] == len(data["categories"])


def test_api_categories_content_type(client: TestClient):
    """Test /api/categories returns JSON."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_api_categories_has_categories(client: TestClient):
    """Test /api/categories returns actual categories."""
    response = client.get("/api/categories")
    data = response.json()

    # Should have at least some categories from test fixtures
    assert data["count"] > 0
    assert len(data["categories"]) > 0


def test_api_categories_format(client: TestClient):
    """Test /api/categories response format."""
    response = client.get("/api/categories")
    data = response.json()

    # Categories should be strings
    for category in data["categories"]:
        assert isinstance(category, str)
        assert len(category) > 0


def test_api_categories_detailed(client: TestClient):
    """Test /api/categories includes detailed metadata."""
    response = client.get("/api/categories")
    data = response.json()

    assert "detailed" in data
    assert isinstance(data["detailed"], list)

    # Check detailed format
    for cat_detail in data["detailed"]:
        assert "name" in cat_detail
        assert "count" in cat_detail
        assert "display_name" in cat_detail
        assert "description" in cat_detail
