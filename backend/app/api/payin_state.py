"""
Pay-in State Machine Endpoints
Phase A: State transitions, quality gates, admin-created pay-ins
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from uuid import UUID

from app.db.models.payin_report import PayinReport, PayinStatus, PayinSource
from app.db.models.bank_transaction import BankTransaction
from app.db.models.house import House
from app.db.models.user import User
from app.db.session import get_db
from app.core.deps import require_user, require_admin, require_admin_or_accounting, get_user_house_id

router = APIRouter(prefix="/api/payin-state", tags=["payin-state-machine"])


# ==================== Request/Response Models ====================

class SubmitPayinRequest(BaseModel):
    """Request to submit a draft pay-in for review"""
    pass  # No additional fields needed


class RejectPayinRequest(BaseModel):
    """Request to reject a pay-in"""
    reason: str
    reason_code: Optional[str] = None  # e.g., WRONG_AMOUNT, WRONG_DATE, UNREADABLE_SLIP


class AdminCreateFromBankRequest(BaseModel):
    """Request to create pay-in from unidentified bank transaction"""
    bank_transaction_id: str  # UUID as string
    house_id: int
    note: Optional[str] = None
    source: Optional[str] = "ADMIN_CREATED"  # ADMIN_CREATED or LINE_RECEIVED


REJECTION_REASONS = [
    {"code": "WRONG_AMOUNT", "label": "จำนวนเงินไม่ตรง / Amount mismatch"},
    {"code": "WRONG_DATE", "label": "วันที่/เวลาไม่ตรง / Date/time mismatch"},
    {"code": "UNREADABLE_SLIP", "label": "สลิปไม่ชัด / Unreadable slip"},
    {"code": "DUPLICATE", "label": "ซ้ำกับรายการอื่น / Duplicate entry"},
    {"code": "WRONG_ACCOUNT", "label": "โอนผิดบัญชี / Wrong bank account"},
    {"code": "OTHER", "label": "อื่นๆ / Other"},
]


# ==================== State Machine Endpoints ====================

@router.get("/rejection-reasons")
async def get_rejection_reasons():
    """Get list of preset rejection reasons for admin UI"""
    return {"reasons": REJECTION_REASONS}


@router.post("/{payin_id}/submit")
async def submit_payin_for_review(
    payin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    """
    Submit a DRAFT or REJECTED_NEEDS_FIX pay-in for admin review.
    Quality gate: validates required fields before submission.
    
    Transitions: DRAFT → SUBMITTED, REJECTED_NEEDS_FIX → SUBMITTED
    """
    payin = db.query(PayinReport).options(
        joinedload(PayinReport.house)
    ).filter(PayinReport.id == payin_id).first()
    
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Access control: residents can only submit their own
    if current_user.role == "resident":
        if user_house_id != payin.house_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # State validation
    if not payin.can_be_submitted():
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit pay-in in {payin.status.value} state. Only DRAFT or REJECTED_NEEDS_FIX can be submitted."
        )
    
    # Quality gate: validate required fields
    errors = payin.validate_for_submission()
    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_FAILED",
                "message": "Pay-in failed quality gate validation",
                "errors": errors
            }
        )
    
    # Transition to SUBMITTED
    payin.status = PayinStatus.SUBMITTED
    payin.submitted_at = datetime.now(timezone.utc)
    payin.rejection_reason = None  # Clear previous rejection reason
    
    db.commit()
    db.refresh(payin)
    
    return {
        "message": "Pay-in submitted for review",
        "payin": payin.to_dict()
    }


@router.post("/{payin_id}/reject")
async def reject_payin_needs_fix(
    payin_id: int,
    request: RejectPayinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Reject a pay-in and request resident to fix it.
    
    Transitions: SUBMITTED/PENDING → REJECTED_NEEDS_FIX
    """
    payin = db.query(PayinReport).options(
        joinedload(PayinReport.house)
    ).filter(PayinReport.id == payin_id).first()
    
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # State validation
    if not payin.can_be_reviewed():
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject pay-in in {payin.status.value} state. Only SUBMITTED/PENDING can be rejected."
        )
    
    if not request.reason or not request.reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is required")
    
    # Build rejection message
    rejection_text = request.reason
    if request.reason_code:
        # Find label for reason code
        reason_label = next(
            (r["label"] for r in REJECTION_REASONS if r["code"] == request.reason_code),
            None
        )
        if reason_label:
            rejection_text = f"[{request.reason_code}] {reason_label}: {request.reason}"
    
    # Transition to REJECTED_NEEDS_FIX
    payin.status = PayinStatus.REJECTED_NEEDS_FIX
    payin.rejection_reason = rejection_text
    
    db.commit()
    db.refresh(payin)
    
    return {
        "message": "Pay-in rejected and sent back for fixing",
        "payin": payin.to_dict()
    }


