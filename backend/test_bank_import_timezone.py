#!/usr/bin/env python3
"""
Regression test for bank-statement month-boundary validation across timezones.

Bug: effective_at is stored as UTC. The month check compared the UTC calendar
date directly against the selected month, so a transaction just after Thai
midnight (e.g. 01:51 ICT = 18:51 UTC the previous day) was judged against the
previous month and wrongly rejected with "falls outside selected month".

These tests exercise BankStatementValidator.validate_batch and the CSV parser
without a real database (the only DB call is the duplicate-batch lookup, which
we stub to "no existing batch").
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.timezone import ensure_utc, BANGKOK_TZ
from app.services.csv_parser import CSVParserService
from app.services.bank_statement_validator import BankStatementValidator


class _FakeQuery:
    """Minimal query stub: filter() chains, first() returns None (no existing batch)."""
    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None


class _FakeSession:
    def query(self, *args, **kwargs):
        return _FakeQuery()


def _txn(effective_at, credit=600):
    return {
        'effective_at': effective_at,
        'description': 'รับโอนเงิน',
        'details': None,
        'debit': None,
        'credit': credit,
        'balance': None,
        'channel': 'K PLUS',
        'raw_row': [],
    }


def test_after_thai_midnight_belongs_to_bangkok_month():
    """01:51 ICT on 1 June (= 18:51 UTC 31 May) must count as June, not May."""
    # Bangkok-local 2026-06-01 01:51 → stored as UTC 2026-05-31 18:51
    naive_bkk = datetime(2026, 6, 1, 1, 51)
    effective_at = ensure_utc(naive_bkk)
    assert effective_at.astimezone(BANGKOK_TZ).month == 6
    assert effective_at.month == 5  # UTC really is the previous month — the trap

    result = BankStatementValidator.validate_batch(
        db=_FakeSession(),
        bank_account_id="00000000-0000-0000-0000-000000000001",
        year=2026,
        month=6,
        transactions=[_txn(effective_at)],
    )

    assert result.is_valid(), f"Should pass but got errors: {result.errors}"
    print("✅ after-Thai-midnight transaction accepted into June")


def test_genuine_wrong_month_still_rejected():
    """A transaction truly in May (by Bangkok date) must still be rejected for June."""
    effective_at = ensure_utc(datetime(2026, 5, 15, 10, 0))  # clearly May in ICT
    result = BankStatementValidator.validate_batch(
        db=_FakeSession(),
        bank_account_id="00000000-0000-0000-0000-000000000001",
        year=2026,
        month=6,
        transactions=[_txn(effective_at)],
    )
    assert not result.is_valid(), "May transaction should be rejected for June batch"
    assert any("falls outside selected month" in e for e in result.errors)
    print("✅ genuine wrong-month transaction still rejected")


def test_end_of_thai_month_boundary():
    """23:30 ICT on 30 June (= 16:30 UTC 30 June) must count as June."""
    effective_at = ensure_utc(datetime(2026, 6, 30, 23, 30))
    result = BankStatementValidator.validate_batch(
        db=_FakeSession(),
        bank_account_id="00000000-0000-0000-0000-000000000001",
        year=2026,
        month=6,
        transactions=[_txn(effective_at)],
    )
    assert result.is_valid(), f"Should pass but got errors: {result.errors}"
    print("✅ late-evening end-of-month transaction accepted into June")


def test_csv_parse_then_validate_june_boundary():
    """End-to-end: a CSV row dated 01/06/2569 01:51 (BE) validates into June 2026."""
    csv_content = (
        "วันที่,รายการ,ถอนเงิน,ฝากเงิน,ยอดคงเหลือ,ช่องทาง\n"
        "01/06/2569 01:51,รับโอนเงิน,,600.00,300168.92,K PLUS\n"
        "30/06/2569 21:03,รับโอนเงิน,,1200.00,301368.92,K PLUS\n"
    )
    parsed = CSVParserService.parse_csv(csv_content, enable_diagnostics=False)
    txns = parsed['transactions']
    assert len(txns) == 2, f"expected 2 transactions, got {len(txns)}"

    # First row stored as UTC should be the previous day (the original bug trigger)
    assert txns[0]['effective_at'].astimezone(BANGKOK_TZ).month == 6

    result = BankStatementValidator.validate_batch(
        db=_FakeSession(),
        bank_account_id="00000000-0000-0000-0000-000000000001",
        year=2026,
        month=6,
        transactions=txns,
    )
    assert result.is_valid(), f"Should pass but got errors: {result.errors}"
    print("✅ CSV (BE dates) round-trips and validates into June")


def main():
    print("=" * 60)
    print("Bank Statement Import - Timezone Boundary Regression Tests")
    print("=" * 60)
    tests = [
        test_after_thai_midnight_belongs_to_bangkok_month,
        test_genuine_wrong_month_still_rejected,
        test_end_of_thai_month_boundary,
        test_csv_parse_then_validate_june_boundary,
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
    print("✅ All timezone boundary tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
