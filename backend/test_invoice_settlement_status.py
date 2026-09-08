#!/usr/bin/env python3
"""
Unit tests for Invoice.get_settlement_status() — the canonical invoice status
(Phase 2: one status rule shared by list API, detail API, filter and the UI).

Regression guards for the two mislabels this phase fixed:
  - a fully PAID invoice must NOT report CREDITED (old UI rule keyed on
    ``outstanding === 0``, so paid bills showed "เครดิตแล้ว")
  - a partially CREDITED but unpaid invoice must NOT report PARTIALLY_PAID
    (old UI rule keyed on ``outstanding < total``)

The status methods only read total_amount / credit_notes / payments, so we bind
them to a plain object and skip both the DB and SQLAlchemy instrumentation.
"""
import sys
import os
from decimal import Decimal
from types import SimpleNamespace

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models.invoice import Invoice, InvoiceStatus

# Methods that read only plain attributes, so they can be bound to a fake self.
_METHODS = [
    'get_total_credited_decimal', 'get_total_paid_decimal',
    'get_net_amount_decimal', 'get_remaining_balance_decimal',
    'is_fully_credited', 'get_settlement_status', 'update_status',
]


def make_invoice(total, credits=(), payments=()):
    """credits/payments: list of amounts, or (amount, status) tuples."""
    inv = type('FakeInvoice', (), {})()
    inv.total_amount = Decimal(str(total))
    inv.credit_notes = [
        SimpleNamespace(credit_amount=Decimal(str(c[0])), status=c[1])
        if isinstance(c, tuple) else
        SimpleNamespace(credit_amount=Decimal(str(c)), status='applied')
        for c in credits
    ]
    inv.payments = [
        SimpleNamespace(amount=Decimal(str(p[0])), status=SimpleNamespace(value=p[1]))
        if isinstance(p, tuple) else
        SimpleNamespace(amount=Decimal(str(p)), status=SimpleNamespace(value='ACTIVE'))
        for p in payments
    ]
    inv.status = None
    for name in _METHODS:
        setattr(inv, name, getattr(Invoice, name).__get__(inv))
    return inv


def test_unpaid_is_issued():
    assert make_invoice(600).get_settlement_status() == 'ISSUED'
    print("✅ unpaid → ISSUED")


def test_partial_payment_is_partially_paid():
    assert make_invoice(600, payments=[400]).get_settlement_status() == 'PARTIALLY_PAID'
    print("✅ partial payment → PARTIALLY_PAID")


def test_fully_paid_is_paid_not_credited():
    """REGRESSION: the old UI rule labelled any outstanding==0 bill as CREDITED."""
    status = make_invoice(600, payments=[600]).get_settlement_status()
    assert status == 'PAID', f"fully paid must be PAID, got {status}"
    print("✅ fully paid → PAID (not CREDITED)")


def test_fully_credited_is_credited():
    assert make_invoice(600, credits=[600]).get_settlement_status() == 'CREDITED'
    print("✅ fully credited → CREDITED")


def test_partial_credit_unpaid_is_issued_not_partially_paid():
    """REGRESSION: partial credit with no payment is not a partial *payment*."""
    status = make_invoice(600, credits=[300]).get_settlement_status()
    assert status == 'ISSUED', f"partial credit unpaid must be ISSUED, got {status}"
    print("✅ partial credit, unpaid → ISSUED (not PARTIALLY_PAID)")


def test_payment_plus_credit_settles_to_paid():
    inv = make_invoice(600, credits=[200], payments=[400])
    assert inv.get_remaining_balance_decimal() == Decimal('0')
    assert inv.get_settlement_status() == 'PAID'
    print("✅ payment 400 + credit 200 on 600 → PAID")


def test_credit_plus_partial_payment_is_partially_paid():
    assert make_invoice(600, credits=[100], payments=[200]).get_settlement_status() == 'PARTIALLY_PAID'
    print("✅ credit 100 + payment 200 on 600 → PARTIALLY_PAID")


def test_reversed_payment_ignored():
    inv = make_invoice(600, payments=[(600, 'REVERSED')])
    assert inv.get_total_paid_decimal() == Decimal('0')
    assert inv.get_settlement_status() == 'ISSUED'
    print("✅ REVERSED payment ignored → ISSUED")


def test_non_applied_credit_note_ignored():
    inv = make_invoice(600, credits=[(600, 'void')])
    assert inv.get_total_credited_decimal() == Decimal('0')
    assert inv.get_settlement_status() == 'ISSUED'
    print("✅ non-'applied' credit note ignored → ISSUED")


def test_zero_total_is_not_credited():
    """is_fully_credited guards total > 0 so a ฿0 invoice isn't reported CREDITED."""
    inv = make_invoice(0)
    assert inv.is_fully_credited() is False
    assert inv.get_settlement_status() == 'PAID'  # nothing outstanding
    print("✅ zero-total invoice → not CREDITED")


def test_special_invoice_large_amount():
    """Owner rule: cap follows each invoice's own total, not a fixed 600."""
    inv = make_invoice(20000, credits=[5000])
    assert inv.get_remaining_balance_decimal() == Decimal('15000')
    assert inv.get_settlement_status() == 'ISSUED'
    print("✅ special invoice 20,000 credited 5,000 → 15,000 outstanding, ISSUED")


def test_update_status_persists_cancelled_for_credited():
    """CREDITED is an API value; the DB enum stores CANCELLED."""
    inv = make_invoice(600, credits=[600])
    inv.update_status()
    assert inv.status == InvoiceStatus.CANCELLED, f"got {inv.status}"

    paid = make_invoice(600, payments=[600])
    paid.update_status()
    assert paid.status == InvoiceStatus.PAID, f"got {paid.status}"
    print("✅ update_status persists CANCELLED for credited, PAID for paid")


def main():
    print("=" * 62)
    print("Invoice.get_settlement_status() — canonical status tests")
    print("=" * 62)
    tests = [
        test_unpaid_is_issued,
        test_partial_payment_is_partially_paid,
        test_fully_paid_is_paid_not_credited,
        test_fully_credited_is_credited,
        test_partial_credit_unpaid_is_issued_not_partially_paid,
        test_payment_plus_credit_settles_to_paid,
        test_credit_plus_partial_payment_is_partially_paid,
        test_reversed_payment_ignored,
        test_non_applied_credit_note_ignored,
        test_zero_total_is_not_credited,
        test_special_invoice_large_amount,
        test_update_status_persists_cancelled_for_credited,
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
    print("=" * 62)
    if failed:
        print(f"❌ {failed} test(s) failed")
        sys.exit(1)
    print("✅ All canonical status tests passed!")
    print("=" * 62)


if __name__ == "__main__":
    main()
