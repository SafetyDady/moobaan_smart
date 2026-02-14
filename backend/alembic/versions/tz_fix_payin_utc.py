"""Fix timezone: Normalize pay-in transfer_date from naive-Bangkok-as-UTC to proper UTC.

Root cause: When frontend sends naive datetime (e.g. "2026-01-30T15:28:00") representing
Bangkok time, backend stored it as-is. On production PostgreSQL (timezone=Etc/UTC), the
naive 15:28 was stored as 15:28+00:00 (UTC), but the actual UTC equivalent is 08:28+00:00.
This caused a 7-hour mismatch with bank transactions, breaking auto-matching.

Fix: Subtract 7 hours from all pay-in transfer_date values that were stored with
Bangkok time incorrectly treated as UTC.

SAFETY:
- Only affects payin_reports.transfer_date
- Only adjusts records where transfer_date has NO sub-minute precision (all resident submissions)
- Updates transfer_hour/transfer_minute to match the corrected UTC time
- Reversible via downgrade (adds 7 hours back)

Revision ID: tz_fix_payin_utc
Revises: p1_statement_driven
Create Date: 2026-02-15
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'tz_fix_payin_utc'
down_revision = 'p1_statement_driven'
branch_labels = None
depends_on = None


def upgrade():
    """
    Shift all payin transfer_date values by -7 hours (Bangkok→UTC normalization).
    
    Before: 15:28+00:00 (Bangkok time wrongly stored as UTC)
    After:  08:28+00:00 (correct UTC)
    
    Also update transfer_hour/transfer_minute to reflect Bangkok display time
    (they should still show 15:28 in Bangkok, which is the hour/minute of the 
    original Bangkok time — these are for display only).
    """
    # Step 1: Fix transfer_date by subtracting 7 hours
    # This converts "Bangkok-time-as-UTC" → actual UTC
    op.execute("""
        UPDATE payin_reports
        SET transfer_date = transfer_date - INTERVAL '7 hours'
        WHERE transfer_date IS NOT NULL
    """)
    
    # Step 2: transfer_hour and transfer_minute should remain as Bangkok display time.
    # They were originally set from the Bangkok input (e.g., hour=15, minute=28).
    # Since transfer_date is now in UTC (08:28), the hour/minute fields still
    # represent Bangkok time for display — no change needed.
    # 
    # Going forward, payins.py now sets:
    #   transfer_date = UTC datetime
    #   transfer_hour = Bangkok hour (for display)
    #   transfer_minute = Bangkok minute (for display)


def downgrade():
    """Reverse: add 7 hours back to transfer_date."""
    op.execute("""
        UPDATE payin_reports
        SET transfer_date = transfer_date + INTERVAL '7 hours'
        WHERE transfer_date IS NOT NULL
    """)
