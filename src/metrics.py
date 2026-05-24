from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from src.config import settings


class MetricsTracker:
    """Track usage metrics in SQLite database."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.images_dir / ".placepix_metrics.db"
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time_ms REAL NOT NULL,
                    category TEXT,
                    width INTEGER,
                    height INTEGER,
                    format TEXT,
                    cache_hit BOOLEAN NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date DATE PRIMARY KEY,
                    total_requests INTEGER NOT NULL,
                    cache_hits INTEGER NOT NULL,
                    total_bandwidth_bytes INTEGER NOT NULL,
                    avg_response_time_ms REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_timestamp 
                ON requests(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_endpoint 
                ON requests(endpoint)
            """)
            conn.commit()

    def log_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        category: str | None = None,
        width: int | None = None,
        height: int | None = None,
        format: str | None = None,
        cache_hit: bool = False,
    ) -> None:
        """Log a single request."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO requests (
                    timestamp, endpoint, method, status_code, response_time_ms,
                    category, width, height, format, cache_hit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    endpoint,
                    method,
                    status_code,
                    response_time_ms,
                    category,
                    width,
                    height,
                    format,
                    cache_hit,
                ),
            )
            conn.commit()

    def get_total_requests(self) -> int:
        """Get total number of requests."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM requests")
            return cursor.fetchone()[0]

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as hits
                FROM requests
            """)
            total, hits = cursor.fetchone()
            if total == 0:
                return 0.0
            return (hits / total) * 100

    def get_avg_response_time(self) -> float:
        """Get average response time in milliseconds."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT AVG(response_time_ms) FROM requests")
            result = cursor.fetchone()[0]
            return result if result else 0.0

    def get_popular_sizes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most popular image sizes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT width, height, COUNT(*) as count
                FROM requests
                WHERE width IS NOT NULL AND height IS NOT NULL
                GROUP BY width, height
                ORDER BY count DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [
                {"width": row[0], "height": row[1], "count": row[2]}
                for row in cursor.fetchall()
            ]

    def get_popular_categories(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most popular categories."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT category, COUNT(*) as count
                FROM requests
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [
                {"category": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]

    def get_popular_formats(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most popular output formats."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT format, COUNT(*) as count
                FROM requests
                WHERE format IS NOT NULL
                GROUP BY format
                ORDER BY count DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [
                {"format": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]

    def get_requests_by_endpoint(self) -> list[dict[str, Any]]:
        """Get request count by endpoint."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT endpoint, COUNT(*) as count
                FROM requests
                GROUP BY endpoint
                ORDER BY count DESC
                """
            )
            return [
                {"endpoint": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]

    def get_requests_by_status(self) -> list[dict[str, Any]]:
        """Get request count by status code."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT status_code, COUNT(*) as count
                FROM requests
                GROUP BY status_code
                ORDER BY status_code
                """
            )
            return [
                {"status_code": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]

    def aggregate_daily_stats(self) -> None:
        """Aggregate stats for yesterday into daily_stats table."""
        yesterday = date.today().replace(day=date.today().day - 1)
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if already aggregated
            cursor = conn.execute(
                "SELECT COUNT(*) FROM daily_stats WHERE date = ?",
                (yesterday.isoformat(),),
            )
            if cursor.fetchone()[0] > 0:
                return
            
            # Aggregate yesterday's data
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as cache_hits,
                    AVG(response_time_ms) as avg_response_time
                FROM requests
                WHERE DATE(timestamp) = ?
                """,
                (yesterday.isoformat(),),
            )
            row = cursor.fetchone()
            if row and row[0] > 0:
                conn.execute(
                    """
                    INSERT INTO daily_stats (
                        date, total_requests, cache_hits, 
                        total_bandwidth_bytes, avg_response_time_ms
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (yesterday.isoformat(), row[0], row[1] or 0, 0, row[2] or 0.0),
                )
                conn.commit()

    def get_stats_summary(self) -> dict[str, Any]:
        """Get comprehensive stats summary."""
        return {
            "total_requests": self.get_total_requests(),
            "cache_hit_rate": round(self.get_cache_hit_rate(), 2),
            "avg_response_time_ms": round(self.get_avg_response_time(), 2),
            "popular_sizes": self.get_popular_sizes(10),
            "popular_categories": self.get_popular_categories(10),
            "popular_formats": self.get_popular_formats(10),
            "requests_by_endpoint": self.get_requests_by_endpoint(),
            "requests_by_status": self.get_requests_by_status(),
        }
