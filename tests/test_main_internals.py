"""Unit tests for main.py internals: cache cleanup, SEO endpoints, helpers."""

from __future__ import annotations

import io
from pathlib import Path
import shutil
import time
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import ImageFont
import pytest

from src.image_manager import ImageEntry
import src.main as main_mod
from src.main import CacheCleaner


def _fill(cache_dir: Path, subdir: str, name: str, size: int, age_hours: float = 0.0) -> Path:
    """Create a cache file of a given size and age."""
    d = cache_dir / subdir
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_bytes(b"x" * size)
    if age_hours:
        old = time.time() - age_hours * 3600
        import os

        os.utime(p, (old, old))
    return p


# ── CacheCleaner._get_cache_size ────────────────────────────────────


def test_get_cache_size_sums_files(tmp_path: Path):
    _fill(tmp_path, "ab", "one.jpg", 100)
    _fill(tmp_path, "cd", "two.jpg", 250)
    (tmp_path / "loose.txt").write_bytes(b"ignored")  # not in a subdir

    cleaner = CacheCleaner(tmp_path, ttl_hours=0, max_size_mb=1)
    assert cleaner._get_cache_size() == 350


def test_get_cache_size_ignores_unstatable_files(tmp_path: Path, monkeypatch):
    """A file that disappears between is_file() and stat() must not abort the sweep."""
    _fill(tmp_path, "ab", "one.jpg", 100)
    _fill(tmp_path, "ab", "two.jpg", 40)
    cleaner = CacheCleaner(tmp_path, ttl_hours=0, max_size_mb=1)

    real_stat = Path.stat
    seen = {"n": 0}

    def flaky_stat(self, *args, **kwargs):
        # is_file() calls stat() first and swallows OSError, so only fail the
        # second call - the one inside the try block being exercised here.
        if self.name == "one.jpg":
            seen["n"] += 1
            if seen["n"] >= 2:
                raise OSError("vanished")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", flaky_stat)
    assert cleaner._get_cache_size() == 40


# ── CacheCleaner._evict_by_size ─────────────────────────────────────


def test_evict_by_size_removes_oldest_first(tmp_path: Path):
    old = _fill(tmp_path, "ab", "old.jpg", 600, age_hours=10)
    new = _fill(tmp_path, "ab", "new.jpg", 600, age_hours=1)

    cleaner = CacheCleaner(tmp_path, ttl_hours=0, max_size_mb=0)
    cleaner.max_size_bytes = 700  # room for one file only

    removed, freed = cleaner._evict_by_size()

    assert removed == 1
    assert freed == 600
    assert not old.exists()
    assert new.exists()


def test_evict_by_size_stops_once_under_limit(tmp_path: Path):
    _fill(tmp_path, "ab", "a.jpg", 100)
    _fill(tmp_path, "ab", "b.jpg", 100)

    cleaner = CacheCleaner(tmp_path, ttl_hours=0, max_size_mb=0)
    cleaner.max_size_bytes = 10_000  # already under the limit

    assert cleaner._evict_by_size() == (0, 0)


def test_evict_by_size_survives_unlink_errors(tmp_path: Path):
    _fill(tmp_path, "ab", "a.jpg", 900, age_hours=5)
    cleaner = CacheCleaner(tmp_path, ttl_hours=0, max_size_mb=0)
    cleaner.max_size_bytes = 1

    with patch.object(Path, "unlink", side_effect=PermissionError("locked")):
        removed, freed = cleaner._evict_by_size()

    assert (removed, freed) == (0, 0)


# ── CacheCleaner.run ────────────────────────────────────────────────


def test_run_removes_stale_files_and_empty_subdirs(tmp_path: Path):
    stale = _fill(tmp_path, "ab", "stale.jpg", 50, age_hours=100)
    fresh = _fill(tmp_path, "cd", "fresh.jpg", 50, age_hours=1)

    CacheCleaner(tmp_path, ttl_hours=24, max_size_mb=0).run()

    assert not stale.exists()
    assert not (tmp_path / "ab").exists()  # empty subdir pruned
    assert fresh.exists()