@router.post("/{payin_id}/save-draft")
async def save_payin_draft(
    payin_id: int,
    amount: Optional[float] = Form(None),
    transfer_date: Optional[str] = Form(None),
    transfer_hour: Optional[int] = Form(None),
    transfer_minute: Optional[int] = Form(None),
    slip: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    """
    Save changes to a pay-in in DRAFT or REJECTED_NEEDS_FIX state.
    Does NOT submit - just saves the edits.
    """
    payin = db.query(PayinReport).options(
        joinedload(PayinReport.house)
    ).filter(PayinReport.id == payin_id).first()
    
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Access control
    if current_user.role == "resident":
        if user_house_id != payin.house_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # State validation
    if not payin.can_be_edited():
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit pay-in in {payin.status.value} state. Only DRAFT or REJECTED_NEEDS_FIX can be edited."
        )
    
    # Update fields if provided
    if amount is not None:
        payin.amount = amount
    
    if transfer_date is not None:
        from dateutil import parser as date_parser
        try:
            payin.transfer_date = date_parser.isoparse(transfer_date)
        except:
            raise HTTPException(status_code=400, detail="Invalid transfer_date format")
    
    if transfer_hour is not None:
        if not 0 <= transfer_hour <= 23:
            raise HTTPException(status_code=400, detail="transfer_hour must be 0-23")
        payin.transfer_hour = transfer_hour
    
    if transfer_minute is not None:
        if not 0 <= transfer_minute <= 59:
            raise HTTPException(status_code=400, detail="transfer_minute must be 0-59")
        payin.transfer_minute = transfer_minute
    
    if slip:
        # Handle file upload (mock for now)
        payin.slip_url = f"https://example.com/slips/{slip.filename}"
    
    db.commit()
    db.refresh(payin)
    
    return {
        "message": "Pay-in draft saved",
        "payin": payin.to_dict()
    }


# ==================== Admin-Created Pay-in from Bank ====================

