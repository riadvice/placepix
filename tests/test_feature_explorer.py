"""Tests for the feature explorer page."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_feature_explorer_page(client: TestClient):
    """Test that feature explorer page loads."""
    response = client.get("/features")
    assert response.status_code == 200
    assert "Feature Explorer" in response.text
    assert "URL Constructor" in response.text


def test_feature_explorer_has_endpoint_tabs(client: TestClient):
    """Test that feature explorer has all endpoint options."""
    response = client.get("/features")
    assert response.status_code == 200
    assert "Random" in response.text
    assert "By ID" in response.text
    assert "Aspect Ratio" in response.text
    assert "Preset" in response.text
    assert "Solid Color" in response.text


def test_feature_explorer_has_filters(client: TestClient):
    """Test that feature explorer includes filter options."""
    response = client.get("/features")
    assert response.status_code == 200
    assert "Grayscale" in response.text
    assert "Sepia" in response.text
    assert "Blur" in response.text
    assert "Noise" in response.text
    assert "Pixelate" in response.text


def test_feature_explorer_has_layout_options(client: TestClient):
    """Test that feature explorer includes layout options."""
    response = client.get("/features")
    assert response.status_code == 200
    assert "Smart Crop" in response.text
    assert "Border" in response.text
    assert "Padding" in response.text


def test_feature_explorer_has_quality_controls(client: TestClient):
    """Test that feature explorer includes quality controls."""
    response = client.get("/features")
    assert response.status_code == 200
    assert "Quality" in response.text
    assert "LQIP" in response.text


def test_feature_explorer_has_color_adjustments(client: TestClient):
    """Test that feature explorer includes color adjustment options."""
    response = client.get("/features")
    assert response.status_code == 200
    assert "Brightness" in response.text
    assert "Contrast" in response.text
    assert "Saturation" in response.text


def test_feature_explorer_has_presets(client: TestClient):
    """Test that feature explorer lists preset options."""
    response = client.get("/features")
    assert response.status_code == 200
    assert "Instagram" in response.text
    assert "YouTube" in response.text
    assert "Facebook" in response.text


def test_feature_explorer_has_format_options(client: TestClient):
    """Test that feature explorer includes format selection."""
    response = client.get("/features")
    assert response.status_code == 200
    assert "JPEG" in response.text
    assert "PNG" in response.text
    assert "WebP" in response.text
    assert "AVIF" in response.text
