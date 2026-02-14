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
from app.db.models.bank_transaction import BankTransaction, PostingStatus
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
    
    # Phase P1: Update posting status
    bank_txn.posting_status = PostingStatus.MATCHED
    
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
    
    # Phase P1: Reset posting status
    bank_txn.posting_status = PostingStatus.UNMATCHED
    
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


# ===== Phase P1: Confirm & Post (Statement-Driven Atomic Flow) =====

class ConfirmPostRequest(BaseModel):
    """Optional: specify target invoice for ambiguous cases"""
    invoice_id: Optional[int] = None


class ReverseRequest(BaseModel):
    reason: str


@router.post("/transactions/{txn_id}/confirm-and-post")
async def confirm_and_post(
    txn_id: str,
    data: Optional[ConfirmPostRequest] = None,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Atomic Confirm & Post: Statement → Ledger → Invoice allocation in 1 click.
    
    Flow:
    1. Lock bank transaction row (SELECT FOR UPDATE)
    2. Idempotency: if already POSTED, return existing result
    3. Detect exact-match invoice (or use specified invoice_id)
    4. Create IncomeTransaction (ledger)
    5. FIFO allocate to invoice(s)
    6. Update invoice status
    7. Set posting_status = POSTED
    8. If matched pay-in exists, set status = ACCEPTED
    
    Guards:
    - Only CREDIT transactions
    - Must be MATCHED or UNMATCHED (not already POSTED/REVERSED)
    - Auto only when exact match (1 invoice, exact amount)
    - Returns 409 AMBIGUOUS if multiple candidates
    """
    from app.db.models.income_transaction import IncomeTransaction, LedgerStatus
    from app.db.models.invoice_payment import InvoicePayment
    from app.db.models.invoice import Invoice, InvoiceStatus
    from app.db.models.house import House
    from app.db.models.payin_report import PayinReport, PayinStatus as PayinStatusEnum
    from datetime import datetime
    
    # Parse UUID
    try:
        txn_uuid = uuid.UUID(txn_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")
    
    # 1. Lock row (SELECT FOR UPDATE)
    bank_txn = db.query(BankTransaction).filter(
        BankTransaction.id == txn_uuid
    ).with_for_update().first()
    
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    
    # Must be CREDIT
    if not bank_txn.credit or bank_txn.credit <= 0:
        raise HTTPException(status_code=400, detail="Only CREDIT transactions can be posted")
    
    # 2. Idempotency: already POSTED → return existing result
    if bank_txn.posting_status == PostingStatus.POSTED:
        existing_ledger = db.query(IncomeTransaction).filter(
            IncomeTransaction.reference_bank_transaction_id == txn_uuid
        ).first()
        return {
            "status": "already_posted",
            "message": "Transaction already posted (idempotent)",
            "bank_transaction_id": txn_id,
            "income_transaction_id": existing_ledger.id if existing_ledger else None,
            "posting_status": "POSTED",
        }
    
    # Cannot post REVERSED transactions
    if bank_txn.posting_status == PostingStatus.REVERSED:
        raise HTTPException(
            status_code=400,
            detail="Cannot post a reversed transaction. Create a new transaction instead."
        )
    
    # 3. Detect target house and invoice
    amount = float(bank_txn.credit)
    target_house_id = None
    target_invoice = None
    payin = None
    
    # If matched with pay-in, use pay-in's house
    if bank_txn.matched_payin_id:
        payin = db.query(PayinReport).filter(
            PayinReport.id == bank_txn.matched_payin_id
        ).first()
        if payin:
            target_house_id = payin.house_id
    
    if not target_house_id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "AMBIGUOUS",
                "message": "ไม่สามารถระบุบ้านได้ กรุณา Match กับ Pay-in ก่อน หรือระบุ invoice_id",
            }
        )
    
    # Find target invoice
    if data and data.invoice_id:
        # Admin specified which invoice
        target_invoice = db.query(Invoice).filter(
            Invoice.id == data.invoice_id,
            Invoice.house_id == target_house_id,
        ).first()
        if not target_invoice:
            raise HTTPException(status_code=404, detail="Specified invoice not found for this house")
        if target_invoice.get_outstanding_amount() <= 0:
            raise HTTPException(status_code=400, detail="Specified invoice is already fully paid")
    else:
        # Auto-detect: exact match only
        outstanding_invoices = db.query(Invoice).filter(
            Invoice.house_id == target_house_id,
            Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID]),
        ).order_by(Invoice.due_date.asc()).all()
        
        # Filter to only those with actual outstanding balance
        outstanding_invoices = [inv for inv in outstanding_invoices if inv.get_outstanding_amount() > 0]
        
        if not outstanding_invoices:
            # No outstanding invoice — still post the ledger, but skip allocation
            pass
        elif len(outstanding_invoices) == 1 and abs(outstanding_invoices[0].get_outstanding_amount() - amount) < 0.01:
            # EXACT MATCH: 1 invoice, exact amount
            target_invoice = outstanding_invoices[0]
        else:
            # AMBIGUOUS or partial — do FIFO allocation across invoices
            # Phase 1: Only auto-allocate if total outstanding >= amount (no overpay)
            total_outstanding = sum(inv.get_outstanding_amount() for inv in outstanding_invoices)
            if total_outstanding >= amount:
                # FIFO across multiple invoices — this is safe
                target_invoice = "FIFO"  # sentinel
            else:
                # Overpayment scenario — still post ledger, allocate what we can
                target_invoice = "FIFO"
    
    # 4. ATOMIC TRANSACTION: Create ledger + allocate + update status
    try:
        # Create IncomeTransaction (ledger entry)
        income_txn = IncomeTransaction(
            house_id=target_house_id,
            payin_id=payin.id if payin else None,
            reference_bank_transaction_id=bank_txn.id,
            amount=amount,
            received_at=bank_txn.effective_at,
            status=LedgerStatus.POSTED,
        )
        db.add(income_txn)
        db.flush()  # Get income_txn.id
        
        # 5. FIFO Allocation
        allocations = []
        if target_invoice == "FIFO":
            # Re-query for FIFO
            fifo_invoices = db.query(Invoice).filter(
                Invoice.house_id == target_house_id,
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID]),
            ).order_by(Invoice.due_date.asc()).all()
            
            remaining = amount
            for inv in fifo_invoices:
                if remaining <= 0:
                    break
                outstanding = inv.get_outstanding_amount()
                if outstanding <= 0:
                    continue
                alloc_amount = min(remaining, outstanding)
                payment = InvoicePayment(
                    invoice_id=inv.id,
                    income_transaction_id=income_txn.id,
                    amount=alloc_amount,
                )
                db.add(payment)
                db.flush()
                db.refresh(inv)
                inv.update_status()
                allocations.append({
                    "invoice_id": inv.id,
                    "amount": alloc_amount,
                    "new_status": inv.status.value,
                })
                remaining -= alloc_amount
                
        elif target_invoice and target_invoice != "FIFO":
            # Single invoice exact match
            alloc_amount = min(amount, target_invoice.get_outstanding_amount())
            payment = InvoicePayment(
                invoice_id=target_invoice.id,
                income_transaction_id=income_txn.id,
                amount=alloc_amount,
            )
            db.add(payment)
            db.flush()
            db.refresh(target_invoice)
            target_invoice.update_status()
            allocations.append({
                "invoice_id": target_invoice.id,
                "amount": alloc_amount,
                "new_status": target_invoice.status.value,
            })
        
        # 6. Update bank transaction posting_status
        bank_txn.posting_status = PostingStatus.POSTED
        
        # 7. If matched pay-in, set to ACCEPTED
        if payin:
            payin.status = PayinStatusEnum.ACCEPTED
            payin.accepted_by = current_user.id
            payin.accepted_at = datetime.now()
        
        db.commit()
        db.refresh(income_txn)
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm and post: {str(e)}"
        )
    
    return {
        "status": "posted",
        "message": f"Posted ฿{amount:,.2f} → House {target_house_id}, {len(allocations)} invoice(s) allocated",
        "bank_transaction_id": txn_id,
        "income_transaction_id": income_txn.id,
        "posting_status": "POSTED",
        "house_id": target_house_id,
        "amount": amount,
        "allocations": allocations,
        "payin_id": payin.id if payin else None,
        "payin_accepted": payin is not None,
    }


# ===== Phase P1: Reverse Endpoint =====

@router.post("/transactions/{txn_id}/reverse")
async def reverse_posted_transaction(
    txn_id: str,
    data: ReverseRequest,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Reverse a POSTED transaction: compensating state change (no hard delete).
    
    Flow:
    1. Lock bank transaction
    2. Find IncomeTransaction → mark REVERSED
    3. Find InvoicePayments → mark REVERSED
    4. Recalc invoice status for each affected invoice
    5. Set posting_status = REVERSED
    6. If linked pay-in, revert to SUBMITTED
    """
    from app.db.models.income_transaction import IncomeTransaction, LedgerStatus
    from app.db.models.invoice_payment import InvoicePayment, PaymentStatus
    from app.db.models.invoice import Invoice
    from app.db.models.payin_report import PayinReport, PayinStatus as PayinStatusEnum
    from datetime import datetime
    
    if not data.reason or not data.reason.strip():
        raise HTTPException(status_code=400, detail="Reverse reason is required")
    
    # Parse UUID
    try:
        txn_uuid = uuid.UUID(txn_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")
    
    # 1. Lock row
    bank_txn = db.query(BankTransaction).filter(
        BankTransaction.id == txn_uuid
    ).with_for_update().first()
    
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    
    if bank_txn.posting_status != PostingStatus.POSTED:
        raise HTTPException(
            status_code=400,
            detail=f"Can only reverse POSTED transactions (current: {bank_txn.posting_status.value})"
        )
    
    try:
        # 2. Find IncomeTransaction
        income_txn = db.query(IncomeTransaction).filter(
            IncomeTransaction.reference_bank_transaction_id == txn_uuid
        ).first()
        
        reversed_invoices = []
        
        if income_txn:
            # 3. Mark all InvoicePayments as REVERSED
            payments = db.query(InvoicePayment).filter(
                InvoicePayment.income_transaction_id == income_txn.id,
                InvoicePayment.status == PaymentStatus.ACTIVE,
            ).all()
            
            affected_invoice_ids = set()
            for payment in payments:
                payment.status = PaymentStatus.REVERSED
                affected_invoice_ids.add(payment.invoice_id)
            
            # 4. Recalc invoice status
            for inv_id in affected_invoice_ids:
                invoice = db.query(Invoice).filter(Invoice.id == inv_id).first()
                if invoice:
                    db.flush()
                    db.refresh(invoice)
                    invoice.update_status()
                    reversed_invoices.append({
                        "invoice_id": inv_id,
                        "new_status": invoice.status.value,
                    })
            
            # Mark IncomeTransaction as REVERSED
            income_txn.status = LedgerStatus.REVERSED
            income_txn.reversed_at = datetime.now()
            income_txn.reversed_by = current_user.id
            income_txn.reverse_reason = data.reason.strip()
        
        # 5. Set posting_status = REVERSED
        bank_txn.posting_status = PostingStatus.REVERSED
        
        # 6. Revert matched pay-in to SUBMITTED
        if bank_txn.matched_payin_id:
            payin = db.query(PayinReport).filter(
                PayinReport.id == bank_txn.matched_payin_id
            ).first()
            if payin and payin.status == PayinStatusEnum.ACCEPTED:
                payin.status = PayinStatusEnum.SUBMITTED
                payin.accepted_by = None
                payin.accepted_at = None
        
        db.commit()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reverse: {str(e)}"
        )
    
    return {
        "status": "reversed",
        "message": f"Transaction reversed: {data.reason}",
        "bank_transaction_id": txn_id,
        "posting_status": "REVERSED",
        "income_transaction_id": income_txn.id if income_txn else None,
        "reversed_invoices": reversed_invoices,
        "reason": data.reason.strip(),
    }
