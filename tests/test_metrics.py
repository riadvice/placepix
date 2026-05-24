from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.config import Settings
from src.metrics import MetricsTracker


def test_metrics_tracker_initialization(tmp_path: Path):
    """Test metrics tracker initializes database."""
    db_path = tmp_path / "test_metrics.db"
    tracker = MetricsTracker(db_path)
    assert db_path.exists()


def test_log_request(tmp_path: Path):
    """Test logging a request."""
    tracker = MetricsTracker(tmp_path / "test.db")
    tracker.log_request(
        endpoint="/500/500",
        method="GET",
        status_code=200,
        response_time_ms=15.5,
        width=500,
        height=500,
        format="jpeg",
        cache_hit=False,
    )
    assert tracker.get_total_requests() == 1


def test_cache_hit_rate(tmp_path: Path):
    """Test cache hit rate calculation."""
    tracker = MetricsTracker(tmp_path / "test.db")
    
    # Log 3 requests, 2 cache hits
    tracker.log_request("/500/500", "GET", 200, 10.0, cache_hit=True)
    tracker.log_request("/500/500", "GET", 200, 10.0, cache_hit=True)
    tracker.log_request("/600/600", "GET", 200, 10.0, cache_hit=False)
    
    assert tracker.get_cache_hit_rate() == pytest.approx(66.67, rel=0.1)


def test_avg_response_time(tmp_path: Path):
    """Test average response time calculation."""
    tracker = MetricsTracker(tmp_path / "test.db")
    
    tracker.log_request("/500/500", "GET", 200, 10.0)
    tracker.log_request("/500/500", "GET", 200, 20.0)
    tracker.log_request("/500/500", "GET", 200, 30.0)
    
    assert tracker.get_avg_response_time() == 20.0


def test_popular_sizes(tmp_path: Path):
    """Test popular sizes tracking."""
    tracker = MetricsTracker(tmp_path / "test.db")
    
    tracker.log_request("/500/500", "GET", 200, 10.0, width=500, height=500)
    tracker.log_request("/500/500", "GET", 200, 10.0, width=500, height=500)
    tracker.log_request("/600/600", "GET", 200, 10.0, width=600, height=600)
    
    sizes = tracker.get_popular_sizes()
    assert len(sizes) == 2
    assert sizes[0]["width"] == 500
    assert sizes[0]["height"] == 500
    assert sizes[0]["count"] == 2


def test_popular_categories(tmp_path: Path):
    """Test popular categories tracking."""
    tracker = MetricsTracker(tmp_path / "test.db")
    
    tracker.log_request("/500/500/nature", "GET", 200, 10.0, category="nature")
    tracker.log_request("/500/500/nature", "GET", 200, 10.0, category="nature")
    tracker.log_request("/500/500/animals", "GET", 200, 10.0, category="animals")
    
    categories = tracker.get_popular_categories()
    assert len(categories) == 2
    assert categories[0]["category"] == "nature"
    assert categories[0]["count"] == 2


def test_popular_formats(tmp_path: Path):
    """Test popular formats tracking."""
    tracker = MetricsTracker(tmp_path / "test.db")
    
    tracker.log_request("/500/500.webp", "GET", 200, 10.0, format="webp")
    tracker.log_request("/500/500.webp", "GET", 200, 10.0, format="webp")
    tracker.log_request("/500/500.png", "GET", 200, 10.0, format="png")
    
    formats = tracker.get_popular_formats()
    assert len(formats) == 2
    assert formats[0]["format"] == "webp"
    assert formats[0]["count"] == 2


def test_stats_summary(tmp_path: Path):
    """Test comprehensive stats summary."""
    tracker = MetricsTracker(tmp_path / "test.db")
    
    tracker.log_request("/500/500", "GET", 200, 10.0, width=500, height=500, cache_hit=True)
    tracker.log_request("/600/600", "GET", 200, 20.0, width=600, height=600, cache_hit=False)
    
    stats = tracker.get_stats_summary()
    assert stats["total_requests"] == 2
    assert stats["cache_hit_rate"] == 50.0
    assert stats["avg_response_time_ms"] == 15.0
    assert len(stats["popular_sizes"]) == 2


