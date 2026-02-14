"""
Timezone utility: ensure all datetimes are stored as UTC.

Policy (LOCKED — do not change):
  1. All DB timestamps = UTC only.
  2. All UI display = Asia/Bangkok (handled by frontend).
  3. All business month boundaries = Asia/Bangkok.
  4. All naive datetimes from user input or CSV are assumed Asia/Bangkok.
  5. No path may bypass ensure_utc() before DB insert.
  6. Production timeline is canonical — no more historical shifts.
"""

from datetime import datetime, timezone, timedelta

# Bangkok is UTC+7, define without requiring zoneinfo (Python 3.9+)
BANGKOK_OFFSET = timedelta(hours=7)
BANGKOK_TZ = timezone(BANGKOK_OFFSET, name="Asia/Bangkok")
UTC_TZ = timezone.utc


def ensure_utc(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC.

    - If naive (no tzinfo): assume Asia/Bangkok, convert to UTC.
    - If aware: convert to UTC.

    Examples:
        naive 15:28 → Bangkok 15:28 → UTC 08:28
        aware 15:28+07:00 → UTC 08:28
        aware 15:28+00:00 → UTC 15:28 (already UTC)
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Naive → assume Bangkok
        dt = dt.replace(tzinfo=BANGKOK_TZ)
    result = dt.astimezone(UTC_TZ)
    assert result.tzinfo is not None, "ensure_utc produced naive datetime"
    return result


def assert_utc(dt: datetime, field_name: str = "datetime") -> datetime:
    """
    Defensive assertion: verify a datetime is timezone-aware UTC before DB insert.
    
    Use this at every DB insert point to prevent silent corruption.
    Raises AssertionError immediately if dt is naive or not UTC.
    """
    if dt is None:
        return None
    assert dt.tzinfo is not None, (
        f"[TZ GUARD] {field_name} is naive — must be UTC-aware before DB insert. "
        f"Value: {dt!r}. Use ensure_utc() first."
    )
    assert dt.utcoffset() == timedelta(0), (
        f"[TZ GUARD] {field_name} is not UTC (offset={dt.utcoffset()}). "
        f"Value: {dt!r}. Use ensure_utc() first."
    )
    return dt


def utc_now() -> datetime:
    """Return current time in UTC (timezone-aware)."""
    return datetime.now(UTC_TZ)
