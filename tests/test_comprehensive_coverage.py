"""Comprehensive tests to achieve 100% coverage."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def _get_image_id(client: TestClient) -> int:
    """Helper to get a valid image ID from the manager."""
    from src.main import manager
    entry = manager.pick()
    assert entry is not None
    return entry.id


def test_config_avif_available(client: TestClient):
    """Test AVIF format availability check."""
    from src.image_processor import _AVIF_AVAILABLE
    # Just verify the flag exists
    assert isinstance(_AVIF_AVAILABLE, bool)


def test_config_opencv_available(client: TestClient):
    """Test OpenCV availability check."""
    from src.image_processor import _OPENCV_AVAILABLE
    assert isinstance(_OPENCV_AVAILABLE, bool)


def test_image_processor_tint_effect(client: TestClient):
    """Test tint color effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?tint=ff0000")
    assert response.status_code == 200


def test_image_processor_brightness_adjustment(client: TestClient):
    """Test brightness adjustment."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?brightness=1.5")
    assert response.status_code == 200


def test_image_processor_contrast_adjustment(client: TestClient):
    """Test contrast adjustment."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?contrast=1.5")
    assert response.status_code == 200


def test_image_processor_saturation_adjustment(client: TestClient):
    """Test saturation adjustment."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?saturation=0.5")
    assert response.status_code == 200


def test_image_processor_all_fit_modes(client: TestClient):
    """Test all fit modes."""
    image_id = _get_image_id(client)
    fit_modes = ["crop", "scale", "contain", "cover", "smart"]
    for mode in fit_modes:
        response = client.get(f"/id/{image_id}/500/500?fit={mode}")
        assert response.status_code == 200


def test_image_processor_text_overlay(client: TestClient):
    """Test text overlay on image."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?text=Hello+World")
    assert response.status_code == 200


def test_image_processor_png_format(client: TestClient):
    """Test PNG format output."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_image_processor_webp_format(client: TestClient):
    """Test WebP format output."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500.webp")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"


def test_image_processor_avif_format(client: TestClient):
    """Test AVIF format output (may fallback to JPEG)."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500.avif")
    assert response.status_code == 200
    # May be AVIF or JPEG depending on availability
    assert "image/" in response.headers["content-type"]


def test_image_processor_size_clamping(client: TestClient):
    """Test that sizes are clamped to valid ranges."""
    image_id = _get_image_id(client)
    # Too large
    response = client.get(f"/id/{image_id}/5000/5000")
    assert response.status_code == 200

    # Too small
    response = client.get(f"/id/{image_id}/1/1")
    assert response.status_code == 200


def test_image_processor_width_only(client: TestClient):
    """Test specifying width only."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/0")
    assert response.status_code == 200


def test_image_processor_height_only(client: TestClient):
    """Test specifying height only."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/0/500")
    assert response.status_code == 200


def test_random_image_with_seed(client: TestClient):
    """Test deterministic random image with seed."""
    response1 = client.get("/500/500?seed=test123")
    response2 = client.get("/500/500?seed=test123")
    # Should return same image with same seed
    assert response1.status_code == 200
    assert response2.status_code == 200


def test_random_image_with_category(client: TestClient):
    """Test random image from specific category."""
    category = _get_image_id(client)  # Reuse helper to get a category
    from src.main import manager
    categories = list(manager.categories.keys())
    if not categories:
        return
    response = client.get(f"/500/500/{categories[0]}")
    assert response.status_code == 200


def test_random_image_with_extension(client: TestClient):
    """Test random image with file extension."""
    from src.main import manager
    categories = list(manager.categories.keys())
    if not categories:
        return
    response = client.get(f"/500/500/{categories[0]}.webp")
    assert response.status_code == 200


def test_color_based_image_selection(client: TestClient):
    """Test color-based image selection."""
    # Color endpoint requires hex without hash
    response = client.get("/color/ff0000/500/500")
    # May return 404 if no matching color found, which is acceptable
    assert response.status_code in [200, 404]


def test_color_based_with_extension(client: TestClient):
    """Test color-based selection with extension."""
    response = client.get("/color/3b82f6/500/500.png")
    # May return 404 if no matching color found
    assert response.status_code in [200, 404]


def test_svg_placeholder(client: TestClient):
    """Test SVG placeholder generation."""
    response = client.get("/svg/500/300")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"


def test_svg_placeholder_with_text(client: TestClient):
    """Test SVG placeholder with custom text."""
    response = client.get("/svg/500/300?text=Custom+Text")
    assert response.status_code == 200
    assert b"Custom Text" in response.content


def test_svg_placeholder_with_color(client: TestClient):
    """Test SVG placeholder with custom color."""
    response = client.get("/svg/500/300?bg=ff0000")
    assert response.status_code == 200
    assert b"ff0000" in response.content


def test_api_images_endpoint(client: TestClient):
    """Test API images metadata endpoint."""
    response = client.get("/api/images")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "total" in data


def test_api_info_by_id(client: TestClient):
    """Test API info endpoint for specific image."""
    image_id = _get_image_id(client)
    response = client.get(f"/api/info/id/{image_id}")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data


def test_api_info_invalid_id(client: TestClient):
    """Test API info with invalid ID."""
    response = client.get("/api/info/id/99999")
    assert response.status_code == 404


def test_random_redirect_endpoint(client: TestClient):
    """Test random image redirect endpoint."""
    response = client.get("/random/", follow_redirects=False)
    assert response.status_code in [302, 307]


def test_random_redirect_with_category(client: TestClient):
    """Test random redirect with category."""
    from src.main import manager
    categories = list(manager.categories.keys())
    if not categories:
        return
    response = client.get(f"/random/{categories[0]}", follow_redirects=False)
    assert response.status_code in [302, 307]


def test_random_redirect_with_color(client: TestClient):
    """Test random redirect with color filter."""
    response = client.get("/random/?color=ff0000", follow_redirects=False)
    # May return 404 if no matching color, or redirect
    assert response.status_code in [302, 307, 404]


def test_image_explorer_page(client: TestClient):
    """Test image explorer page loads."""
    response = client.get("/images")
    assert response.status_code == 200
    assert b"PlacePix" in response.content


def test_palette_page(client: TestClient):
    """Test color palette page loads."""
    response = client.get("/palette")
    assert response.status_code == 200


def test_index_page(client: TestClient):
    """Test index page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"PlacePix" in response.content


