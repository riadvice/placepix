"""Unit tests for src.ai_generator internals (no network)."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image
import pytest
import requests

import src.ai_generator as ag


def _png_b64() -> str:
    """A tiny valid PNG, base64-encoded the way the AI endpoint returns it."""
    from io import BytesIO

    buf = BytesIO()
    Image.new("RGB", (8, 8), (10, 20, 30)).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def ai_settings(tmp_path: Path, monkeypatch):
    """Point the generator at a temp image dir with AI generation enabled."""
    monkeypatch.setattr(ag.settings, "seed_dir_str", str(tmp_path), raising=False)
    monkeypatch.setattr(ag.settings, "ai_generation_enabled", True, raising=False)
    monkeypatch.setattr(ag.settings, "ovh_ai_endpoints_token", "test-token", raising=False)
    monkeypatch.setattr(ag.settings, "ovh_ai_endpoints_url", "https://ai.example/v1", raising=False)
    monkeypatch.setattr(ag.settings, "ai_max_images_per_category", 3, raising=False)
    monkeypatch.setattr(ag.settings, "ai_s3_upload_enabled", False, raising=False)
    monkeypatch.setattr(ag.settings, "s3_enabled", False, raising=False)
    return ag.settings


# ── helpers ─────────────────────────────────────────────────────────


def test_get_client_ip_prefers_forwarded_header():
    ip = ag._get_client_ip({"x-forwarded-for": "203.0.113.7, 10.0.0.1"}, "10.0.0.1")
    assert ip == "203.0.113.7"


def test_get_client_ip_falls_back_to_client_host():
    assert ag._get_client_ip({}, "192.0.2.5") == "192.0.2.5"


def test_get_client_ip_unknown_when_nothing_available():
    assert ag._get_client_ip({}, None) == "unknown"


def test_check_rate_limit_allows_then_blocks():
    ag._rate_limit_last.clear()
    allowed, retry = asyncio.run(ag.check_rate_limit("198.51.100.1"))
    assert allowed is True and retry == 0.0

    allowed, retry = asyncio.run(ag.check_rate_limit("198.51.100.1"))
    assert allowed is False and 0 < retry <= 1.0


def test_cleanup_rate_limit_drops_stale_entries():
    ag._rate_limit_last.clear()
    ag._rate_limit_last["stale"] = 0.0  # epoch: definitely older than 60s
    ag._rate_limit_last["fresh"] = ag.time.time()
    ag._cleanup_rate_limit()
    assert "stale" not in ag._rate_limit_last
    assert "fresh" in ag._rate_limit_last


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("A Red Fox!", "a-red-fox"),
        ("  spaced   out  ", "spaced-out"),
        ("---dashes---", "dashes"),
        ("émoji ✨ stripped", "moji-stripped"),
    ],
)
def test_slugify(raw: str, expected: str):
    assert ag._slugify(raw) == expected


def test_slugify_truncates_to_80_chars():
    assert len(ag._slugify("word " * 100)) <= 80


# ── generate_image guard clauses ────────────────────────────────────


def test_generate_image_disabled(monkeypatch):
    monkeypatch.setattr(ag.settings, "ai_generation_enabled", False, raising=False)
    result = ag.generate_image("a cat", "animals")
    assert result.success is False
    assert "disabled" in result.error


def test_generate_image_without_token(ai_settings, monkeypatch):
    monkeypatch.setattr(ag.settings, "ovh_ai_endpoints_token", "", raising=False)
    result = ag.generate_image("a cat", "animals")
    assert result.success is False
    assert "OVH_AI_ENDPOINTS_TOKEN" in result.error


def test_generate_image_respects_category_cap(ai_settings, tmp_path: Path):
    cat_dir = tmp_path / "ai-generated" / "animals"
    cat_dir.mkdir(parents=True)
    for i in range(3):  # ai_max_images_per_category == 3
        (cat_dir / f"old{i}.png").write_bytes(b"x")

    result = ag.generate_image("a cat", "animals")
    assert result.success is False
    assert "cap" in result.error


# ── generate_image request handling ─────────────────────────────────


def test_generate_image_success_writes_file(ai_settings, tmp_path: Path):
    response = MagicMock()
    response.json.return_value = {"images": [{"b64_json": _png_b64()}]}

    with patch("src.ai_generator.requests.post", return_value=response) as post:
        result = ag.generate_image(
            "a red fox", "animals", negative_prompt="blurry", seed=42, steps=12, cfg_scale=6.5
        )

    assert result.success is True
    assert result.category == "animals"
    assert result.prompt == "a red fox"
    assert result.filename.startswith("a-red-fox_")
    assert result.path is not None and result.path.exists()
    assert Image.open(result.path).size == (8, 8)

    payload = post.call_args.kwargs["json"]
    assert payload["seed"] == 42
    assert payload["num_inference_steps"] == 12
    assert payload["guidance_scale"] == 6.5
    assert payload["negative_prompt"] == "blurry"


def test_generate_image_clamps_dimensions(ai_settings):
    response = MagicMock()
    response.json.return_value = {"images": [{"b64_json": _png_b64()}]}

    with patch("src.ai_generator.requests.post", return_value=response) as post:
        ag.generate_image("x", "animals", width=99999, height=1)

    payload = post.call_args.kwargs["json"]
    assert payload["width"] == 2048
    assert payload["height"] == 256


def test_generate_image_uses_default_steps_and_scale(ai_settings, monkeypatch):
    monkeypatch.setattr(ag.settings, "ai_default_steps", 25, raising=False)
    monkeypatch.setattr(ag.settings, "ai_default_cfg_scale", 8.5, raising=False)
    response = MagicMock()
    response.json.return_value = {"images": [{"b64_json": _png_b64()}]}

    with patch("src.ai_generator.requests.post", return_value=response) as post:
        ag.generate_image("x", "animals")

    payload = post.call_args.kwargs["json"]
    assert payload["num_inference_steps"] == 25
    assert payload["guidance_scale"] == 8.5
    assert "seed" not in payload


def test_generate_image_no_images_returned(ai_settings):
    response = MagicMock()
    response.json.return_value = {"images": []}
    with patch("src.ai_generator.requests.post", return_value=response):
        result = ag.generate_image("x", "animals")
    assert result.success is False
    assert "No image returned" in result.error


def test_generate_image_empty_b64(ai_settings):
    response = MagicMock()
    response.json.return_value = {"images": [{"b64_json": ""}]}
    with patch("src.ai_generator.requests.post", return_value=response):
        result = ag.generate_image("x", "animals")
    assert result.success is False
    assert "Empty image data" in result.error


def test_generate_image_request_exception(ai_settings):
    with patch("src.ai_generator.requests.post", side_effect=requests.RequestException("timeout")):
        result = ag.generate_image("x", "animals")
    assert result.success is False
    assert "request failed" in result.error


def test_generate_image_unexpected_exception(ai_settings):
    response = MagicMock()
    response.json.side_effect = ValueError("not json")
    with patch("src.ai_generator.requests.post", return_value=response):
        result = ag.generate_image("x", "animals")
    assert result.success is False
    assert "AI generation failed" in result.error


def test_generate_image_uploads_to_s3_when_enabled(ai_settings, monkeypatch):
    monkeypatch.setattr(ag.settings, "ai_s3_upload_enabled", True, raising=False)
    monkeypatch.setattr(ag.settings, "s3_enabled", True, raising=False)
    response = MagicMock()
    response.json.return_value = {"images": [{"b64_json": _png_b64()}]}

    with (
        patch("src.ai_generator.requests.post", return_value=response),
        patch("src.ai_generator._upload_to_s3", return_value="ai-generated/animals/x.png") as up,
    ):
        result = ag.generate_image("x", "animals")

    assert result.success is True
    assert result.s3_key == "ai-generated/animals/x.png"
    assert up.call_count == 1


# ── _upload_to_s3 ───────────────────────────────────────────────────


def test_upload_to_s3_success(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(ag.settings, "s3_bucket", "bucket", raising=False)
    with patch("boto3.client", return_value=client):
        key = ag._upload_to_s3(b"bytes", "ai-generated/cats/a.png")

    assert key == "ai-generated/cats/a.png"
    assert client.put_object.call_args.kwargs["Bucket"] == "bucket"
    assert client.put_object.call_args.kwargs["ContentType"] == "image/png"


def test_upload_to_s3_returns_none_on_failure():
    with patch("boto3.client", side_effect=RuntimeError("no credentials")):
        assert ag._upload_to_s3(b"bytes", "k") is None