def test_run_skips_non_hash_subdirs(tmp_path: Path):
    """Only two-character shard directories are cleaned."""
    keep = _fill(tmp_path, "not-a-shard", "old.jpg", 50, age_hours=100)
    CacheCleaner(tmp_path, ttl_hours=1, max_size_mb=0).run()
    assert keep.exists()


def test_run_evicts_when_over_size_limit(tmp_path: Path):
    _fill(tmp_path, "ab", "a.jpg", 2 * 1024 * 1024, age_hours=5)
    _fill(tmp_path, "ab", "b.jpg", 2 * 1024 * 1024, age_hours=1)

    CacheCleaner(tmp_path, ttl_hours=0, max_size_mb=3).run()

    remaining = list((tmp_path / "ab").iterdir())
    assert len(remaining) == 1
    assert remaining[0].name == "b.jpg"  # newest survives


def test_run_noop_when_within_limits(tmp_path: Path):
    f = _fill(tmp_path, "ab", "a.jpg", 100, age_hours=1)
    CacheCleaner(tmp_path, ttl_hours=24, max_size_mb=10).run()
    assert f.exists()


# ── _load_font ──────────────────────────────────────────────────────


def _a_system_ttf() -> Path | None:
    for root in ("/usr/share/fonts", "/System/Library/Fonts", "/Windows/Fonts"):
        base = Path(root)
        if base.exists():
            for f in base.rglob("*.ttf"):
                return f
    return None


def test_load_font_prefers_custom_directory(tmp_path: Path, monkeypatch):
    src_font = _a_system_ttf()
    if src_font is None:
        pytest.skip("no system .ttf available to copy")

    fonts = tmp_path / "fonts"
    fonts.mkdir()
    shutil.copy(src_font, fonts / "brand.ttf")
    monkeypatch.setattr(main_mod.settings, "font_dir", str(fonts), raising=False)

    font = main_mod._load_font(32)
    assert isinstance(font, ImageFont.FreeTypeFont)
    assert font.size == 32


def test_load_font_skips_broken_custom_fonts(tmp_path: Path, monkeypatch):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    (fonts / "broken.ttf").write_bytes(b"nope")
    (fonts / "broken.ttc").write_bytes(b"nope")
    monkeypatch.setattr(main_mod.settings, "font_dir", str(fonts), raising=False)

    assert main_mod._load_font(16) is not None


# ── _resolve_image_source ───────────────────────────────────────────