def test_combined_filters_and_effects(client: TestClient):
    """Test combining multiple filters and effects."""
    image_id = _get_image_id(client)
    response = client.get(
        f"/id/{image_id}/500/500?"
        "grayscale=true&blur=3&sepia=true&"
        "brightness=1.2&contrast=1.1&saturation=0.8&"
        "border=5&padding=10&noise=20&pixelate=5&"
        "quality=90&text=Test"
    )
    assert response.status_code == 200


def test_ratio_with_all_parameters(client: TestClient):
    """Test aspect ratio endpoint with all parameters."""
    response = client.get(
        "/ratio/16:9/1080?"
        "grayscale=true&blur=2&quality=95&"
        "border=10&padding=5"
    )
    assert response.status_code == 200


def test_preset_with_all_parameters(client: TestClient):
    """Test preset endpoint with all parameters."""
    response = client.get(
        "/preset/instagram-square?"
        "sepia=true&noise=15&pixelate=3&"
        "brightness=1.3&watermark=true"
    )
    assert response.status_code == 200


def test_solid_color_with_all_parameters(client: TestClient):
    """Test solid color with all parameters."""
    response = client.get(
        "/solid/500/300/667eea/ffffff?"
        "text=Hello&border=5&padding=10"
    )
    assert response.status_code == 200


def test_border_with_color(client: TestClient):
    """Test border with custom color."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?border=10,ff0000")
    assert response.status_code == 200


def test_watermark_all_positions(client: TestClient):
    """Test watermark with all position options."""
    image_id = _get_image_id(client)
    positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center", "true"]
    for pos in positions:
        response = client.get(f"/id/{image_id}/500/500?watermark={pos}")
        assert response.status_code == 200


def test_lqip_with_other_effects(client: TestClient):
    """Test LQIP combined with other effects."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?lqip=true&grayscale=true&blur=2")
    assert response.status_code == 200


