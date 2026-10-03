"""Time helpers: the only source of "now" for business logic.

Why a module for two tiny functions:
- utcnow() makes every timestamp the application writes an aware-UTC
  datetime. Consistency matters because tests run on in-memory SQLite while
  production runs on PostgreSQL (see ensure_utc below).
- ensure_utc() normalizes datetimes READ from the database. SQLite stores
  DATETIME columns without timezone information and hands back naive
  datetimes; PostgreSQL returns aware ones. Comparing those two shapes
  directly raises TypeError, so anything read from a row passes through
  ensure_utc() before being compared with utcnow().

Step 4 (get_current_user) needs this for session-expiry checks; defined now
so the convention is established alongside the token lifecycles that use it.
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Return `value` as an aware UTC datetime.

    Naive values (SQLite's shape) are assumed to already be UTC — true for
    anything this application writes, because every bound timestamp comes
    from utcnow(). Aware values are converted to UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
