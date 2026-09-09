"""Shared eligibility for the invoice picker and locked apply endpoint.

Existing accepted pay-ins remain supported. A receipt without a pay-in must
retain its confirmed Statement provenance; a NULL payin_id alone is not proof.
Writers must hold the ledger lock while evaluating this function.
"""
from decimal import Decimal
from app.db.models import PayinStatus, PostingStatus
from app.db.models.income_transaction import LedgerStatus


def allocation_error(ledger):
    if ledger.status != LedgerStatus.POSTED:
        return 'Cannot apply a reversed or unposted ledger'
    if ledger.payin_id is not None:
        payin = ledger.payin
        if not payin or payin.status != PayinStatus.ACCEPTED:
            return 'Ledger pay-in must be ACCEPTED'
        if payin.house_id != ledger.house_id:
            return 'Ledger and pay-in must belong to the same house'
        return None
    bank = ledger.bank_transaction
    if (not bank or bank.posting_status != PostingStatus.POSTED
            or bank.matched_payin_id is not None or not bank.batch
            or bank.batch.status != 'CONFIRMED'):
        return 'Receipt without pay-in requires a confirmed, posted Statement source'
    if (Decimal(bank.credit or 0) <= 0 or Decimal(bank.debit or 0) != 0
            or Decimal(bank.credit) != Decimal(ledger.amount)
            or bank.effective_at != ledger.received_at):
        return 'Ledger amount or receipt time does not match its Statement source'
    return None