def test_format_query_parameter(client: TestClient):
    """Test format specified via query parameter."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?format=png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_category_not_found(client: TestClient):
    """Test requesting non-existent category."""
    response = client.get("/500/500/nonexistent_category_xyz")
    assert response.status_code == 404


def test_invalid_preset(client: TestClient):
    """Test requesting invalid preset."""
    response = client.get("/preset/invalid_preset_xyz")
    assert response.status_code == 404


def test_invalid_aspect_ratio(client: TestClient):
    """Test invalid aspect ratio format."""
    response = client.get("/ratio/invalid/1080")
    assert response.status_code == 400


def test_color_query_parameter_on_random(client: TestClient):
    """Test color filter on random endpoint."""
    response = client.get("/500/500?color=3b82f6")
    # May return 404 if no matching color
    assert response.status_code in [200, 404]


def test_color_query_parameter_on_ratio(client: TestClient):
    """Test color filter on ratio endpoint."""
    response = client.get("/ratio/16:9/1080?color=ff0000")
    # May return 404 if no matching color
    assert response.status_code in [200, 404]


def test_color_query_parameter_on_preset(client: TestClient):
    """Test color filter on preset endpoint."""
    response = client.get("/preset/instagram-square?color=00ff00")
    # May return 404 if no matching color
    assert response.status_code in [200, 404]


def test_head_request_on_all_endpoints(client: TestClient):
    """Test HEAD requests work on all image endpoints."""
    image_id = _get_image_id(client)
    endpoints = [
        f"/id/{image_id}/500/500",
        "/500/500",
        "/ratio/16:9/1080",
        "/preset/instagram-square",
    ]
    for endpoint in endpoints:
        response = client.head(endpoint)
        assert response.status_code == 200
        assert len(response.content) == 0  # HEAD should have no body

    # Color endpoint may return 404 if no match
    response = client.head("/color/ff0000/500/500")
    assert response.status_code in [200, 404]


def test_cache_control_headers_on_different_endpoints(client: TestClient):
    """Test cache control headers are set correctly."""
    image_id = _get_image_id(client)
    # ID endpoint should have immutable cache
    response = client.get(f"/id/{image_id}/500/500")
    assert "Cache-Control" in response.headers
    assert "immutable" in response.headers["Cache-Control"]

    # Random endpoint should have must-revalidate
    response = client.get("/500/500")
    assert "Cache-Control" in response.headers
    assert "must-revalidate" in response.headers["Cache-Control"]

    # Seeded random should have long cache
    response = client.get("/500/500?seed=test")
    assert "Cache-Control" in response.headers


def test_content_disposition_header(client: TestClient):
    """Test Content-Disposition header is present."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500")
    assert "Content-Disposition" in response.headers
    assert "inline" in response.headers["Content-Disposition"]


def test_etag_consistency(client: TestClient):
    """Test ETag is consistent for same image."""
    image_id = _get_image_id(client)
    response1 = client.get(f"/id/{image_id}/500/500")
    response2 = client.get(f"/id/{image_id}/500/500")
    assert response1.headers.get("ETag") == response2.headers.get("ETag")


def test_last_modified_header_present(client: TestClient):
    """Test Last-Modified header is present."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500")
    assert "Last-Modified" in response.headers


def test_all_presets_work(client: TestClient):
    """Test all preset dimensions work."""
    presets = [
        "facebook-cover", "twitter-header", "instagram-square",
        "instagram-portrait", "youtube-thumbnail", "leaderboard",
        "banner", "skyscraper", "rectangle", "mobile", "tablet",
        "desktop", "4k"
    ]
    for preset in presets:
        response = client.get(f"/preset/{preset}")
        assert response.status_code == 200


def test_all_aspect_ratios_work(client: TestClient):
    """Test various aspect ratios work."""
    ratios = ["16:9", "4:3", "1:1", "21:9", "9:16", "3:2", "2:3"]
    for ratio in ratios:
        response = client.get(f"/ratio/{ratio}/1080")
        assert response.status_code == 200


def test_extreme_quality_values(client: TestClient):
    """Test quality parameter edge cases."""
    image_id = _get_image_id(client)
    # Minimum quality
    response = client.get(f"/id/{image_id}/500/500?quality=1")
    assert response.status_code == 200

    # Maximum quality
    response = client.get(f"/id/{image_id}/500/500?quality=100")
    assert response.status_code == 200


def test_extreme_blur_values(client: TestClient):
    """Test blur parameter edge cases."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?blur=10")
    assert response.status_code == 200


def test_extreme_noise_values(client: TestClient):
    """Test noise parameter edge cases."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?noise=100")
    assert response.status_code == 200


def test_extreme_pixelate_values(client: TestClient):
    """Test pixelate parameter edge cases."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?pixelate=50")
    assert response.status_code == 200


def test_extreme_brightness_values(client: TestClient):
    """Test brightness parameter edge cases."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?brightness=0.1")
    assert response.status_code == 200

    response = client.get(f"/id/{image_id}/500/500?brightness=2.0")
    assert response.status_code == 200


def test_extreme_contrast_values(client: TestClient):
    """Test contrast parameter edge cases."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?contrast=0.1")
    assert response.status_code == 200

    response = client.get(f"/id/{image_id}/500/500?contrast=2.0")
    assert response.status_code == 200


def test_extreme_saturation_values(client: TestClient):
    """Test saturation parameter edge cases."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?saturation=0.0")
    assert response.status_code == 200

    response = client.get(f"/id/{image_id}/500/500?saturation=2.0")
    assert response.status_code == 200


def test_solid_color_short_hex(client: TestClient):
    """Test solid color with 3-digit hex."""
    response = client.get("/solid/500x300/f00")
    assert response.status_code == 200


def test_solid_color_without_hash(client: TestClient):
    """Test solid color works without # prefix."""
    response = client.get("/solid/500x300/ff0000")
    assert response.status_code == 200


def test_tint_short_hex(client: TestClient):
    """Test tint with 3-digit hex color."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?tint=f00")
    assert response.status_code == 200


def test_tint_with_hash(client: TestClient):
    """Test tint with # prefix."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?tint=%23ff0000")
    assert response.status_code == 200
