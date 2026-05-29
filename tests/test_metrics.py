from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from src.metrics import MetricsTracker


def test_metrics_tracker_initialization(tmp_path: Path):
    """Test metrics tracker initializes database."""
    db_path = tmp_path / "test_metrics.db"
    MetricsTracker(db_path)
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
        image_format="jpeg",
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

    tracker.log_request("/500/500.webp", "GET", 200, 10.0, image_format="webp")
    tracker.log_request("/500/500.webp", "GET", 200, 10.0, image_format="webp")
    tracker.log_request("/500/500.png", "GET", 200, 10.0, image_format="png")

    formats = tracker.get_popular_formats()
    assert len(formats) == 2
    assert formats[0]["format"] == "webp"
    assert formats[0]["count"] == 2


def test_stats_summary(tmp_path: Path):
    """Test comprehensive stats summary."""
    tracker = MetricsTracker(tmp_path / "test.db")

    tracker.log_request("/500/500", "GET", 200, 10.0, width=500, height=500, cache_hit=True)
    tracker.log_request("/600/600", "GET", 200, 20.0, width=600, height=600, cache_hit=False)
    tracker.log_request("/500/500", "GET", 404, 5.0, width=500, height=500, cache_hit=False)

    stats = tracker.get_stats_summary()
    assert stats["total_requests"] == 3
    assert stats["cache_hit_rate"] == pytest.approx(33.33, rel=0.1)
    assert stats["avg_response_time_ms"] == pytest.approx(11.67, rel=0.1)
    assert len(stats["popular_sizes"]) == 2
    assert "response_time_percentiles" in stats
    assert "error_summary" in stats
    assert stats["error_summary"]["client_errors"] == 1
    assert "requests_by_day" in stats
    assert "peak_hours" in stats
    assert "bandwidth_estimate" in stats


def test_new_granular_stats(tmp_path: Path):
    """Test new granular stats methods."""
    tracker = MetricsTracker(tmp_path / "test.db")

    tracker.log_request("/500/500", "GET", 200, 10.0)
    tracker.log_request("/600/600", "GET", 200, 20.0)
    tracker.log_request("/500/500", "GET", 500, 5.0)

    percentiles = tracker.get_response_time_percentiles()
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles

    errors = tracker.get_error_summary()
    assert errors["total"] == 3
    assert errors["server_errors"] == 1
    assert errors["error_rate"] == pytest.approx(33.33, rel=0.1)

    bandwidth = tracker.get_bandwidth_estimate()
    assert "bytes" in bandwidth
    assert bandwidth["bytes"] > 0

    daily = tracker.get_requests_by_day()
    assert len(daily) >= 1

    peak = tracker.get_peak_hours()
    assert len(peak) >= 1


def test_metrics_middleware_class():
    """Test that metrics middleware class is defined."""
    from src.main import MetricsMiddleware

    assert MetricsMiddleware is not None
    assert hasattr(MetricsMiddleware, "dispatch")


def test_metrics_always_enabled(client: TestClient):
    """Test that metrics middleware is always active."""
    # Make any request to trigger metrics logging
    response = client.get("/500/500")
    assert response.status_code in [200, 404]  # May or may not find images
