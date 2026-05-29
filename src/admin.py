from __future__ import annotations

from pathlib import Path
import sys

# Allow running from repo root without package install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.metrics import MetricsTracker


def _fmt_number(n: int) -> str:
    """Format large numbers with commas."""
    return f"{n:,}"


def _print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _print_row(label: str, value: str, width: int = 40) -> None:
    print(f"  {label:<{width}}{value}")


def _print_table(headers: list[str], rows: list[list[str]], col_widths: list[int]) -> None:
    # Print header row
    header_line = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    print(f"  {header_line}")
    print(f"  {'-' * (sum(col_widths) + 3 * (len(headers) - 1))}")
    for row in rows:
        row_line = " | ".join(f"{cell:<{col_widths[i]}}" for i, cell in enumerate(row))
        print(f"  {row_line}")


def main() -> None:
    tracker = MetricsTracker()
    stats = tracker.get_stats_summary()

    _print_header("PlacePix Stats")

    # Overview
    _print_header("Overview")
    _print_row("Total Requests", _fmt_number(stats["total_requests"]))
    _print_row("Cache Hit Rate", f"{stats['cache_hit_rate']}%")
    _print_row("Avg Response Time", f"{stats['avg_response_time_ms']} ms")

    # Response Time Percentiles
    percentiles = stats["response_time_percentiles"]
    _print_header("Response Times")
    _print_row("p50 (median)", f"{percentiles['p50']} ms")
    _print_row("p95", f"{percentiles['p95']} ms")
    _print_row("p99", f"{percentiles['p99']} ms")

    # Bandwidth
    bw = stats["bandwidth_estimate"]
    _print_header("Bandwidth Estimate")
    _print_row("Total", f"{bw['mb']} MB ({bw['gb']} GB)")

    # Errors
    err = stats["error_summary"]
    _print_header("Errors")
    _print_row("Total Requests", _fmt_number(err["total"]))
    _print_row("Client Errors (4xx)", _fmt_number(err["client_errors"]))
    _print_row("Server Errors (5xx)", _fmt_number(err["server_errors"]))
    _print_row("Overall Error Rate", f"{err['error_rate']}%")

    # Daily Requests
    daily = stats["requests_by_day"]
    if daily:
        _print_header("Daily Requests (Last 7 Days)")
        _print_table(
            ["Date", "Requests"],
            [[d["day"], _fmt_number(d["count"])] for d in daily],
            [12, 12],
        )

    # Peak Hours
    peak = stats["peak_hours"]
    if peak:
        _print_header("Peak Hours (Top 5)")
        _print_table(
            ["Hour", "Requests"],
            [[p["hour"], _fmt_number(p["count"])] for p in peak],
            [10, 12],
        )

    # Popular Sizes
    sizes = stats["popular_sizes"]
    if sizes:
        _print_header("Popular Sizes (Top 10)")
        _print_table(
            ["Size", "Requests"],
            [[f"{s['width']}x{s['height']}", _fmt_number(s["count"])] for s in sizes],
            [14, 12],
        )

    # Popular Categories
    cats = stats["popular_categories"]
    if cats:
        _print_header("Popular Categories (Top 10)")
        _print_table(
            ["Category", "Requests"],
            [[c["category"], _fmt_number(c["count"])] for c in cats],
            [20, 12],
        )

    # Popular Formats
    fmts = stats["popular_formats"]
    if fmts:
        _print_header("Popular Formats (Top 10)")
        _print_table(
            ["Format", "Requests"],
            [[f["format"].upper(), _fmt_number(f["count"])] for f in fmts],
            [10, 12],
        )

    # Status Codes
    statuses = stats["requests_by_status"]
    if statuses:
        _print_header("Requests by Status Code")
        _print_table(
            ["Status", "Requests"],
            [[str(s["status_code"]), _fmt_number(s["count"])] for s in statuses],
            [10, 12],
        )

    print()


if __name__ == "__main__":
    main()
