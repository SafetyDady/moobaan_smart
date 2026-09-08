"""Serialize settlement writers. Lock ledger first, then invoices in ID order.

Locks belong to the caller's transaction (commit/rollback releases them). Refresh
collections after waiting: the Session may already contain a pre-lock balance.
"""
from sqlalchemy.orm import Session
from app.db.models import Invoice, IncomeTransaction


def lock_invoices(db: Session, *, invoice_ids=None, house_id=None):
    if invoice_ids is None and house_id is None:
        raise ValueError("An invoice or house scope is required")
    query = db.query(Invoice)
    if invoice_ids is not None:
        query = query.filter(Invoice.id.in_(sorted(set(invoice_ids))))
    if house_id is not None:
        query = query.filter(Invoice.house_id == house_id)
    invoices = query.order_by(Invoice.id).populate_existing().with_for_update().all()
    for invoice in invoices:
        db.expire(invoice, ["payments", "credit_notes"])
    return invoices


def lock_invoice(db: Session, invoice_id: int):
    invoices = lock_invoices(db, invoice_ids=[invoice_id])
    return invoices[0] if invoices else None


def lock_ledger(db: Session, ledger_id: int):
    ledger = (db.query(IncomeTransaction)
              .filter(IncomeTransaction.id == ledger_id)
              .populate_existing().with_for_update().first())
    if ledger:
        db.expire(ledger, ["invoice_payments"])
    return ledger
