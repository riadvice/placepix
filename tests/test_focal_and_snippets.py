from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient
import numpy as np
from PIL import Image, ImageDraw
import pytest

from src.image_manager import ImageEntry, ImageManager
from src.image_processor import ImageProcessor
import src.main


def _entry(id: int, path: Path | None, filename: str = "img.jpg") -> ImageEntry:
    return ImageEntry(
        id=id,
        path=path,
        filename=filename,
        category="root",
    )


def test_detect_focal_point(tmp_path: Path) -> None:
    """Focal point detection finds a salient subject."""
    img = Image.new("RGB", (400, 300), color=(128, 128, 128))
    draw = ImageDraw.Draw(img)
    draw.rectangle([250, 50, 350, 250], fill=(255, 0, 0))
    img_path = tmp_path / "focal.jpg"
    img.save(img_path, "JPEG")

    fx, fy = ImageManager._detect_focal_point(img_path)
    assert 0.65 < fx < 0.85
    assert 0.35 < fy < 0.65


def test_detect_focal_point_branches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Focal point detection handles missing and degenerate inputs."""
    # Non-existent image
    assert ImageManager._detect_focal_point(tmp_path / "missing.jpg") == (0.5, 0.5)

    # Valid image, saliency succeeds where face detection is skipped
    img = Image.new("RGB", (400, 300), color=(128, 128, 128))
    img_path = tmp_path / "focal2.jpg"
    img.save(img_path, "JPEG")

    # Zero-sized image
    monkeypatch.setattr(
        "src.image_manager.cv2.imread",
        lambda _p: np.zeros((0, 0, 3), dtype=np.uint8),
    )
    assert ImageManager._detect_focal_point(img_path) == (0.5, 0.5)
    monkeypatch.undo()

    # Face detection raises, falls back to saliency
    def _fake_cascade(*_args, **_kwargs):
        raise RuntimeError("no face cascade")
    monkeypatch.setattr("src.image_manager.cv2.CascadeClassifier", _fake_cascade)
    fx, fy = ImageManager._detect_focal_point(img_path)
    assert 0.0 <= fx <= 1.0
    assert 0.0 <= fy <= 1.0
    monkeypatch.undo()

    # Saliency raises
    class _FakeClassifier:
        def detectMultiScale(self, *_args, **_kwargs):
            return ()
    monkeypatch.setattr("src.image_manager.cv2.CascadeClassifier", _FakeClassifier)
    monkeypatch.setattr(
        "src.image_manager.cv2.saliency.StaticSaliencyFineGrained_create",
        lambda: (_ for _ in ()).throw(RuntimeError("no saliency")),
    )
    assert ImageManager._detect_focal_point(img_path) == (0.5, 0.5)
    monkeypatch.undo()

    # Outer exception (cv2.imread raises)
    monkeypatch.setattr(
        "src.image_manager.cv2.imread",
        lambda _p: (_ for _ in ()).throw(RuntimeError("read")),
    )
    assert ImageManager._detect_focal_point(img_path) == (0.5, 0.5)


def test_crop_around_focal() -> None:
    """Cropping with a focal point shifts the crop around the subject."""
    img = Image.new("RGB", (400, 300), color=(128, 128, 128))
    draw = ImageDraw.Draw(img)
    draw.rectangle([250, 50, 350, 250], fill=(255, 0, 0))

    buffer = io.BytesIO()
    img.save(buffer, "JPEG")
    buffer.seek(0)

    processor = ImageProcessor()
    centered = processor.process(buffer, width=100, height=100, fit="crop")
    centered_img = Image.open(io.BytesIO(centered))
    gray_center = centered_img.getpixel((50, 50))
    assert gray_center[0] < 200  # gray, not red

    buffer.seek(0)
    focal = processor.process(
        buffer,
        width=100,
        height=100,
        fit="crop",
        focal_x=0.75,
        focal_y=0.5,
    )
    focal_img = Image.open(io.BytesIO(focal))
    red_center = focal_img.getpixel((50, 50))
    assert red_center[0] > 200


def test_api_responsive_snippet(client: TestClient) -> None:
    """The snippet endpoint returns copy-paste img/picture tags."""
    entry = src.main.manager.get_by_filename("test1.jpg")
    assert entry is not None

    resp = client.get(f"/api/snippet/{entry.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == entry.id
    assert "img" in data
    assert "picture" in data
    assert "srcset" in data
    assert f"{entry.id}/320" in data["srcset"]
    assert "loading=\"lazy\"" in data["img"]
    assert "<picture>" in data["picture"]


def test_api_responsive_snippet_errors(client: TestClient) -> None:
    """Snippet endpoint returns 404 for missing images and 400 for invalid widths."""
    entry = src.main.manager.get_by_filename("test1.jpg")
    assert entry is not None

    assert client.get("/api/snippet/999999").status_code == 404
    assert client.get(f"/api/snippet/{entry.id}?widths=abc").status_code == 400
    assert client.get(f"/api/snippet/{entry.id}?widths=").status_code == 400
    assert client.get(f"/api/snippet/{entry.id}?widths=320").status_code == 200


def test_api_srcset(client: TestClient) -> None:
    """Srcset endpoint returns responsive image URLs and validates input."""
    entry = src.main.manager.get_by_filename("test1.jpg")
    assert entry is not None

    resp = client.get(f"/api/srcset/{entry.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == entry.id
    assert "srcset" in data
    assert "srcset_string" in data
    assert f"{entry.id}/320" in data["srcset_string"]

    resp_webp = client.get(f"/api/srcset/{entry.id}?format=webp")
    assert resp_webp.status_code == 200
    assert ".webp" in resp_webp.json()["srcset_string"]

    assert client.get("/api/srcset/999999").status_code == 404
    assert client.get(f"/api/srcset/{entry.id}?sizes=abc").status_code == 400
    assert client.get(f"/api/srcset/{entry.id}?sizes=").status_code == 400


def test_focal_query_parameter(client: TestClient) -> None:
    """The focal query parameter is accepted without errors."""
    entry = src.main.manager.get_by_filename("test1.jpg")
    assert entry is not None

    resp_center = client.get(f"/id/{entry.id}/100/100?fit=crop")
    resp_focal = client.get(f"/id/{entry.id}/100/100?fit=crop&focal=0.2,0.8")
    assert resp_center.status_code == 200
    assert resp_focal.status_code == 200

    # Invalid focal string is logged and ignored
    assert client.get(f"/id/{entry.id}/100/100?fit=crop&focal=bad").status_code == 200


def test_base64_size_limit(client: TestClient) -> None:
    """Base64 responses are rejected when they exceed the configured limit."""
    entry = src.main.manager.get_by_filename("test1.jpg")
    assert entry is not None

    resp = client.get(f"/id/{entry.id}/300/300?base64=1")
    assert resp.status_code == 400
    assert "base64 images limited" in resp.json()["detail"]


def test_get_focal(monkeypatch: pytest.MonkeyPatch) -> None:
    """ImageManager.get_focal caches and handles missing entries."""
    entry = src.main.manager.get_by_filename("test1.jpg")
    assert entry is not None

    # Prime cache with a deterministic value
    src.main.manager._focal_points.pop(entry.id, None)
    monkeypatch.setattr(ImageManager, "_detect_focal_point", lambda _self, _path: (0.25, 0.75))
    first = src.main.manager.get_focal(entry.id)
    assert first == (0.25, 0.75)

    # Cache hit: change detector and verify result is still the cached value
    monkeypatch.setattr(ImageManager, "_detect_focal_point", lambda _self, _path: (0.99, 0.99))
    second = src.main.manager.get_focal(entry.id)
    assert second == (0.25, 0.75)

    # Missing image entry
    assert src.main.manager.get_focal(999999) == (0.5, 0.5)

    # Entry with a missing path
    monkeypatch.setattr(
        ImageManager,
        "get_by_id",
        lambda _self, _id: _entry(9000, Path("/no/such/file.jpg")),
    )
    assert src.main.manager.get_focal(9000) == (0.5, 0.5)

    monkeypatch.undo()


def test_get_dimensions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """ImageManager.get_dimensions caches and handles missing or broken images."""
    entry = src.main.manager.get_by_filename("test1.jpg")
    assert entry is not None

    # Cache hit
    src.main.manager._dimensions[entry.id] = (123, 456)
    assert src.main.manager.get_dimensions(entry.id) == (123, 456)
    src.main.manager._dimensions.pop(entry.id, None)

    # Read from file
    dims = src.main.manager.get_dimensions(entry.id)
    assert isinstance(dims, tuple)
    assert len(dims) == 2

    # Missing entry
    assert src.main.manager.get_dimensions(999999) is None

    # Broken image file (open raises)
    bad_path = tmp_path / "bad.jpg"
    bad_path.write_bytes(b"not an image")
    monkeypatch.setattr(ImageManager, "get_by_id", lambda _self, _id: _entry(9001, bad_path))
    assert src.main.manager.get_dimensions(9001) is None

    # Entry with no path
    monkeypatch.setattr(ImageManager, "get_by_id", lambda _self, _id: _entry(9002, None))
    assert src.main.manager.get_dimensions(9002) is None

    monkeypatch.undo()
