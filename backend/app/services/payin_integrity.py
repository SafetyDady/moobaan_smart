"""Pay-in evidence integrity. Callers own the transaction and commit.

Lock order: bank row, pay-in row, then the existing allocation lock order.
An unmatched pay-in has no bank lock. If its link changes while obtaining locks,
abort; never acquire a newly discovered bank lock after locking a pay-in.
"""
import logging
import hashlib
import json
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy import or_

from app.core.timezone import BANGKOK_TZ, ensure_utc
from app.db.models.bank_transaction import BankTransaction, PostingStatus
from app.db.models.payin_report import PayinReport, PayinStatus
from app.db.models.income_transaction import IncomeTransaction, LedgerStatus

logger = logging.getLogger(__name__)


def evidence_revision(payin):
    """Opaque review token; no schema change and no secret/user data in the token."""
    values = [payin.id, payin.house_id, str(payin.amount), payin.transfer_date.isoformat(),
              payin.transfer_hour, payin.transfer_minute, payin.slip_url,
              payin.status.value, str(payin.matched_statement_txn_id),
              payin.updated_at.isoformat() if payin.updated_at else None]
    return hashlib.sha256(json.dumps(values, ensure_ascii=True).encode()).hexdigest()


def validate_review_revision(payin, expected):
    # Optional for existing API clients; the new Admin review always sends it.
    if expected is not None and expected != evidence_revision(payin):
        conflict()


def conflict():
    raise HTTPException(409, detail={"code": "MATCH_CHANGED", "message":
        "รายการเปลี่ยนระหว่างตรวจ กรุณาโหลดข้อมูลใหม่และตรวจอีกครั้ง"})


def lock_bank(db, bank_id):
    bank = (db.query(BankTransaction).filter_by(id=bank_id)
            .populate_existing().with_for_update().first())
    if bank is None:
        raise HTTPException(404, "Bank transaction not found")
    return bank


def lock_payin_row(db, payin_id):
    payin = (db.query(PayinReport).filter_by(id=payin_id)
             .populate_existing().with_for_update().first())
    if payin is None:
        raise HTTPException(404, "Pay-in report not found")
    return payin


def lock_payin_evidence(db, payin_id):
    observed = db.query(PayinReport.matched_statement_txn_id).filter_by(id=payin_id).first()
    if observed is None:
        raise HTTPException(404, "Pay-in report not found")
    bank_id = observed[0]
    bank = lock_bank(db, bank_id) if bank_id else None
    payin = lock_payin_row(db, payin_id)
    if payin.matched_statement_txn_id != bank_id:
        conflict()
    # Detect inconsistent reverse links without clearing someone else's match.
    reverse_id = db.query(BankTransaction.id).filter_by(matched_payin_id=payin_id).scalar()
    if reverse_id != bank_id or (bank and bank.matched_payin_id != payin.id):
        conflict()
    return payin, bank


def assert_unposted(db, payin, bank=None):
    if payin.status == PayinStatus.ACCEPTED or (bank and bank.posting_status in
            (PostingStatus.POSTED, PostingStatus.REVERSED)):
        raise HTTPException(400, "Cannot change posted/reversed evidence; review the ledger first")
    references = [IncomeTransaction.payin_id == payin.id]
    if bank:
        references.append(IncomeTransaction.reference_bank_transaction_id == bank.id)
    if db.query(IncomeTransaction.id).filter(or_(*references),
            IncomeTransaction.status != LedgerStatus.REVERSED).first():
        raise HTTPException(400, "Cannot change evidence with an active ledger")


def release_bank_match(db, payin, bank, *, actor_id, reason):
    assert_unposted(db, payin, bank)
    if bank is None:
        return False
    if bank.matched_payin_id != payin.id or payin.matched_statement_txn_id != bank.id:
        conflict()
    bank.matched_payin_id = None
    payin.matched_statement_txn_id = None
    bank.posting_status = PostingStatus.UNMATCHED
    logger.info("PAYIN_MATCH_RELEASE payin=%s bank=%s actor=%s reason=%s",
                payin.id, bank.id, actor_id, reason)
    return True


def validate_evidence(payin, bank, *, require_link=True):
    """Validate fresh locked data before match or any posting entry point.

    Preserves existing matching tolerances. Ledger values always come from bank.
    This does not claim that the image itself has been verified.
    """
    if require_link and (payin.matched_statement_txn_id != bank.id or
                         bank.matched_payin_id != payin.id):
        conflict()
    if not payin.can_be_reviewed():
        raise HTTPException(400, "Pay-in is no longer reviewable")
    if bank.posting_status in (PostingStatus.POSTED, PostingStatus.REVERSED):
        raise HTTPException(400, "Bank transaction is already posted or reversed")
    credit = Decimal(str(bank.credit or 0))
    amount = Decimal(str(payin.amount))
    if credit <= 0 or not amount.is_finite() or amount <= 0:
        raise HTTPException(400, "Only positive credit amounts can be received")
    if not bank.batch or bank.batch.status != 'CONFIRMED':
        raise HTTPException(400, "Statement batch must be confirmed")
    at, bank_at = payin.transfer_datetime, bank.effective_at
    if (abs(credit - amount) > Decimal('0.01') or not at or not bank_at or
            at.tzinfo is None or bank_at.tzinfo is None or
            abs((at - bank_at).total_seconds()) > 60):
        raise HTTPException(400, detail={"code": "EVIDENCE_CHANGED", "message":
            "หลักฐานไม่ตรงกับรายการธนาคารแล้ว กรุณายกเลิกการจับคู่และตรวจใหม่"})


def evidence_values(payin, *, amount=None, transfer_date=None, transfer_hour=None,
                    transfer_minute=None, slip_url=None):
    """Normalize edits before comparing or changing any persistent field."""
    values = {}
    if amount is not None:
        try:
            value = Decimal(str(amount))
            if not value.is_finite() or value <= 0 or value != value.quantize(Decimal('0.01')):
                raise ValueError()
        except (InvalidOperation, ValueError):
            raise HTTPException(400, "Amount must be positive with at most two decimal places")
        values['amount'] = value
    if any(v is not None for v in (transfer_date, transfer_hour, transfer_minute)):
        from dateutil.parser import isoparse
        try:
            at = ensure_utc(payin.transfer_date).astimezone(BANGKOK_TZ)
            if transfer_date is not None:
                parsed = isoparse(transfer_date)
                if len(transfer_date) == 10:
                    at = at.replace(year=parsed.year, month=parsed.month, day=parsed.day)
                else:
                    at = ensure_utc(parsed).astimezone(BANGKOK_TZ)
            if transfer_hour is not None:
                at = at.replace(hour=transfer_hour)
            if transfer_minute is not None:
                at = at.replace(minute=transfer_minute)
            values.update(transfer_date=ensure_utc(at), transfer_hour=at.hour, transfer_minute=at.minute)
        except (ValueError, TypeError, OverflowError):
            raise HTTPException(400, "Invalid transfer date/time")
    if slip_url is not None:
        values['slip_url'] = slip_url
    return values


def apply_evidence_edit(db, payin, bank, values, *, actor_id):
    assert_unposted(db, payin, bank)
    changed = sorted(k for k, v in values.items() if getattr(payin, k) != v)
    if changed:
        release_bank_match(db, payin, bank, actor_id=actor_id,
                           reason='evidence_changed:' + ','.join(changed))
        for key, value in values.items():
            setattr(payin, key, value)
    return changed
