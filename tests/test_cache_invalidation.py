from __future__ import annotations

from pathlib import Path
import time

from src.image_manager import ImageEntry
from src.main import CacheCleaner, _cache_path

# ── Hash-Based Cache Key Tests ──────────────────────────────────────


class TestCacheHashDeterminism:
    @staticmethod
    def test_same_inputs_produce_same_key(test_images_dir, monkeypatch):
        """Identical params and image must yield the same cache path."""
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        path1 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        path2 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        assert path1 == path2

    @staticmethod
    def test_different_params_produce_different_keys(test_images_dir, monkeypatch):
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

    @staticmethod
    def test_border_changes_hash(test_images_dir, monkeypatch):
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", border="")
        with_border = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", border="5,ff0000")
        assert base != with_border

    @staticmethod
    def test_padding_changes_hash(test_images_dir, monkeypatch):
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", padding=0)
        with_padding = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", padding=10)
        assert base != with_padding

    @staticmethod
    def test_noise_changes_hash(test_images_dir, monkeypatch):
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", noise=0)
        with_noise = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", noise=10)
        assert base != with_noise

    @staticmethod
    def test_pixelate_changes_hash(test_images_dir, monkeypatch):
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", pixelate=0)
        with_pixelate = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", pixelate=5)
        assert base != with_pixelate

    @staticmethod
    def test_quality_changes_hash(test_images_dir, monkeypatch):
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", quality=85)
        with_quality = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", quality=50)
        assert base != with_quality

    @staticmethod
    def test_lqip_changes_hash(test_images_dir, monkeypatch):
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", lqip=False)
        with_lqip = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", lqip=True)
        assert base != with_lqip

    @staticmethod
    def test_watermark_changes_hash(test_images_dir, monkeypatch):
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        base = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop", watermark="")
        with_watermark = _cache_path(
            entry,
            500,
            500,
            "jpeg",
            False,
            0,
            "",
            "crop",
            watermark="true",
            watermark_config={
                "watermark_image": "",
                "watermark_text": "hello",
                "watermark_position": "bottom-right",
                "watermark_opacity": 0.5,
            },
        )
        assert base != with_watermark

    @staticmethod
    def test_source_mtime_changes_hash(test_images_dir, monkeypatch):
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

    @staticmethod
    def test_s3_key_in_hash_no_local_path(test_images_dir, monkeypatch):
        """S3 entries use s3_key in the hash instead of source_mtime."""
        from src.config import Settings

        monkeypatch.setattr("src.main.settings", Settings(dir=str(test_images_dir), cache=True))

        entry = ImageEntry(
            path=None, filename="remote.jpg", category="root", id=2, s3_key="photos/remote.jpg"
        )

        path1 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        path2 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        assert path1 == path2


# ── Cache Cleaner Tests ────────────────────────────────────────────


class TestCacheCleaner:
    @staticmethod
    def test_removes_old_files(tmp_path: Path):
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

    @staticmethod
    def test_keeps_all_files_when_ttl_zero(tmp_path: Path):
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

    @staticmethod
    def test_removes_empty_subdirs(tmp_path: Path):
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

    @staticmethod
    def test_logs_removed_count(tmp_path: Path, caplog):
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
            max_width=2400,
            max_height=2400,
            upload_enabled=True,
        )


class TestEndToEndCache:
    @staticmethod
    def test_cache_path_creates_flat_structure(test_images_dir, monkeypatch, tmp_path):
        """Test that cache path creates flat structure with 2-char prefix."""
        from src.image_manager import ImageEntry

        cache_dir = tmp_path / "test_cache"
        cache_dir.mkdir()
        test_settings = _TestSettings.make(test_images_dir, cache_dir)
        monkeypatch.setattr("src.config.settings", test_settings)
        monkeypatch.setattr("src.main.settings", test_settings)

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        cache_path = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")

        # Should be in flat structure: cache_dir/<first_2_hex>/<full_hash>.jpeg
        assert cache_path.parent.parent == cache_dir
        assert len(cache_path.parent.name) == 2
        assert cache_path.name.endswith(".jpeg")
        assert len(cache_path.stem) == 64  # SHA256 hex length

    @staticmethod
    def test_cache_path_is_deterministic(test_images_dir, monkeypatch, tmp_path):
        """Same inputs should produce same cache path."""
        from src.image_manager import ImageEntry

        cache_dir = tmp_path / "test_cache2"
        cache_dir.mkdir()
        test_settings = _TestSettings.make(test_images_dir, cache_dir)
        monkeypatch.setattr("src.config.settings", test_settings)
        monkeypatch.setattr("src.main.settings", test_settings)

        img_path = test_images_dir / "test1.jpg"
        entry = ImageEntry(path=img_path, filename="test1.jpg", category="root", id=1)

        path1 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")
        path2 = _cache_path(entry, 500, 500, "jpeg", False, 0, "", "crop")

        assert path1 == path2
        assert path1.name == path2.name
        assert path1.parent == path2.parent
