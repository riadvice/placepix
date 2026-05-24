from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.image_manager import ImageEntry
from src.main import _cache_path, CacheCleaner


# ── Hash-Based Cache Key Tests ──────────────────────────────────────

class TestCacheHashDeterminism:
    def test_same_inputs_produce_same_key(self, test_images_dir, monkeypatch):
        """Identical params and image must yield the same cache path."""
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        path1 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        path2 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        assert path1 == path2

    def test_different_params_produce_different_keys(self, test_images_dir, monkeypatch):
        """Changing any param must produce a different cache path."""
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        assert _cache_path(entry, 501, 500, "jpeg", False, 0, "", "crop") != base
        assert _cache_path(entry, 500, 500, "png", False, 0, "", "crop") != base
        assert _cache_path(entry, 500, 500, "jpeg", True, 0, "", "crop") != base
        assert _cache_path(entry, 500, 500, "jpeg", False, 2, "", "crop") != base
        assert _cache_path(entry, 500, 500, "jpeg", False, 0, "hello", "crop") != base
        assert _cache_path(entry, 500, 500, "jpeg", False, 0, "", "scale") != base

    def test_border_changes_hash(self, test_images_dir, monkeypatch):
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", border="")
        with_border = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", border="5,ff0000")
        assert base != with_border

    def test_padding_changes_hash(self, test_images_dir, monkeypatch):
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", padding=0)
        with_padding = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", padding=10)
        assert base != with_padding

    def test_noise_changes_hash(self, test_images_dir, monkeypatch):
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", noise=0)
        with_noise = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", noise=10)
        assert base != with_noise

    def test_pixelate_changes_hash(self, test_images_dir, monkeypatch):
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", pixelate=0)
        with_pixelate = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", pixelate=5)
        assert base != with_pixelate

    def test_quality_changes_hash(self, test_images_dir, monkeypatch):
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", quality=85)
        with_quality = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", quality=50)
        assert base != with_quality

    def test_lqip_changes_hash(self, test_images_dir, monkeypatch):
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", lqip=False)
        with_lqip = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", lqip=True)
        assert base != with_lqip

    def test_watermark_changes_hash(self, test_images_dir, monkeypatch):
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", watermark="")
        with_watermark = _cache_path(
            entry, 500, 500, "jpeg", False, 0, "", "crop", watermark="true",
            watermark_config={
                "watermark_image": "",
                "watermark_text": "hello",
                "watermark_position": "bottom-right",
                "watermark_opacity": 0.5,
            },
        )
        assert base != with_watermark

    def test_source_mtime_changes_hash(self, test_images_dir, monkeypatch):
        """Changing the source image mtime must invalidate the cache key."""
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        path1 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")

        # Touch the file to change mtime
        time.sleep(0.1)
        img_path.touch()

        path2 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        assert path1 != path2

    def test_s3_key_in_hash_no_local_path(self, test_images_dir, monkeypatch):
        """S3 entries use s3_key in the hash instead of source_mtime."""
        from src.config import Settings
        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        entry = ImageEntry(path=None, filename="remote.jpg", category="root", id=2, s3_key="photos/remote.jpg")

        path1 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        path2 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        assert path1 == path2


# ── Cache Cleaner Tests ────────────────────────────────────────────