def test_admin_disabled_without_password(client: TestClient):
    """Test admin endpoints return 404 when password not set."""
    response = client.get("/admin/stats", headers={"X-Admin-Password": "test"})
    assert response.status_code == 404


def test_admin_with_password(test_images_dir: Path, tmp_path: Path, monkeypatch):
    """Test admin endpoints with password protection."""
    from src.main import app
    from src.image_manager import ImageManager
    
    # Create settings with admin password
    test_settings = Settings(
        host="127.0.0.1:3000",
        dir=str(test_images_dir),
        cache=True,
        admin_password="test123",
    )
    monkeypatch.setattr("src.config.settings", test_settings)
    monkeypatch.setattr("src.main.settings", test_settings)
    
    # Reinitialize with metrics enabled
    from src.metrics import MetricsTracker
    tracker = MetricsTracker(tmp_path / "metrics.db")
    monkeypatch.setattr("src.main.metrics_tracker", tracker)
    
    manager = ImageManager()
    monkeypatch.setattr("src.main.manager", manager)
    
    client = TestClient(app)
    
    # Test without password
    response = client.get("/admin/stats")
    assert response.status_code == 422  # Missing header
    
    # Test with wrong password
    response = client.get("/admin/stats", headers={"X-Admin-Password": "wrong"})
    assert response.status_code == 403
    
    # Test with correct password
    response = client.get("/admin/stats", headers={"X-Admin-Password": "test123"})
    assert response.status_code == 200
    assert "PlacePix Admin" in response.text


def test_admin_api_stats(test_images_dir: Path, tmp_path: Path, monkeypatch):
    """Test admin API stats endpoint."""
    from src.main import app
    from src.image_manager import ImageManager
    
    test_settings = Settings(
        host="127.0.0.1:3000",
        dir=str(test_images_dir),
        admin_password="test123",
    )
    monkeypatch.setattr("src.config.settings", test_settings)
    monkeypatch.setattr("src.main.settings", test_settings)
    
    from src.metrics import MetricsTracker
    tracker = MetricsTracker(tmp_path / "metrics.db")
    tracker.log_request("/500/500", "GET", 200, 10.0)
    monkeypatch.setattr("src.main.metrics_tracker", tracker)
    
    manager = ImageManager()
    monkeypatch.setattr("src.main.manager", manager)
    
    client = TestClient(app)
    
    response = client.get("/api/admin/stats", headers={"X-Admin-Password": "test123"})
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert data["total_requests"] == 1


def test_admin_popular_sizes_endpoint(test_images_dir: Path, tmp_path: Path, monkeypatch):
    """Test admin popular sizes endpoint."""
    from src.main import app
    from src.image_manager import ImageManager
    
    test_settings = Settings(
        host="127.0.0.1:3000",
        dir=str(test_images_dir),
        admin_password="test123",
    )
    monkeypatch.setattr("src.config.settings", test_settings)
    monkeypatch.setattr("src.main.settings", test_settings)
    
    from src.metrics import MetricsTracker
    tracker = MetricsTracker(tmp_path / "metrics.db")
    tracker.log_request("/500/500", "GET", 200, 10.0, width=500, height=500)
    monkeypatch.setattr("src.main.metrics_tracker", tracker)
    
    manager = ImageManager()
    monkeypatch.setattr("src.main.manager", manager)
    
    client = TestClient(app)
    
    response = client.get("/api/admin/popular-sizes", headers={"X-Admin-Password": "test123"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["width"] == 500


def test_metrics_middleware_class():
    """Test that metrics middleware class is defined."""
    from src.main import MetricsMiddleware
    
    assert MetricsMiddleware is not None
    assert hasattr(MetricsMiddleware, "dispatch")


def test_metrics_disabled_by_default(client: TestClient):
    """Test that metrics are disabled when no admin password is set."""
    # With default settings (no admin password), metrics should be disabled
    response = client.get("/api/admin/stats", headers={"X-Admin-Password": "test"})
    assert response.status_code == 404
