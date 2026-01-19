"""
Bank Statement Transaction Reconciliation API
Match/unmatch bank transactions with payin reports
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import timedelta

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
    3. Pay-in must be in review-eligible state (SUBMITTED or legacy PENDING)
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
    
    # Validation 3: Pay-in must be in review-eligible state (SUBMITTED or legacy PENDING)
    review_eligible_states = [PayinStatus.SUBMITTED, PayinStatus.PENDING]
    if payin.status not in review_eligible_states:
        raise HTTPException(
            status_code=400,
            detail=f"Pay-in must be in review queue (SUBMITTED or PENDING). Current status: {payin.status.value}. Cannot match REJECTED_NEEDS_FIX or ACCEPTED pay-ins."
        )
    
    # Validation 4: Pay-in not already matched
    if payin.matched_statement_txn_id is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Pay-in already matched with bank transaction {payin.matched_statement_txn_id}"
        )
    
    # Validation 5: Amount must match exactly
    amount_diff = abs(float(bank_txn.credit) - float(payin.amount))
    if amount_diff > 0.01:  # More than 1 cent difference
        raise HTTPException(
            status_code=400,
            detail=f"Amount mismatch: Bank ฿{bank_txn.credit} vs Pay-in ฿{payin.amount}. Amounts must match exactly."
        )
    
    # Validation 6: Time tolerance ±1 minute (using transfer_datetime business truth)
    if not payin.transfer_datetime:
        raise HTTPException(
            status_code=400,
            detail="Pay-in transfer_datetime not available"
        )
    
    # Both timestamps should be timezone-aware
    payin_time = payin.transfer_datetime
    bank_time = bank_txn.effective_at
    
    time_diff = abs((payin_time - bank_time).total_seconds())
    if time_diff > 60:  # More than 60 seconds
        raise HTTPException(
            status_code=400,
            detail=f"Time mismatch: Pay-in {payin_time.strftime('%H:%M:%S')} vs Bank {bank_time.strftime('%H:%M:%S')}. Must be within ±1 minute."
        )
    
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


# ===== Get Candidate Transactions for Pay-in (Pay-in Centric UX) =====

@router.get("/candidates/payin/{payin_id}")
async def get_candidate_transactions_for_payin(
    payin_id: int,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Get candidate bank transactions for a specific pay-in (Pay-in Centric Matching)
    
    Returns transactions that match the criteria:
    - CREDIT only (deposits)
    - Unmatched only
    - Amount exactly matches pay-in amount (±0.01 tolerance)
    - Time within ±1 minute of pay-in transfer_datetime
    - Sorted by closest time first (best match at top)
    
    This endpoint supports the Pay-in Centric UX where admin starts from Pay-in Review Queue
    and sees pre-filtered candidates in a single context.
    """
    try:
        # Get pay-in with house relationship
        from app.db.models.house import House
        payin = db.query(PayinReport).filter(PayinReport.id == payin_id).first()
        if not payin:
            raise HTTPException(status_code=404, detail="Pay-in not found")
        
        # Get house info safely
        house_number = "N/A"
        if payin.house_id:
            house = db.query(House).filter(House.id == payin.house_id).first()
            if house:
                house_number = house.house_code  # Use house_code not number
        
        # Ensure pay-in has transfer_datetime
        try:
            payin_time = payin.transfer_datetime
            if not payin_time:
                raise HTTPException(
                    status_code=400,
                    detail="Pay-in transfer_datetime not available"
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot compute transfer_datetime: {str(e)}"
            )
        
        # Get all unmatched credit transactions
        all_unmatched = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.is_(None),
            BankTransaction.credit > 0,
        ).all()
        
        # Filter candidates based on matching criteria
        candidates = []
        payin_amount = float(payin.amount)
        
        for txn in all_unmatched:
            try:
                # Amount must match exactly (±0.01 tolerance)
                txn_amount = float(txn.credit)
                amount_diff = abs(txn_amount - payin_amount)
                if amount_diff > 0.01:
                    continue
                
                # Time must be within ±1 minute
                bank_time = txn.effective_at
                if not bank_time:
                    continue
                
                time_diff_seconds = abs((payin_time - bank_time).total_seconds())
                if time_diff_seconds > 60:
                    continue
                
                # Add to candidates with metadata
                txn_dict = txn.to_dict()
                txn_dict['time_diff_seconds'] = time_diff_seconds
                txn_dict['amount_diff'] = amount_diff
                txn_dict['is_perfect_match'] = amount_diff < 0.01 and time_diff_seconds <= 60
                candidates.append(txn_dict)
            except Exception as e:
                # Skip this transaction if there's any error
                continue
        
        # Sort by time difference (closest first)
        candidates.sort(key=lambda x: x['time_diff_seconds'])
        
        return {
            "payin": {
                "id": payin.id,
                "house_number": house_number,
                "amount": float(payin.amount),
                "transfer_datetime": payin_time.isoformat(),
            },
            "candidates": candidates,
            "count": len(candidates),
            "criteria": {
                "amount_tolerance": "±0.01",
                "time_tolerance": "±1 minute",
                "transaction_type": "CREDIT only",
                "match_status": "unmatched only"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error getting candidates: {str(e)}"
        )
