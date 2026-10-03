"""Tests for the time helpers — tiny, but every expiry check leans on them."""

from datetime import UTC, datetime, timedelta, timezone

from app.core.clock import ensure_utc, utcnow


def test_utcnow_is_timezone_aware_utc():
    now = utcnow()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_ensure_utc_attaches_utc_to_naive_values():
    naive = datetime(2025, 6, 1, 12, 0, 0)  # the shape SQLite hands back
    assert ensure_utc(naive) == datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)


def test_ensure_utc_converts_aware_values_to_utc():
    plus_two = timezone(timedelta(hours=2))  # 14:00+02:00 == 12:00 UTC
    value = datetime(2025, 6, 1, 14, 0, 0, tzinfo=plus_two)
    assert ensure_utc(value) == datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
