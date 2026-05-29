from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import PRESETS, _parse_aspect_ratio


def test_aspect_ratio_16_9(client: TestClient):
    """Test 16:9 aspect ratio sizing."""
    response = client.get("/ratio/16:9/1080")
    assert response.status_code == 200
    assert "image/" in response.headers["content-type"]


def test_aspect_ratio_4_3(client: TestClient):
    """Test 4:3 aspect ratio sizing."""
    response = client.get("/ratio/4:3/768")
    assert response.status_code == 200


def test_aspect_ratio_1_1(client: TestClient):
    """Test 1:1 (square) aspect ratio."""
    response = client.get("/ratio/1:1/500")
    assert response.status_code == 200


def test_aspect_ratio_invalid(client: TestClient):
    """Test invalid aspect ratio format."""
    response = client.get("/ratio/invalid/1080")
    assert response.status_code == 400


def test_aspect_ratio_with_extension(client: TestClient):
    """Test aspect ratio with file extension."""
    response = client.get("/ratio/16:9/1080.webp")
    assert response.status_code == 200


def test_aspect_ratio_with_seed(client: TestClient):
    """Test aspect ratio with seed for deterministic selection."""
    response1 = client.get("/ratio/16:9/1080?seed=test123")
    response2 = client.get("/ratio/16:9/1080?seed=test123")
    assert response1.status_code == 200
    assert response2.status_code == 200
    # Same seed should give same image
    assert response1.content == response2.content


def test_preset_instagram_square(client: TestClient):
    """Test Instagram square preset."""
    response = client.get("/preset/instagram-square")
    assert response.status_code == 200


def test_preset_facebook_cover(client: TestClient):
    """Test Facebook cover preset."""
    response = client.get("/preset/facebook-cover")
    assert response.status_code == 200


def test_preset_youtube_thumbnail(client: TestClient):
    """Test YouTube thumbnail preset."""
    response = client.get("/preset/youtube-thumbnail")
    assert response.status_code == 200


def test_preset_leaderboard(client: TestClient):
    """Test leaderboard ad preset."""
    response = client.get("/preset/leaderboard")
    assert response.status_code == 200


def test_preset_mobile(client: TestClient):
    """Test mobile screen preset."""
    response = client.get("/preset/mobile")
    assert response.status_code == 200


def test_preset_4k(client: TestClient):
    """Test 4K preset."""
    response = client.get("/preset/4k")
    assert response.status_code == 200


def test_preset_invalid(client: TestClient):
    """Test invalid preset name."""
    response = client.get("/preset/nonexistent")
    assert response.status_code == 404


def test_preset_with_filters(client: TestClient):
    """Test preset with image filters."""
    response = client.get("/preset/instagram-square?grayscale=true&blur=2")
    assert response.status_code == 200


def test_preset_with_extension(client: TestClient):
    """Test preset with file extension."""
    response = client.get("/preset/desktop.png")
    assert response.status_code == 200


def test_solid_color_basic(client: TestClient):
    """Test basic solid color placeholder."""
    response = client.get("/solid/500/500/ff0000")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_solid_color_with_fg(client: TestClient):
    """Test solid color with foreground color."""
    response = client.get("/solid/500/500/000000/ffffff")
    assert response.status_code == 200


def test_solid_color_with_text(client: TestClient):
    """Test solid color with text overlay."""
    response = client.get("/solid/500/500/3b82f6?text=Hello")
    assert response.status_code == 200


def test_solid_color_short_hex(client: TestClient):
    """Test solid color with 3-digit hex."""
    response = client.get("/solid/300/200/f00")
    assert response.status_code == 200


def test_solid_color_without_hash(client: TestClient):
    """Test solid color without # prefix."""
    response = client.get("/solid/400/300/00ff00")
    assert response.status_code == 200


def test_solid_color_cache_headers(client: TestClient):
    """Test solid color has proper cache headers."""
    response = client.get("/solid/500/500/cccccc")
    assert response.status_code == 200
    assert "ETag" in response.headers
    assert "Cache-Control" in response.headers
    assert "immutable" in response.headers["Cache-Control"]


def test_all_presets_exist():
    """Test that all documented presets are available."""

    expected_presets = [
        "facebook-cover",
        "twitter-header",
        "instagram-square",
        "instagram-portrait",
        "youtube-thumbnail",
        "leaderboard",
        "banner",
        "skyscraper",
        "rectangle",
        "mobile",
        "tablet",
        "desktop",
        "4k",
    ]

    for preset in expected_presets:
        assert preset in PRESETS, f"Preset {preset} not found"


def test_aspect_ratio_parser():
    """Test aspect ratio parsing function."""

    # Valid ratios
    assert _parse_aspect_ratio("16:9", 1080) == (1920, 1080)
    assert _parse_aspect_ratio("4:3", 768) == (1024, 768)
    assert _parse_aspect_ratio("1:1", 500) == (500, 500)
    assert _parse_aspect_ratio("21:9", 1080) == (2520, 1080)

    # Invalid ratios
    assert _parse_aspect_ratio("invalid", 1080) == (0, 0)
    assert _parse_aspect_ratio("16", 1080) == (0, 0)
    assert _parse_aspect_ratio("16:0", 1080) == (0, 0)