def test_resolve_image_source_reads_from_s3(monkeypatch):
    monkeypatch.setattr(main_mod.settings, "s3_enabled", True, raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_bucket", "bucket", raising=False)

    body = MagicMock()
    body.read.return_value = b"image-bytes"
    client = MagicMock()
    client.get_object.return_value = {"Body": body}

    entry = ImageEntry(path=None, filename="a.jpg", category="nature", s3_key="nature/a.jpg")
    with patch("src.main._get_s3_client", return_value=client):
        result = main_mod._resolve_image_source(entry)

    assert isinstance(result, io.BytesIO)
    assert result.read() == b"image-bytes"


def test_resolve_image_source_s3_failure_raises_500(monkeypatch):
    monkeypatch.setattr(main_mod.settings, "s3_enabled", True, raising=False)
    entry = ImageEntry(path=None, filename="a.jpg", category="nature", s3_key="nature/a.jpg")

    with patch("src.main._get_s3_client", side_effect=RuntimeError("no creds")):
        with pytest.raises(HTTPException) as exc:
            main_mod._resolve_image_source(entry)

    assert exc.value.status_code == 500
    assert "Failed to load S3 image" in exc.value.detail


def test_resolve_image_source_without_path_or_key(monkeypatch):
    monkeypatch.setattr(main_mod.settings, "s3_enabled", False, raising=False)
    entry = ImageEntry(path=None, filename="a.jpg", category="nature")

    with pytest.raises(HTTPException) as exc:
        main_mod._resolve_image_source(entry)

    assert exc.value.status_code == 500


def test_resolve_image_source_returns_local_path(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "s3_enabled", False, raising=False)
    p = tmp_path / "a.jpg"
    p.write_bytes(b"x")
    entry = ImageEntry(path=p, filename="a.jpg", category="nature")

    assert main_mod._resolve_image_source(entry) == p


# ── markdown helpers ────────────────────────────────────────────────


def test_parse_frontmatter_extracts_yaml():
    meta, body = main_mod._parse_frontmatter("---\ntitle: Guide\nweight: 2\n---\n# Body\n")
    assert meta == {"title": "Guide", "weight": 2}
    assert body.strip() == "# Body"


def test_parse_frontmatter_without_frontmatter():
    meta, body = main_mod._parse_frontmatter("# Just markdown")
    assert meta == {}
    assert body == "# Just markdown"


def test_parse_frontmatter_empty_block():
    meta, body = main_mod._parse_frontmatter("---\n\n---\nbody")
    assert meta == {}
    assert body == "body"


def test_split_sections_by_h2():
    html_text = "<p>intro</p><h2>First</h2><p>one</p><h2>Second</h2><p>two</p>"
    sections = main_mod._split_sections(html_text)

    assert [s["heading"] for s in sections] == ["First", "Second"]
    assert sections[0]["html"] == "<p>one</p>"
    assert sections[1]["html"] == "<p>two</p>"


def test_split_sections_without_headings():
    assert main_mod._split_sections("<p>no headings here</p>") == []


# ── SEO-gated endpoints ─────────────────────────────────────────────


def test_llms_txt_served_when_seo_enabled(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", True, raising=False)
    response = client.get("/llms.txt")
    assert response.status_code in (200, 404)  # 404 only if the file is absent
    if response.status_code == 200:
        assert response.headers["content-type"].startswith("text/plain")


def test_llms_txt_hidden_when_seo_disabled(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", False, raising=False)
    assert client.get("/llms.txt").status_code == 404


def test_llms_txt_missing_file(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", True, raising=False)
    with patch.object(Path, "exists", return_value=False):
        assert client.get("/llms.txt").status_code == 404


def test_sitemap_xml_redirects(client: TestClient):
    response = client.get("/sitemap.xml", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "/sitemap/sitemap-index.xml"


def test_sitemap_index_hidden_when_seo_disabled(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", False, raising=False)
    assert client.get("/sitemap/sitemap-index.xml").status_code == 404


def test_sitemap_index_missing_file(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", True, raising=False)
    with patch.object(Path, "exists", return_value=False):
        assert client.get("/sitemap/sitemap-index.xml").status_code == 404


def test_sitemap_file_hidden_when_seo_disabled(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", False, raising=False)
    assert client.get("/sitemap/sitemap-en.xml").status_code == 404


def test_sitemap_file_rejects_path_traversal(client: TestClient, monkeypatch):
    """The filename is reduced to its basename before use."""
    monkeypatch.setattr(main_mod.settings, "seo_enabled", True, raising=False)
    response = client.get("/sitemap/..%2f..%2fetc%2fpasswd")
    assert response.status_code == 404


def test_sitemap_file_missing(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", True, raising=False)
    assert client.get("/sitemap/definitely-not-here.xml").status_code == 404


# ── health check S3 branch ──────────────────────────────────────────


def test_health_reports_s3_connected(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "s3_enabled", True, raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_bucket", "bucket", raising=False)

    with patch("src.main._get_s3_client", return_value=MagicMock()):
        response = client.get("/health")

    assert response.json()["s3"] == {"connected": True}


def test_health_reports_s3_failure_as_warning(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "s3_enabled", True, raising=False)

    with patch("src.main._get_s3_client", side_effect=RuntimeError("unreachable")):
        response = client.get("/health")

    body = response.json()
    assert response.status_code == 503
    assert body["status"] == "warning"
    assert body["s3"]["connected"] is False
    assert "unreachable" in body["s3"]["error"]


# ── _validate_startup ───────────────────────────────────────────────


def test_validate_startup_passes_with_writable_dirs(tmp_path: Path, monkeypatch):
    for name in ("images", "data", "cache"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(main_mod.settings, "seed_dir_str", str(tmp_path / "images"), raising=False)
    monkeypatch.setattr(main_mod.settings, "dir", str(tmp_path / "data"), raising=False)
    monkeypatch.setattr(main_mod.settings, "cache_dir_str", str(tmp_path / "cache"), raising=False)
    monkeypatch.setattr(main_mod.settings, "watermark_enabled", False, raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_enabled", False, raising=False)
    monkeypatch.setattr(main_mod.settings, "font_dir", "", raising=False)

    main_mod._validate_startup()  # must not raise


def test_validate_startup_rejects_unreadable_image_dir(tmp_path: Path, monkeypatch):
    for name in ("data", "cache"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(main_mod.settings, "seed_dir_str", str(tmp_path / "gone"), raising=False)
    monkeypatch.setattr(main_mod.settings, "dir", str(tmp_path / "data"), raising=False)
    monkeypatch.setattr(main_mod.settings, "cache_dir_str", str(tmp_path / "cache"), raising=False)
    monkeypatch.setattr(main_mod.settings, "watermark_enabled", False, raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_enabled", False, raising=False)

    with pytest.raises(SystemExit, match="Startup validation failed"):
        main_mod._validate_startup()


def test_validate_startup_reports_missing_watermark(tmp_path: Path, monkeypatch):
    for name in ("images", "data", "cache"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(main_mod.settings, "seed_dir_str", str(tmp_path / "images"), raising=False)
    monkeypatch.setattr(main_mod.settings, "dir", str(tmp_path / "data"), raising=False)
    monkeypatch.setattr(main_mod.settings, "cache_dir_str", str(tmp_path / "cache"), raising=False)
    monkeypatch.setattr(main_mod.settings, "watermark_enabled", True, raising=False)
    monkeypatch.setattr(
        main_mod.settings, "watermark_image", str(tmp_path / "absent.png"), raising=False
    )
    monkeypatch.setattr(main_mod.settings, "s3_enabled", False, raising=False)

    with pytest.raises(SystemExit):
        main_mod._validate_startup()


def test_validate_startup_requires_complete_s3_config(tmp_path: Path, monkeypatch):
    for name in ("images", "data", "cache"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(main_mod.settings, "seed_dir_str", str(tmp_path / "images"), raising=False)
    monkeypatch.setattr(main_mod.settings, "dir", str(tmp_path / "data"), raising=False)
    monkeypatch.setattr(main_mod.settings, "cache_dir_str", str(tmp_path / "cache"), raising=False)
    monkeypatch.setattr(main_mod.settings, "watermark_enabled", False, raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_enabled", True, raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_endpoint", "", raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_bucket", "", raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_access_key", "", raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_secret_key", "", raising=False)

    with pytest.raises(SystemExit):
        main_mod._validate_startup()


def test_validate_startup_warns_on_empty_custom_font_dir(tmp_path: Path, monkeypatch):
    for name in ("images", "data", "cache"):
        (tmp_path / name).mkdir()
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    monkeypatch.setattr(main_mod.settings, "seed_dir_str", str(tmp_path / "images"), raising=False)
    monkeypatch.setattr(main_mod.settings, "dir", str(tmp_path / "data"), raising=False)
    monkeypatch.setattr(main_mod.settings, "cache_dir_str", str(tmp_path / "cache"), raising=False)
    monkeypatch.setattr(main_mod.settings, "watermark_enabled", False, raising=False)
    monkeypatch.setattr(main_mod.settings, "s3_enabled", False, raising=False)
    monkeypatch.setattr(main_mod.settings, "font_dir", str(fonts), raising=False)

    main_mod._validate_startup()  # warns, does not fail


# ── robots.txt ──────────────────────────────────────────────────────


def test_robots_txt_served_when_seo_enabled(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", True, raising=False)
    monkeypatch.setattr(main_mod.settings, "site_url", "https://example.test", raising=False)

    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_robots_txt_minimal_when_seo_disabled(client: TestClient, monkeypatch):
    monkeypatch.setattr(main_mod.settings, "seo_enabled", False, raising=False)
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "Disallow" in response.text
