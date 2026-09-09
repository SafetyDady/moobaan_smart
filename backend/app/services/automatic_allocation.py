"""Use confirmed household funds automatically; never rewrite existing allocations.

Automatic receipt creation and invoice creation take the same transaction-scoped
house gate, including when no ledger/invoice exists yet. Row locking remains
ledger IDs first, then invoice IDs, compatible with explicit settlement writers.
The caller owns commit/rollback; no background task or resident invoice choice.
"""
from dataclasses import dataclass
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload
from app.db.models import IncomeTransaction, Invoice, InvoicePayment, PaymentStatus, BankTransaction
from app.services.invoice_locking import lock_invoices
from app.services.receipt_eligibility import allocation_error

_LOCK_NAMESPACE = 1296192334  # Dedicated PostgreSQL advisory-lock namespace.


@dataclass
class AllocationScope:
    house_ids: tuple
    ledgers: list
    invoices: list


def prepare_allocation(db: Session, house_ids) -> AllocationScope:
    """Must run before inserting receipts/invoices or taking invoice row locks.

    For monthly batches acquire ALL house gates, ALL ledgers, ALL invoices in
    that order; do not loop house A's invoices then house B's ledgers.
    """
    house_ids = tuple(sorted(set(house_ids)))
    for house_id in house_ids:
        db.execute(text('SELECT pg_advisory_xact_lock(:namespace, :house_id)'),
                   {'namespace': _LOCK_NAMESPACE, 'house_id': house_id})
    ledgers = (db.query(IncomeTransaction).filter(IncomeTransaction.house_id.in_(house_ids))
               .options(selectinload(IncomeTransaction.invoice_payments),
                        selectinload(IncomeTransaction.payin),
                        selectinload(IncomeTransaction.bank_transaction).selectinload(BankTransaction.batch))
               .order_by(IncomeTransaction.id).populate_existing().with_for_update().all())
    invoice_ids = [row[0] for row in db.query(Invoice.id).filter(Invoice.house_id.in_(house_ids)).all()]
    invoices = lock_invoices(db, invoice_ids=invoice_ids)
    # Refresh the expired balance collections in batches after all row locks.
    if invoices:
        db.query(Invoice).filter(Invoice.id.in_(invoice_ids)).options(
            selectinload(Invoice.payments), selectinload(Invoice.credit_notes)
        ).populate_existing().all()
    return AllocationScope(house_ids, ledgers, invoices)


def apply_prepared_funds(db: Session, scope: AllocationScope):
    """FIFO by due_date/id, using older received_at/id funds first, per house.

    Newly inserted ledger/invoice objects must be appended to the prepared scope
    by the caller. Their rows are already owned by the current transaction.
    """
    db.flush()
    remaining = {inv.id: inv.get_remaining_balance_decimal() for inv in scope.invoices}
    created = []
    touched = {}
    used_ledgers = {}
    bills_by_house = {}
    for inv in sorted(scope.invoices, key=lambda bill: (bill.due_date, bill.id)):
        bills_by_house.setdefault(inv.house_id, []).append(inv)
    for ledger in sorted(scope.ledgers, key=lambda entry: (entry.received_at, entry.id)):
        if ledger.house_id not in scope.house_ids:
            raise ValueError('Receipt outside prepared household scope')
        if allocation_error(ledger):
            continue  # Pending/reversed or invalid provenance cannot fund bills.
        applied = sum((Decimal(p.amount) for p in ledger.invoice_payments
                       if p.status == PaymentStatus.ACTIVE), Decimal('0'))
        available = Decimal(ledger.amount) - applied
        if available < 0:
            raise ValueError('Receipt is already overallocated; review required')
        for inv in bills_by_house.get(ledger.house_id, []):
            if available <= 0:
                break
            if inv.house_id != ledger.house_id or remaining[inv.id] <= 0:
                continue
            amount = min(available, remaining[inv.id])
            payment = InvoicePayment(invoice_id=inv.id, income_transaction_id=ledger.id,
                                     amount=amount, status=PaymentStatus.ACTIVE)
            db.add(payment)
            created.append(payment)
            available -= amount
            remaining[inv.id] -= amount
            touched[inv.id] = inv
            used_ledgers[ledger.id] = ledger
    db.flush()
    for inv in touched.values():
        db.expire(inv, ['payments', 'credit_notes'])
        inv.update_status()
    for ledger in used_ledgers.values():
        db.expire(ledger, ['invoice_payments'])
    db.flush()
    return created
