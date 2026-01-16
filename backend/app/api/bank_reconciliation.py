"""
Bank Statement Transaction Reconciliation API
Match/unmatch bank transactions with payin reports
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.db.models.user import User
from app.db.models.bank_transaction import BankTransaction
from app.db.models.payin_report import PayinReport, PayinStatus


router = APIRouter(prefix="/api/bank-statements", tags=["bank-reconciliation"])


# ===== Request/Response Models =====

class MatchRequest(BaseModel):
    payin_id: int


class MatchResponse(BaseModel):
    success: bool
    message: str
    bank_transaction_id: str
    payin_id: int


# ===== Match Endpoint =====

@router.post("/transactions/{txn_id}/match", response_model=MatchResponse)
async def match_transaction_with_payin(
    txn_id: str,
    data: MatchRequest,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Match a bank transaction with a pay-in report (1:1)
    
    Validation rules:
    1. Transaction must be CREDIT > 0 (not debit)
    2. Transaction must not be already matched
    3. Pay-in must be PENDING status
    4. Pay-in must not be already matched
    5. Amounts should match (warning if different)
    """
    # Parse UUID
    try:
        txn_uuid = uuid.UUID(txn_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")
    
    # Get bank transaction
    bank_txn = db.query(BankTransaction).filter(BankTransaction.id == txn_uuid).first()
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    
    # Validation 1: Must be CREDIT transaction
    if not bank_txn.credit or bank_txn.credit <= 0:
        raise HTTPException(
            status_code=400,
            detail="Only credit transactions (deposits) can be matched with pay-ins"
        )
    
    # Validation 2: Transaction not already matched
    if bank_txn.matched_payin_id is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Transaction already matched with pay-in ID {bank_txn.matched_payin_id}"
        )
    
    # Get pay-in report
    payin = db.query(PayinReport).filter(PayinReport.id == data.payin_id).first()
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Validation 3: Pay-in must be PENDING
    if payin.status != PayinStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Pay-in must be PENDING status (current: {payin.status.value}). Rejected pay-ins cannot be matched."
        )
    
    # Validation 4: Pay-in not already matched
    if payin.matched_statement_txn_id is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Pay-in already matched with bank transaction {payin.matched_statement_txn_id}"
        )
    
    # Validation 5: Amount warning (soft check)
    amount_diff = abs(float(bank_txn.credit) - float(payin.amount))
    if amount_diff > 0.01:  # More than 1 cent difference
        # Log warning but allow match
        print(f"⚠️ WARNING: Amount mismatch - Bank: {bank_txn.credit}, Pay-in: {payin.amount}")
    
    # Perform 1:1 match (both sides)
    bank_txn.matched_payin_id = payin.id
    payin.matched_statement_txn_id = bank_txn.id
    
    db.commit()
    
    return MatchResponse(
        success=True,
        message=f"Successfully matched bank transaction {txn_id} with pay-in {payin.id}",
        bank_transaction_id=txn_id,
        payin_id=payin.id,
    )


# ===== Unmatch Endpoint =====

@router.post("/transactions/{txn_id}/unmatch")
async def unmatch_transaction(
    txn_id: str,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Remove match between bank transaction and pay-in report
    
    Validation:
    - Cannot unmatch if pay-in has been ACCEPTED (ledger already created)
    """
    # Parse UUID
    try:
        txn_uuid = uuid.UUID(txn_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")
    
    # Get bank transaction
    bank_txn = db.query(BankTransaction).filter(BankTransaction.id == txn_uuid).first()
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    
    # Check if matched
    if bank_txn.matched_payin_id is None:
        raise HTTPException(status_code=400, detail="Transaction is not matched")
    
    # Get matched pay-in
    payin = db.query(PayinReport).filter(PayinReport.id == bank_txn.matched_payin_id).first()
    if not payin:
        # Orphaned match - clean up
        bank_txn.matched_payin_id = None
        db.commit()
        return {"success": True, "message": "Cleaned up orphaned match"}
    
    # Validation: Cannot unmatch ACCEPTED pay-in (ledger exists)
    if payin.status == PayinStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot unmatch accepted pay-in. Ledger has been created. Please reject/reverse the ledger entry first."
        )
    
    # Remove match from both sides
    payin_id = payin.id
    bank_txn.matched_payin_id = None
    payin.matched_statement_txn_id = None
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Successfully unmatched bank transaction {txn_id} from pay-in {payin_id}",
        "bank_transaction_id": txn_id,
        "payin_id": payin_id,
    }


# ===== List Unmatched Transactions (for UI) =====

@router.get("/transactions/unmatched")
async def list_unmatched_credit_transactions(
    batch_id: Optional[str] = None,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    List all unmatched CREDIT transactions (for reconciliation UI)
    Filter by batch_id if provided
    """
    query = db.query(BankTransaction).filter(
        BankTransaction.matched_payin_id.is_(None),
        BankTransaction.credit > 0,  # Only credits
    )
    
    if batch_id:
        try:
            batch_uuid = uuid.UUID(batch_id)
            query = query.filter(BankTransaction.bank_statement_batch_id == batch_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid batch ID format")
    
    transactions = query.order_by(BankTransaction.effective_at.desc()).all()
    
    return {
        "items": [txn.to_dict() for txn in transactions],
        "count": len(transactions),
    }