class TestCacheCleaner:
    def test_removes_old_files(self, tmp_path: Path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        sub = cache_dir / "ab"
        sub.mkdir()

        old_file = sub / "oldfile.jpeg"
        old_file.write_bytes(b"old")
        new_file = sub / "newfile.jpeg"
        new_file.write_bytes(b"new")

        # Manually set mtimes
        now = time.time()
        os = __import__("os")
        os.utime(str(old_file), (now - 7200, now - 7200))  # 2 hours old
        os.utime(str(new_file), (now - 1800, now - 1800))  # 30 min old

        cleaner = CacheCleaner(cache_dir, ttl_hours=1)
        cleaner.run()

        assert not old_file.exists()
        assert new_file.exists()

    def test_keeps_all_files_when_ttl_zero(self, tmp_path: Path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        sub = cache_dir / "ab"
        sub.mkdir()

        old_file = sub / "oldfile.jpeg"
        old_file.write_bytes(b"old")

        os = __import__("os")
        now = time.time()
        os.utime(str(old_file), (now - 7200, now - 7200))

        cleaner = CacheCleaner(cache_dir, ttl_hours=0)
        cleaner.run()

        assert old_file.exists()

    def test_removes_empty_subdirs(self, tmp_path: Path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        sub = cache_dir / "ab"
        sub.mkdir()

        old_file = sub / "oldfile.jpeg"
        old_file.write_bytes(b"old")

        os = __import__("os")
        now = time.time()
        os.utime(str(old_file), (now - 7200, now - 7200))

        cleaner = CacheCleaner(cache_dir, ttl_hours=1)
        cleaner.run()

        assert not sub.exists()

    def test_logs_removed_count(self, tmp_path: Path, caplog):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        sub = cache_dir / "ab"
        sub.mkdir()

        old_file = sub / "oldfile.jpeg"
        old_file.write_bytes(b"old data here")

        os = __import__("os")
        now = time.time()
        os.utime(str(old_file), (now - 7200, now - 7200))

        import logging
        with caplog.at_level(logging.INFO, logger="src.main"):
            cleaner = CacheCleaner(cache_dir, ttl_hours=1)
            cleaner.run()

        assert "removed 1 stale files" in caplog.text


# ── End-to-End Cache Tests ────────────────────────────────────────

class _TestSettings:
    """Helper to build a settings object with a custom cache_dir."""

    @staticmethod
    def make(images_dir: Path, cache_dir: Path) -> "Settings":
        from src.config import Settings

        class OverrideSettings(Settings):
            @property
            def cache_dir(self) -> Path:
                return cache_dir

        return OverrideSettings(
            host="127.0.0.1:3000",
            dir=str(images_dir),
            cache=True,
            cdn="",
            min_width=8,
            min_height=8,
            max_width=2000,
            max_height=2000,
            upload_enabled=True,
            admin_password="",
        )


class TestEndToEndCache:
    def test_request_creates_cache_file(self, client: TestClient, test_images_dir, monkeypatch, tmp_path):
        """A processed image request should create a file in the flat cache."""
        from src.main import manager
        entry = manager.pick()
        assert entry is not None

        cache_dir = tmp_path / "e2e_cache"
        cache_dir.mkdir()
        test_settings = _TestSettings.make(test_images_dir, cache_dir)
        monkeypatch.setattr("src.config.settings", test_settings)
        monkeypatch.setattr("src.main.settings", test_settings)

        response = client.get(f"/id/{entry.id}/200/200")
        assert response.status_code == 200

        subdirs = [d for d in cache_dir.iterdir() if d.is_dir()]
        assert len(subdirs) >= 1
        assert any(f.is_file() for sub in subdirs for f in sub.iterdir())

    def test_cached_response_served_on_second_request(self, client: TestClient, test_images_dir, monkeypatch, tmp_path):
        """Two identical requests should hit the same cache file."""
        from src.main import manager
        entry = manager.pick()
        assert entry is not None

        cache_dir = tmp_path / "e2e_cache2"
        cache_dir.mkdir()
        test_settings = _TestSettings.make(test_images_dir, cache_dir)
        monkeypatch.setattr("src.config.settings", test_settings)
        monkeypatch.setattr("src.main.settings", test_settings)

        response1 = client.get(f"/id/{entry.id}/200/200")
        assert response1.status_code == 200

        subdirs1 = [d for d in cache_dir.iterdir() if d.is_dir()]
        files1 = [f for sub in subdirs1 for f in sub.iterdir() if f.is_file()]

        response2 = client.get(f"/id/{entry.id}/200/200")
        assert response2.status_code == 200

        subdirs2 = [d for d in cache_dir.iterdir() if d.is_dir()]
        files2 = [f for sub in subdirs2 for f in sub.iterdir() if f.is_file()]

        assert len(files1) == len(files2)
