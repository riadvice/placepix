"""Unit tests for ImageManager background scans, focal points and leader locking."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image
import pytest

from src.config import Settings
import src.image_manager as im
from src.image_manager import Category, CategoryMeta, ImageEntry, ImageManager


def _jpeg_bytes(color: tuple[int, int, int] = (200, 30, 40)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), color).save(buf, "JPEG")
    return buf.getvalue()


@pytest.fixture
def manager_env(tmp_path: Path, monkeypatch):
    """A bare ImageManager wired to temp dirs, with no filesystem scan performed."""
    images = tmp_path / "images"
    data = tmp_path / "data"
    (images / "nature").mkdir(parents=True)
    data.mkdir()

    settings = Settings(
        host="127.0.0.1:3000",
        dir=str(data),
        seed_dir_str=str(images),
        cache=False,
        s3_enabled=False,
    )
    monkeypatch.setattr("src.config.settings", settings)
    monkeypatch.setattr(im, "settings", settings)

    mgr = ImageManager.__new__(ImageManager)
    mgr._categories = {}
    mgr._total = 0
    mgr._colors = {}
    mgr._dimensions = {}
    mgr._focal_points = {}
    mgr._scanning_colors = False
    mgr._scanning_dimensions = False
    mgr._is_leader = True
    return mgr, images, settings


def _add_local_image(mgr: ImageManager, images: Path, entry_id: int = 1) -> Path:
    path = images / "nature" / f"img{entry_id}.jpg"
    path.write_bytes(_jpeg_bytes())
    mgr._categories["nature"] = Category(
        name="nature",
        meta=CategoryMeta(),
        entries=[
            ImageEntry(path=path, filename=path.name, category="nature", id=entry_id),
        ],
    )
    mgr._total = 1
    return path


def _add_s3_image(mgr: ImageManager, entry_id: int = 2) -> None:
    mgr._categories["nature"] = Category(
        name="nature",
        meta=CategoryMeta(),
        entries=[
            ImageEntry(
                path=None,
                filename="remote.jpg",
                category="nature",
                id=entry_id,
                s3_key="nature/remote.jpg",
            ),
        ],
    )
    mgr._total = 1


# ── scan_colors ─────────────────────────────────────────────────────


def test_scan_colors_extracts_local_colors(manager_env):
    mgr, images, _ = manager_env
    _add_local_image(mgr, images)

    mgr.scan_colors()

    assert 1 in mgr._colors
    assert all(c.startswith("#") for c in mgr._colors[1])


def test_scan_colors_is_reentrant_guarded(manager_env):
    mgr, images, _ = manager_env
    _add_local_image(mgr, images)
    mgr._scanning_colors = True

    mgr.scan_colors()

    assert mgr._colors == {}  # returned immediately


def test_scan_colors_skips_when_nothing_missing(manager_env):
    mgr, images, _ = manager_env
    _add_local_image(mgr, images)
    with patch.object(ImageManager, "_load_colors", return_value={1: ["#ffffff"]}):
        mgr.scan_colors()

    assert mgr._colors == {1: ["#ffffff"]}


def test_scan_colors_reads_s3_objects(manager_env, monkeypatch):
    mgr, _, settings = manager_env
    monkeypatch.setattr(settings, "s3_enabled", True, raising=False)
    _add_s3_image(mgr)

    body = MagicMock()
    body.read.return_value = _jpeg_bytes((10, 200, 10))
    client = MagicMock()
    client.get_object.return_value = {"Body": body}

    with patch.object(im.boto3, "client", return_value=client):
        mgr.scan_colors()

    assert 2 in mgr._colors


def test_scan_colors_survives_s3_read_failure(manager_env, monkeypatch):
    mgr, _, settings = manager_env
    monkeypatch.setattr(settings, "s3_enabled", True, raising=False)
    _add_s3_image(mgr)

    client = MagicMock()
    client.get_object.side_effect = RuntimeError("access denied")

    with patch.object(im.boto3, "client", return_value=client):
        mgr.scan_colors()  # must not raise

    assert mgr._scanning_colors is False


def test_scan_colors_survives_s3_client_failure(manager_env, monkeypatch):
    mgr, _, settings = manager_env
    monkeypatch.setattr(settings, "s3_enabled", True, raising=False)
    _add_s3_image(mgr)

    with patch.object(im.boto3, "client", side_effect=RuntimeError("bad credentials")):
        mgr.scan_colors()  # must not raise

    assert mgr._scanning_colors is False


# ── scan_dimensions ─────────────────────────────────────────────────


def test_scan_dimensions_reads_local_files(manager_env):
    mgr, images, _ = manager_env
    _add_local_image(mgr, images)

    mgr.scan_dimensions()

    assert mgr._dimensions[1] == (40, 30)


def test_scan_dimensions_is_reentrant_guarded(manager_env):
    mgr, images, _ = manager_env
    _add_local_image(mgr, images)
    mgr._scanning_dimensions = True

    mgr.scan_dimensions()

    assert mgr._dimensions == {}


def test_scan_dimensions_skips_when_nothing_missing(manager_env):
    mgr, images, _ = manager_env
    _add_local_image(mgr, images)
    mgr._dimensions = {1: (10, 10)}

    mgr.scan_dimensions()

    assert mgr._dimensions == {1: (10, 10)}


def test_scan_dimensions_handles_unreadable_file(manager_env):
    mgr, images, _ = manager_env
    path = _add_local_image(mgr, images)
    path.write_bytes(b"not an image")

    mgr.scan_dimensions()

    assert 1 not in mgr._dimensions
    assert mgr._scanning_dimensions is False


def test_scan_dimensions_reads_s3_objects(manager_env, monkeypatch):
    mgr, _, settings = manager_env
    monkeypatch.setattr(settings, "s3_enabled", True, raising=False)
    _add_s3_image(mgr)

    body = MagicMock()
    body.read.return_value = _jpeg_bytes()
    client = MagicMock()
    client.get_object.return_value = {"Body": body}

    with patch.object(im.boto3, "client", return_value=client):
        mgr.scan_dimensions()

    assert mgr._dimensions[2] == (40, 30)


def test_scan_dimensions_survives_s3_read_failure(manager_env, monkeypatch):
    mgr, _, settings = manager_env
    monkeypatch.setattr(settings, "s3_enabled", True, raising=False)
    _add_s3_image(mgr)

    client = MagicMock()
    client.get_object.side_effect = RuntimeError("timeout")

    with patch.object(im.boto3, "client", return_value=client):
        mgr.scan_dimensions()

    assert 2 not in mgr._dimensions


def test_scan_dimensions_survives_s3_client_failure(manager_env, monkeypatch):
    mgr, _, settings = manager_env
    monkeypatch.setattr(settings, "s3_enabled", True, raising=False)
    _add_s3_image(mgr)

    with patch.object(im.boto3, "client", side_effect=RuntimeError("no region")):
        mgr.scan_dimensions()

    assert 2 not in mgr._dimensions


def test_scan_dimensions_logs_progress_for_many_images(manager_env):
    """More than ten images exercises the periodic save and progress branches."""
    mgr, images, _ = manager_env
    entries = []
    for i in range(1, 13):
        p = images / "nature" / f"img{i}.jpg"
        p.write_bytes(_jpeg_bytes())
        entries.append(ImageEntry(path=p, filename=p.name, category="nature", id=i))
    mgr._categories["nature"] = Category(name="nature", meta=CategoryMeta(), entries=entries)

    mgr.scan_dimensions()

    assert len(mgr._dimensions) == 12


# ── _detect_focal_point ─────────────────────────────────────────────


def test_detect_focal_point_defaults_for_unreadable_file(tmp_path: Path):
    bad = tmp_path / "broken.jpg"
    bad.write_bytes(b"not an image")
    assert ImageManager._detect_focal_point(bad) == (0.5, 0.5)


def test_detect_focal_point_returns_normalised_coordinates(tmp_path: Path):
    p = tmp_path / "plain.jpg"
    Image.new("RGB", (120, 90), (120, 120, 120)).save(p)

    fx, fy = ImageManager._detect_focal_point(p)

    assert 0.0 <= fx <= 1.0
    assert 0.0 <= fy <= 1.0


def test_detect_focal_point_uses_face_bounding_box(tmp_path: Path, monkeypatch):
    """Face detection wins over saliency when a face is found.

    This build of OpenCV ships no haarcascade XML in cv2/data, so the cascade
    file has to be faked for the branch to run at all.
    """
    p = tmp_path / "face.jpg"
    Image.new("RGB", (200, 100), (10, 10, 10)).save(p)

    cascade_dir = tmp_path / "cascades"
    cascade_dir.mkdir()
    (cascade_dir / "haarcascade_frontalface_default.xml").write_text("<opencv_storage/>")
    monkeypatch.setattr(im.cv2.data, "haarcascades", str(cascade_dir) + "/", raising=False)

    cascade = MagicMock()
    cascade.detectMultiScale.return_value = [(80, 20, 40, 40)]

    with patch.object(im.cv2, "CascadeClassifier", return_value=cascade):
        fx, fy = ImageManager._detect_focal_point(p)

    assert fx == pytest.approx(0.5)  # (80 + 120) / 2 / 200
    assert fy == pytest.approx(0.4)  # (20 + 60) / 2 / 100


def test_detect_focal_point_handles_detector_errors(tmp_path: Path):
    p = tmp_path / "plain.jpg"
    Image.new("RGB", (60, 60), (5, 5, 5)).save(p)

    with patch.object(im.cv2, "CascadeClassifier", side_effect=RuntimeError("no cascade")):
        assert ImageManager._detect_focal_point(p) == pytest.approx((0.5, 0.5), abs=0.5)


# ── leader lock ─────────────────────────────────────────────────────


def test_leader_lock_acquire_and_release(manager_env):
    mgr, _, settings = manager_env

    assert mgr._acquire_leader_lock() is True
    assert (settings.data_dir / ".placepix_leader.lock").exists()

    mgr._release_leader_lock()  # must not raise


def test_leader_lock_release_without_lock_is_safe(manager_env):
    mgr, _, _ = manager_env
    mgr._leader_lock_file = None
    mgr._release_leader_lock()