@router.get("/unidentified-bank-credits")
async def list_unidentified_bank_credits(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    List unmatched CREDIT bank transactions (unidentified receipts).
    These are money received in bank but no pay-in report exists.
    Admin can create pay-in from these.
    """
    # Find CREDIT transactions that are not matched to any pay-in
    unidentified = db.query(BankTransaction).filter(
        and_(
            BankTransaction.credit.isnot(None),
            BankTransaction.credit > 0,
            BankTransaction.matched_payin_id.is_(None)
        )
    ).order_by(BankTransaction.effective_at.desc()).limit(limit).all()
    
    return {
        "count": len(unidentified),
        "transactions": [
            {
                "id": str(txn.id),
                "effective_at": txn.effective_at.isoformat() if txn.effective_at else None,
                "amount": float(txn.credit) if txn.credit else 0,
                "description": txn.description,
                "channel": txn.channel,
                "bank_account_id": str(txn.bank_account_id),
                "created_at": txn.created_at.isoformat() if txn.created_at else None
            }
            for txn in unidentified
        ]
    }


@router.post("/admin-create-from-bank")
async def admin_create_payin_from_bank(
    request: AdminCreateFromBankRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Admin creates a pay-in from an unidentified bank CREDIT transaction.
    
    Use case: Money received in bank but resident never submitted pay-in
    (e.g., sent slip via LINE instead).
    
    This creates a pay-in with:
    - source = ADMIN_CREATED or LINE_RECEIVED
    - status = SUBMITTED (ready for normal review flow)
    - Auto-matched to the bank transaction
    """
    # Validate bank transaction
    try:
        bank_txn_uuid = UUID(request.bank_transaction_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid bank_transaction_id format")
    
    bank_txn = db.query(BankTransaction).filter(
        BankTransaction.id == bank_txn_uuid
    ).first()
    
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    
    # Validate it's a CREDIT
    if not bank_txn.credit or float(bank_txn.credit) <= 0:
        raise HTTPException(
            status_code=400,
            detail="Bank transaction must be a CREDIT (deposit)"
        )
    
    # Validate it's not already matched
    if bank_txn.matched_payin_id is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Bank transaction already matched to pay-in #{bank_txn.matched_payin_id}"
        )
    
    # Check if pay-in already exists for this bank transaction (via reference)
    existing = db.query(PayinReport).filter(
        PayinReport.reference_bank_transaction_id == bank_txn_uuid
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Pay-in #{existing.id} already created from this bank transaction"
        )
    
    # Validate house
    house = db.query(House).filter(House.id == request.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Determine source
    source = PayinSource.LINE_RECEIVED if request.source == "LINE_RECEIVED" else PayinSource.ADMIN_CREATED
    
    # Create pay-in
    new_payin = PayinReport(
        house_id=request.house_id,
        submitted_by_user_id=None,  # No resident submitted
        amount=bank_txn.credit,
        transfer_date=bank_txn.effective_at,
        transfer_hour=bank_txn.effective_at.hour if bank_txn.effective_at else 0,
        transfer_minute=bank_txn.effective_at.minute if bank_txn.effective_at else 0,
        slip_url=None,
        status=PayinStatus.SUBMITTED,  # Ready for review
        source=source,
        created_by_admin_id=current_user.id,
        admin_note=request.note,
        reference_bank_transaction_id=bank_txn_uuid,
        submitted_at=datetime.now(timezone.utc)
    )
    
    db.add(new_payin)
    db.flush()  # Get payin.id
    
    # Auto-match: Link bank transaction to this pay-in
    bank_txn.matched_payin_id = new_payin.id
    new_payin.matched_statement_txn_id = bank_txn.id
    
    db.commit()
    db.refresh(new_payin)
    
    return {
        "message": "Pay-in created from bank transaction",
        "payin": new_payin.to_dict(),
        "auto_matched": True,
        "note": "Pay-in is auto-matched to bank transaction. Proceed to Accept to create ledger."
    }


@router.post("/{payin_id}/attach-slip")
async def attach_slip_to_payin(
    payin_id: int,
    slip: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Attach slip image to an existing pay-in (typically admin-created).
    Used when admin receives slip via LINE and wants to attach as evidence.
    """
    payin = db.query(PayinReport).filter(PayinReport.id == payin_id).first()
    
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Only allow attaching to non-accepted pay-ins
    if payin.status == PayinStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify accepted pay-in"
        )
    
    # Handle file upload (mock for now, Phase 2+ use S3)
    slip_url = f"https://example.com/slips/{slip.filename}"
    payin.slip_url = slip_url
    
    db.commit()
    db.refresh(payin)
    
    return {
        "message": "Slip attached successfully",
        "payin_id": payin_id,
        "slip_url": slip_url
    }


# ==================== Query Endpoints for Admin UI ====================

@router.get("/review-queue")
async def get_review_queue(
    status_filter: Optional[str] = None,  # SUBMITTED, REJECTED_NEEDS_FIX, ACCEPTED
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Get pay-ins organized for admin review.
    Returns counts and lists by status.
    """
    # Count by status
    submitted_count = db.query(PayinReport).filter(
        PayinReport.status.in_([PayinStatus.SUBMITTED, PayinStatus.PENDING])
    ).count()
    
    needs_fix_count = db.query(PayinReport).filter(
        PayinReport.status.in_([PayinStatus.REJECTED_NEEDS_FIX, PayinStatus.REJECTED])
    ).count()
    
    accepted_count = db.query(PayinReport).filter(
        PayinReport.status == PayinStatus.ACCEPTED
    ).count()
    
    draft_count = db.query(PayinReport).filter(
        PayinReport.status == PayinStatus.DRAFT
    ).count()
    
    # Build query based on filter
    query = db.query(PayinReport).options(
        joinedload(PayinReport.house),
        joinedload(PayinReport.submitted_by),
        joinedload(PayinReport.created_by_admin)
    )
    
    if status_filter:
        if status_filter == "NEEDS_REVIEW":
            query = query.filter(PayinReport.status.in_([PayinStatus.SUBMITTED, PayinStatus.PENDING]))
        elif status_filter == "NEEDS_FIX":
            query = query.filter(PayinReport.status.in_([PayinStatus.REJECTED_NEEDS_FIX, PayinStatus.REJECTED]))
        elif status_filter == "ACCEPTED":
            query = query.filter(PayinReport.status == PayinStatus.ACCEPTED)
        elif status_filter == "DRAFT":
            query = query.filter(PayinReport.status == PayinStatus.DRAFT)
    
    payins = query.order_by(PayinReport.created_at.desc()).limit(100).all()
    
    return {
        "counts": {
            "needs_review": submitted_count,
            "needs_fix": needs_fix_count,
            "accepted": accepted_count,
            "draft": draft_count,
            "total": submitted_count + needs_fix_count + accepted_count + draft_count
        },
        "payins": [p.to_dict() for p in payins]
    }
