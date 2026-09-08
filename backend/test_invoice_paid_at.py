#!/usr/bin/env python3
"""
Unit tests for Invoice.get_last_payment_at() — the "วันที่ชำระล่าสุด" column source.

The method returns the latest income_transaction.received_at among ACTIVE payments
(REVERSED excluded), or None when nothing qualifies. It reads only ``self.payments``,
so we exercise it with lightweight fakes and call it unbound — no DB needed.

Covers the review's point #4:
  - no payments
  - two payments where receipt order differs from applied (link) order
  - the latest-received payment is REVERSED (must be ignored)
  - a payment whose ledger is missing
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models.invoice import Invoice

UTC = timezone.utc


def _payment(received_at, applied_at=None, status='ACTIVE', has_ledger=True):
    """Build a fake InvoicePayment-like object."""
    ledger = SimpleNamespace(received_at=received_at) if has_ledger else None
    status_obj = SimpleNamespace(value=status) if status is not None else None
    return SimpleNamespace(
        applied_at=applied_at,
        status=status_obj,
        income_transaction=ledger,
    )


def _call(payments):
    """Call the unbound method with a fake self exposing only .payments."""
    return Invoice.get_last_payment_at(SimpleNamespace(payments=payments))


def test_no_payments_returns_none():
    assert _call([]) is None
    assert _call(None) is None
    print("✅ no payments → None")


def test_returns_latest_received_regardless_of_applied_order():
    # Payment A: received FIRST (t1) but linked/applied LAST (t_late)
    # Payment B: received SECOND (t2) but linked/applied FIRST (t_early)
    t1 = datetime(2026, 8, 1, 3, 0, tzinfo=UTC)   # received earlier
    t2 = datetime(2026, 8, 20, 3, 0, tzinfo=UTC)  # received later  ← expected
    t_late = datetime(2026, 9, 5, 3, 0, tzinfo=UTC)
    t_early = datetime(2026, 8, 25, 3, 0, tzinfo=UTC)
    payments = [
        _payment(received_at=t1, applied_at=t_late),
        _payment(received_at=t2, applied_at=t_early),
    ]
    result = _call(payments)
    assert result == t2, f"expected latest received {t2}, got {result}"
    print("✅ picks max(received_at), independent of applied/link order")


def test_reversed_latest_is_ignored():
    active = datetime(2026, 8, 10, 3, 0, tzinfo=UTC)
    reversed_later = datetime(2026, 8, 28, 3, 0, tzinfo=UTC)  # newer but REVERSED
    payments = [
        _payment(received_at=active, status='ACTIVE'),
        _payment(received_at=reversed_later, status='REVERSED'),
    ]
    result = _call(payments)
    assert result == active, f"REVERSED payment should be ignored; got {result}"
    print("✅ REVERSED latest payment ignored → returns latest ACTIVE")


def test_all_reversed_returns_none():
    payments = [
        _payment(received_at=datetime(2026, 8, 10, 3, 0, tzinfo=UTC), status='REVERSED'),
    ]
    assert _call(payments) is None
    print("✅ all REVERSED → None (unpaid)")


def test_missing_ledger_is_skipped():
    good = datetime(2026, 8, 10, 3, 0, tzinfo=UTC)
    payments = [
        _payment(received_at=None, has_ledger=False),  # no ledger → skip
        _payment(received_at=good),
    ]
    assert _call(payments) == good
    print("✅ payment without ledger skipped")


def test_status_none_treated_as_active():
    t = datetime(2026, 8, 10, 3, 0, tzinfo=UTC)
    assert _call([_payment(received_at=t, status=None)]) == t
    print("✅ status None treated as ACTIVE (defensive)")


def test_bangkok_conversion_of_result():
    """UTC 2026-08-31 18:30 == Bangkok 2026-09-01 01:30 (the display converts this)."""
    from app.core.timezone import BANGKOK_TZ
    utc_val = datetime(2026, 8, 31, 18, 30, tzinfo=UTC)
    result = _call([_payment(received_at=utc_val)])
    bkk = result.astimezone(BANGKOK_TZ)
    assert (bkk.year, bkk.month, bkk.day, bkk.hour, bkk.minute) == (2026, 9, 1, 1, 30)
    print("✅ stored UTC converts to correct Bangkok wall-clock for display")


def main():
    print("=" * 60)
    print("Invoice.get_last_payment_at() — logic tests")
    print("=" * 60)
    tests = [
        test_no_payments_returns_none,
        test_returns_latest_received_regardless_of_applied_order,
        test_reversed_latest_is_ignored,
        test_all_reversed_returns_none,
        test_missing_ledger_is_skipped,
        test_status_none_treated_as_active,
        test_bangkok_conversion_of_result,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {t.__name__}: unexpected error: {e}")
            import traceback
            traceback.print_exc()
    print("=" * 60)
    if failed:
        print(f"❌ {failed} test(s) failed")
        sys.exit(1)
    print("✅ All invoice paid-at logic tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
