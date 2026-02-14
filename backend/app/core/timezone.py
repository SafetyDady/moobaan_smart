"""
Timezone utility: ensure all datetimes are stored as UTC.

Policy:
  - All naive datetimes from user input or CSV are assumed Asia/Bangkok.
  - All datetimes are converted to UTC before database storage.
  - All UI display is handled by frontend (converts UTC → Bangkok).
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
    return dt.astimezone(UTC_TZ)


def utc_now() -> datetime:
    """Return current time in UTC (timezone-aware)."""
    return datetime.now(UTC_TZ)
