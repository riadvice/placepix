"""Tests for AI image generation via OVHcloud AI Endpoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from src.image_manager import ImageEntry, ImageManager


def _clear_rate_limit():
    """Clear the global rate limit state."""
    import src.ai_generator as ag

    ag._rate_limit_last.clear()


def _make_test_manager(images_dir: Path, tmp_path: Path) -> ImageManager:
    """Create an ImageManager with test settings, patching all references."""
    import src.config

    # Save original values
    orig_dir = src.config.settings.dir
    orig_seed = src.config.settings.seed_dir_str
    orig_cache = src.config.settings.cache
    orig_s3 = src.config.settings.s3_enabled
    # Patch attributes on the existing settings object instead of replacing it,
    # because image_manager.py imported settings via 'from src.config import settings'
    # which binds to the object at import time.
    src.config.settings.dir = str(tmp_path)
    src.config.settings.seed_dir_str = str(images_dir)
    src.config.settings.cache = False
    src.config.settings.s3_enabled = False
    try:
        return ImageManager()
    finally:
        # Restore original values so other tests are not affected
        src.config.settings.dir = orig_dir
        src.config.settings.seed_dir_str = orig_seed
        src.config.settings.cache = orig_cache
        src.config.settings.s3_enabled = orig_s3


def test_ai_generation_disabled_by_default(client: TestClient):
    """AI generation endpoint returns 503 when disabled."""
    response = client.post("/api/ai-generate", json={"prompt": "a test"})
    assert response.status_code == 503
    data = response.json()
    assert "disabled" in data["detail"].lower()


def test_ai_generation_rate_limiting(client: TestClient, monkeypatch):
    """Rate limiting: 429 after second request within 1 second."""
    _clear_rate_limit()
    monkeypatch.setattr("src.config.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.main.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.ai_generator.settings.ai_generation_enabled", True)

    with patch("src.ai_generator.generate_image") as mock_gen:
        mock_gen.return_value = type(
            "Result",
            (),
            {
                "success": True,
                "path": Path("/tmp/test.png"),
                "s3_key": None,
                "filename": "test.png",
                "category": "nature",
                "id": 999,
                "prompt": "a test",
                "error": "",
            },
        )()

        # First request should succeed (or fail non-429)
        response1 = client.post("/api/ai-generate", json={"prompt": "a test"})
        assert response1.status_code != 429

        # Second request immediately should be rate limited
        response2 = client.post("/api/ai-generate", json={"prompt": "a test 2"})
        assert response2.status_code == 429
        assert "rate limit" in response2.json()["detail"].lower()


def test_ai_generation_requires_prompt(client: TestClient, monkeypatch):
    """Empty prompt returns 400."""
    _clear_rate_limit()
    monkeypatch.setattr("src.config.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.main.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.ai_generator.settings.ai_generation_enabled", True)

    response = client.post("/api/ai-generate", json={"prompt": "  "})
    assert response.status_code == 400
    assert "prompt" in response.json()["detail"].lower()


def test_ai_generation_prompt_too_long(client: TestClient, monkeypatch):
    """Prompt over 500 chars returns 400."""
    _clear_rate_limit()
    monkeypatch.setattr("src.config.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.main.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.ai_generator.settings.ai_generation_enabled", True)

    response = client.post("/api/ai-generate", json={"prompt": "x" * 501})
    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


def test_image_entry_ai_flag():
    """ImageEntry has ai flag, default False."""
    entry = ImageEntry(path=None, filename="test.jpg", category="nature")
    assert entry.ai is False

    entry_ai = ImageEntry(path=None, filename="test.jpg", category="nature", ai=True)
    assert entry_ai.ai is True


def test_manager_pick_prefers_ai_pool(tmp_path: Path):
    """ImageManager.pick() prefers ai-generated pool over regular."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    # Create regular category
    nature_dir = images_dir / "nature"
    nature_dir.mkdir()
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(nature_dir / "regular.jpg")

    # Create AI category
    ai_dir = images_dir / "ai-generated" / "nature"
    ai_dir.mkdir(parents=True)
    img2 = Image.new("RGB", (100, 100), color=(0, 255, 0))
    img2.save(ai_dir / "ai_image.jpg")

    manager = _make_test_manager(images_dir, tmp_path)

    # When requesting "nature", should get AI image first
    entry = manager.pick("nature")
    assert entry is not None
    assert entry.ai is True
    assert "ai_image" in entry.filename

    # Also check that ai-generated category exists
    ai_cat = manager.categories.get("ai-generated/nature")
    assert ai_cat is not None
    assert len(ai_cat.entries) == 1
    assert ai_cat.entries[0].ai is True


def test_manager_pick_fallback_when_ai_empty(tmp_path: Path):
    """ImageManager.pick() falls back to regular when AI pool is empty."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    # Only regular category, no AI
    nature_dir = images_dir / "nature"
    nature_dir.mkdir()
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(nature_dir / "regular.jpg")

    manager = _make_test_manager(images_dir, tmp_path)
    entry = manager.pick("nature")
    assert entry is not None
    assert entry.ai is False
    assert "regular" in entry.filename


def test_manager_pick_ai_only_method(tmp_path: Path):
    """ImageManager.pick_ai() returns only AI images."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    # Create regular + AI
    nature_dir = images_dir / "nature"
    nature_dir.mkdir()
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(nature_dir / "regular.jpg")

    ai_dir = images_dir / "ai-generated" / "nature"
    ai_dir.mkdir(parents=True)
    img2 = Image.new("RGB", (100, 100), color=(0, 255, 0))
    img2.save(ai_dir / "ai.jpg")

    manager = _make_test_manager(images_dir, tmp_path)

    # pick_ai should return AI image
    entry = manager.pick_ai("nature")
    assert entry is not None
    assert entry.ai is True

    # pick_ai returns None for non-existent AI category
    none_entry = manager.pick_ai("doesnotexist")
    assert none_entry is None


def test_ai_generation_success_response(client: TestClient, monkeypatch):
    """Successful generation returns correct JSON with experimental flag."""
    _clear_rate_limit()
    monkeypatch.setattr("src.config.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.main.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.ai_generator.settings.ai_generation_enabled", True)
    monkeypatch.setattr("src.config.settings.ovh_ai_endpoints_token", "fake-token")
    monkeypatch.setattr("src.ai_generator.settings.ovh_ai_endpoints_token", "fake-token")

    with patch("src.main.generate_image") as mock_gen:
        mock_gen.return_value = type(
            "Result",
            (),
            {
                "success": True,
                "path": Path("/tmp/test.png"),
                "s3_key": "ai-generated/nature/test.png",
                "filename": "test.png",
                "category": "nature",
                "id": 42,
                "prompt": "a cozy cabin",
                "error": "",
            },
        )()

        with (
            patch("src.main.manager.rescan"),
            patch("src.main.manager.get_by_filename") as mock_get,
        ):
            mock_get.return_value = ImageEntry(
                path=Path("/tmp/test.png"),
                filename="test.png",
                category="nature",
                id=42,
                ai=True,
            )
            response = client.post(
                "/api/ai-generate",
                json={
                    "prompt": "a cozy cabin",
                    "category": "nature",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["experimental"] is True
    assert data["ai"] is True
    assert data["prompt"] == "a cozy cabin"
    assert data["filename"] == "test.png"
    assert data["category"] == "nature"
