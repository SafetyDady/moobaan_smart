from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from app.models import (
    PayInReport as PayInReportSchema, PayInReportCreate, PayInReportUpdate,
    RejectPayInRequest, PayInStatus
)
from app.db.models.payin_report import PayinReport as PayinReportModel, PayinStatus as PayinStatusEnum, PayinSource
from app.db.models.house import House as HouseModel
from app.db.models.user import User
from app.db.models.income_transaction import IncomeTransaction
from app.db.session import get_db
from app.core.deps import require_user, require_admin, require_admin_or_accounting, get_user_house_id

router = APIRouter(prefix="/api/payin-reports", tags=["payin-reports"])


@router.get("", response_model=List[dict])
async def list_payin_reports(
    house_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    """List all pay-in reports with role-based filtering"""
    query = db.query(PayinReportModel).options(joinedload(PayinReportModel.house))
    
    # Role-based filtering
    if current_user.role == "resident":
        # Residents can only see their own house's payins
        if user_house_id is None:
            raise HTTPException(status_code=403, detail="Resident not linked to any house")
        query = query.filter(PayinReportModel.house_id == user_house_id)
    elif current_user.role in ["accounting", "super_admin"]:
        # Admin/accounting can filter by house_id or see all
        if house_id:
            query = query.filter(PayinReportModel.house_id == house_id)
    
    if status:
        query = query.filter(PayinReportModel.status == status)
    
    payins = query.order_by(PayinReportModel.created_at.desc()).all()
    
    return [{
        "id": payin.id,
        "house_id": payin.house_id,
        "house_number": payin.house.house_code,
        "amount": float(payin.amount),
        "transfer_date": payin.transfer_date,
        "transfer_hour": payin.transfer_hour,
        "transfer_minute": payin.transfer_minute,
        "slip_image_url": payin.slip_url,  # Map database field to frontend expectation
        "status": payin.status.value if hasattr(payin.status, 'value') else payin.status,
        "display_status": PayinReportModel.get_display_status(payin.status),
        "reject_reason": payin.rejection_reason,
        "matched_statement_txn_id": str(payin.matched_statement_txn_id) if payin.matched_statement_txn_id else None,
        "is_matched": payin.matched_statement_txn_id is not None,
        "source": payin.source.value if payin.source else "RESIDENT",
        "created_by_admin_id": payin.created_by_admin_id,
        "admin_note": payin.admin_note,
        "can_edit": payin.can_be_edited(),
        "can_submit": payin.can_be_submitted(),
        "created_at": payin.created_at,
        "updated_at": payin.updated_at
    } for payin in payins]


@router.get("/{payin_id}", response_model=dict)
async def get_payin_report(
    payin_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    """Get a specific pay-in report by ID with role-based access"""
    payin = db.query(PayinReportModel).options(
        joinedload(PayinReportModel.house)
    ).filter(PayinReportModel.id == payin_id).first()
    
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Role-based access control
    if current_user.role == "resident":
        if user_house_id != payin.house_id:
            raise HTTPException(status_code=403, detail="Access denied to this house's data")
    
    return {
        "id": payin.id,
        "house_id": payin.house_id,
        "house_number": payin.house.house_code,
        "amount": float(payin.amount),
        "transfer_date": payin.transfer_date,
        "transfer_hour": payin.transfer_hour,
        "transfer_minute": payin.transfer_minute,
        "slip_image_url": payin.slip_url,  # Map database field to frontend expectation
        "status": payin.status,
        "reject_reason": payin.rejection_reason,

        "created_at": payin.created_at,
        "updated_at": payin.updated_at
    }


@router.post("", response_model=dict, status_code=201)
async def create_payin_report(
    amount: float = Form(...),
    paid_at: str = Form(...),
    slip: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    """Create a new pay-in report (resident submits proof of payment)"""
    try:
        # Only residents can create payins, and only for their own house
        if current_user.role != "resident":
            raise HTTPException(status_code=403, detail="Only residents can create pay-in reports")
        
        if user_house_id is None:
            raise HTTPException(status_code=403, detail="Resident not linked to any house")
        
        # Check house exists
        house = db.query(HouseModel).filter(HouseModel.id == user_house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="House not found")
        
        # Single-open rule: Block create if there's any open pay-in
        # Per A.1.2 spec: DRAFT, PENDING, REJECTED_NEEDS_FIX, SUBMITTED all block new creation
        # User must complete or delete existing before creating new
        blocking_statuses = ["DRAFT", "PENDING", "REJECTED_NEEDS_FIX", "SUBMITTED"]
        existing_incomplete = db.query(PayinReportModel).filter(
            PayinReportModel.house_id == user_house_id,
            PayinReportModel.status.in_(blocking_statuses)
        ).first()
        
        if existing_incomplete:
            status_value = existing_incomplete.status.value if hasattr(existing_incomplete.status, 'value') else str(existing_incomplete.status)
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "PAYIN_ALREADY_OPEN",
                    "message": "คุณมีรายการที่ยังไม่เสร็จ กรุณาดำเนินการให้เสร็จก่อน",
                    "existing_payin_id": existing_incomplete.id,
                    "existing_status": status_value,
                    "created_at": existing_incomplete.created_at.isoformat() if existing_incomplete.created_at else None
                }
            )
        
        # Validate amount
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        # Parse paid_at (ISO datetime string)
        from dateutil import parser as date_parser
        try:
            paid_at_datetime = date_parser.isoparse(paid_at)
            
            # Debug logging
            print(f"🔍 DEBUG - Received paid_at: {paid_at}")
            print(f"🔍 DEBUG - Parsed datetime: {paid_at_datetime}")
            print(f"🔍 DEBUG - Hour: {paid_at_datetime.hour}, Minute: {paid_at_datetime.minute}")
            print(f"🔍 DEBUG - Timezone info: {paid_at_datetime.tzinfo}")
            
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid paid_at format: {str(e)}")
        
        # Handle slip file upload (mock for Phase 1)
        slip_url = None
        if slip:
            # Phase 1: Generate mock URL from filename
            slip_url = f"https://example.com/slips/{slip.filename}"
            # Phase 2+: Upload to S3 and get real URL
        
        new_payin = PayinReportModel(
            house_id=user_house_id,
            submitted_by_user_id=current_user.id,
            amount=amount,
            transfer_date=paid_at_datetime,
            transfer_hour=paid_at_datetime.hour,
            transfer_minute=paid_at_datetime.minute,
            slip_url=slip_url,
            status=PayinStatusEnum.PENDING,  # PENDING = editable by resident until admin reviews
            source=PayinSource.RESIDENT,
            rejection_reason=None,
            accepted_by=None,
            accepted_at=None,
            submitted_at=datetime.now()
        )
        
        db.add(new_payin)
        db.commit()
        db.refresh(new_payin)
        
        return {
            "id": new_payin.id,
            "house_id": new_payin.house_id,
            "house_number": house.house_code,  # Use house_code not house_no
            "amount": float(new_payin.amount),
            "transfer_date": new_payin.transfer_date.isoformat() if new_payin.transfer_date else None,
            "transfer_hour": new_payin.transfer_hour,
            "transfer_minute": new_payin.transfer_minute,
            "slip_image_url": new_payin.slip_url,
            "status": new_payin.status.value if hasattr(new_payin.status, 'value') else new_payin.status,
            "rejection_reason": new_payin.rejection_reason,
            "created_at": new_payin.created_at.isoformat() if new_payin.created_at else None,
            "updated_at": new_payin.updated_at.isoformat() if new_payin.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ ERROR in create_payin_report: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.put("/{payin_id}", response_model=dict)
async def update_payin_report(
    payin_id: int, 
    payin: PayInReportUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    """Update a pay-in report
    
    Per A.1.2 spec - Editable statuses:
    - DRAFT: edit ✅
    - PENDING: edit ✅ (can edit but not delete)
    - REJECTED_NEEDS_FIX: edit ✅
    """
    import logging
    logger = logging.getLogger(__name__)
    
    existing = db.query(PayinReportModel).options(
        joinedload(PayinReportModel.house)
    ).filter(PayinReportModel.id == payin_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Ownership check for residents
    if current_user.role == "resident":
        if user_house_id != existing.house_id:
            raise HTTPException(status_code=403, detail="Access denied to this house's data")
    
    # Only allow update when can be edited
    if not existing.can_be_edited():
        status_value = existing.status.value if hasattr(existing.status, 'value') else str(existing.status)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CANNOT_EDIT",
                "message": f"ไม่สามารถแก้ไขรายการสถานะ {status_value} ได้",
                "status": status_value
            }
        )
    
    logger.info(f"Updating payin {payin_id} by user {current_user.id}, current status={existing.status}")
    
    # Update fields if provided
    if payin.amount is not None:
        existing.amount = payin.amount
    if payin.transfer_date is not None:
        existing.transfer_date = payin.transfer_date
    if payin.transfer_hour is not None:
        existing.transfer_hour = payin.transfer_hour
    if payin.transfer_minute is not None:
        existing.transfer_minute = payin.transfer_minute
    if payin.slip_image_url is not None:
        existing.slip_url = payin.slip_image_url  # Database field is slip_url
    
    # Keep status as PENDING after edit (still editable by resident)
    # Status only changes when admin accepts/rejects
    existing.status = PayinStatusEnum.PENDING
    existing.rejection_reason = None
    existing.submitted_at = datetime.now()
    existing.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing)
    
    logger.info(f"✅ Payin {payin_id} updated successfully, status=PENDING")
    
    return {
        "id": existing.id,
        "house_id": existing.house_id,
        "house_number": existing.house.house_code,
        "amount": float(existing.amount),
        "transfer_date": existing.transfer_date,
        "transfer_hour": existing.transfer_hour,
        "transfer_minute": existing.transfer_minute,
        "slip_image_url": existing.slip_url,  # Map database field to frontend expectation
        "status": existing.status,
        "reject_reason": existing.rejection_reason,

        "created_at": existing.created_at,
        "updated_at": existing.updated_at
    }


@router.post("/{payin_id}/reject")
async def reject_payin_report(
    payin_id: int, 
    request: RejectPayInRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """Reject a pay-in report (Admin or Accounting) - transitions to REJECTED_NEEDS_FIX"""
    payin = db.query(PayinReportModel).options(
        joinedload(PayinReportModel.house)
    ).filter(PayinReportModel.id == payin_id).first()
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Check if can be reviewed (SUBMITTED or PENDING)
    if not payin.can_be_reviewed():
        raise HTTPException(
            status_code=400,
            detail=f"Can only reject pay-ins in review state (current status: {payin.status.value})"
        )
    
    if not request.reason or not request.reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is required")
    
    payin.status = PayinStatusEnum.REJECTED_NEEDS_FIX
    payin.rejection_reason = request.reason
    payin.updated_at = datetime.now()
    
    db.commit()
    db.refresh(payin)
    
    return {
        "id": payin.id,
        "house_id": payin.house_id,
        "house_number": payin.house.house_code,
        "amount": float(payin.amount),
        "transfer_date": payin.transfer_date.isoformat() if payin.transfer_date else None,
        "transfer_hour": payin.transfer_hour,
        "transfer_minute": payin.transfer_minute,
        "slip_image_url": payin.slip_url,
        "status": payin.status.value if hasattr(payin.status, 'value') else payin.status,
        "rejection_reason": payin.rejection_reason,
        "created_at": payin.created_at.isoformat() if payin.created_at else None,
        "updated_at": payin.updated_at.isoformat() if payin.updated_at else None
    }


@router.post("/{payin_id}/accept")
async def accept_payin_report(
    payin_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Accept a pay-in report and create immutable ledger entry (Admin or Accounting)
    
    STRICT REQUIREMENTS:
    1. Pay-in must be in reviewable state (SUBMITTED/PENDING)
    2. Pay-in MUST be matched with bank statement first
    3. Creates EXACTLY ONE immutable IncomeTransaction (ledger entry)
    4. Locks pay-in to ACCEPTED status (irreversible)
    5. All operations are ATOMIC (both succeed or both fail)
    """
    # Fetch payin with relationships
    payin = db.query(PayinReportModel).options(
        joinedload(PayinReportModel.house),
        joinedload(PayinReportModel.matched_statement_txn)
    ).filter(PayinReportModel.id == payin_id).first()
    
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # PRECONDITION 1: Already accepted?
    if payin.status == PayinStatusEnum.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="Pay-in report is already accepted"
        )
    
    # PRECONDITION 2: Must be in reviewable state
    if not payin.can_be_reviewed():
        raise HTTPException(
            status_code=400,
            detail=f"Can only accept pay-ins in review state (current status: {payin.status.value})"
        )
    
    # PRECONDITION 3: CRITICAL - Must be matched with bank statement
    if payin.matched_statement_txn_id is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot accept pay-in: Must be matched with bank statement first. Please use Match function before accepting."
        )
    
    # PRECONDITION 4: Check if IncomeTransaction already exists (safety check for idempotency)
    existing_income = db.query(IncomeTransaction).filter(
        IncomeTransaction.payin_id == payin_id
    ).first()
    if existing_income:
        raise HTTPException(
            status_code=400,
            detail=f"Income transaction already exists for this payin (ledger_id: {existing_income.id})"
        )
    
    # ATOMIC TRANSACTION: Update payin + Create ledger entry
    try:
        # 1. Update payin status to ACCEPTED (locks the pay-in)
        payin.status = PayinStatusEnum.ACCEPTED
        payin.accepted_by = current_user.id
        payin.accepted_at = datetime.now()
        payin.updated_at = datetime.now()
        
        # 2. Create IMMUTABLE ledger entry (IncomeTransaction)
        #    Uses bank transaction's effective_at as ledger_date (business truth)
        income_transaction = IncomeTransaction(
            house_id=payin.house_id,
            payin_id=payin.id,
            reference_bank_transaction_id=payin.matched_statement_txn_id,
            amount=payin.amount,
            received_at=payin.matched_statement_txn.effective_at if payin.matched_statement_txn else payin.transfer_date
        )
        
        db.add(income_transaction)
        db.commit()  # Atomic commit: both succeed or both fail
        db.refresh(payin)
        db.refresh(income_transaction)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to accept payin and create ledger entry: {str(e)}"
        )
    
    return {
        "id": payin.id,
        "house_id": payin.house_id,
        "house_number": payin.house.house_code,
        "amount": float(payin.amount),
        "transfer_date": payin.transfer_date.isoformat() if payin.transfer_date else None,
        "transfer_hour": payin.transfer_hour,
        "transfer_minute": payin.transfer_minute,
        "slip_image_url": payin.slip_url,
        "status": payin.status.value if hasattr(payin.status, 'value') else payin.status,
        "rejection_reason": payin.rejection_reason,
        "accepted_by": payin.accepted_by,
        "accepted_at": payin.accepted_at.isoformat() if payin.accepted_at else None,
        "matched_statement_txn_id": str(payin.matched_statement_txn_id) if payin.matched_statement_txn_id else None,
        "created_at": payin.created_at.isoformat() if payin.created_at else None,
        "updated_at": payin.updated_at.isoformat() if payin.updated_at else None,
        "income_transaction_id": income_transaction.id,
        "ledger": {
            "id": income_transaction.id,
            "reference_bank_transaction_id": str(income_transaction.reference_bank_transaction_id),
            "amount": float(income_transaction.amount),
            "received_at": income_transaction.received_at.isoformat(),
            "created_at": income_transaction.created_at.isoformat()
        }
    }


@router.post("/{payin_id}/cancel")
async def cancel_payin_report(
    payin_id: int,
    request: RejectPayInRequest,  # Reuse same schema (has 'reason' field)
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """Cancel a pay-in report for test cleanup (Admin or Accounting)"""
    payin = db.query(PayinReportModel).options(
        joinedload(PayinReportModel.house)
    ).filter(PayinReportModel.id == payin_id).first()
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status not in ["PENDING", "REJECTED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Can only cancel PENDING or REJECTED pay-in reports (current status: {payin.status})"
        )
    
    if not request.reason or not request.reason.strip():
        raise HTTPException(status_code=400, detail="Cancellation reason is required")
    
    # Delete the payin report
    db.delete(payin)
    db.commit()
    
    return {
        "message": "Pay-in report cancelled and deleted",
        "payin_id": payin_id,
        "reason": request.reason
    }


@router.delete("/{payin_id}")
async def delete_payin_report(
    payin_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    """Delete a pay-in report
    
    Resident can delete:
    - DRAFT
    - REJECTED_NEEDS_FIX (and legacy REJECTED)
    
    Resident CANNOT delete:
    - PENDING (must edit instead)
    - SUBMITTED (under review)
    - ACCEPTED (permanent record)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"DELETE /payin-reports/{payin_id} by user={current_user.id} role={current_user.role}")
    
    try:
        payin = db.query(PayinReportModel).filter(PayinReportModel.id == payin_id).first()
        if not payin:
            logger.warning(f"Payin {payin_id} not found")
            raise HTTPException(status_code=404, detail="Pay-in report not found")
        
        # Get status value for comparison (handle both Enum and string)
        status_value = payin.status.value if hasattr(payin.status, 'value') else str(payin.status)
        logger.info(f"Payin {payin_id} status={status_value} house_id={payin.house_id}")
        
        # Deletable statuses for residents
        DELETABLE_STATUSES = ["DRAFT", "REJECTED_NEEDS_FIX", "REJECTED"]
        
        # Role-based access control
        if current_user.role == "resident":
            if user_house_id != payin.house_id:
                logger.warning(f"Access denied: user house={user_house_id} != payin house={payin.house_id}")
                raise HTTPException(status_code=403, detail="Access denied to this house's data")
            
            # Residents can only delete DRAFT or REJECTED pay-ins
            if status_value not in DELETABLE_STATUSES:
                logger.info(f"Cannot delete status={status_value}, not in {DELETABLE_STATUSES}")
                # Return proper error code for UI to translate
                if status_value in ["PENDING", "SUBMITTED"]:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "code": "CANNOT_DELETE_PENDING",
                            "message": "ไม่สามารถลบรายการที่รอตรวจสอบได้ กรุณาแก้ไขแทน",
                            "status": status_value
                        }
                    )
                elif status_value == "ACCEPTED":
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "code": "CANNOT_DELETE_ACCEPTED",
                            "message": "ไม่สามารถลบรายการที่ยืนยันแล้วได้",
                            "status": status_value
                        }
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "code": "CANNOT_DELETE",
                            "message": f"ไม่สามารถลบรายการสถานะ {status_value} ได้",
                            "status": status_value
                        }
                    )
        elif current_user.role in ["accounting", "super_admin"]:
            # Admins can delete any non-accepted pay-in
            if status_value == "ACCEPTED":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "CANNOT_DELETE_ACCEPTED",
                        "message": "Cannot delete an accepted pay-in report",
                        "status": status_value
                    }
                )
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Clear any related bank transaction links before delete (avoid FK constraint errors)
        if payin.matched_statement_txn_id:
            logger.info(f"Clearing matched_statement_txn_id={payin.matched_statement_txn_id}")
            payin.matched_statement_txn_id = None
        if payin.reference_bank_transaction_id:
            logger.info(f"Clearing reference_bank_transaction_id={payin.reference_bank_transaction_id}")
            payin.reference_bank_transaction_id = None
        
        # Delete the pay-in
        db.delete(payin)
        db.commit()
        
        logger.info(f"✅ Payin {payin_id} deleted successfully")
        return {"message": "ลบรายการสำเร็จ", "payin_id": payin_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting payin {payin_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "code": "DELETE_ERROR",
                "message": "เกิดข้อผิดพลาดในการลบรายการ กรุณาลองใหม่"
            }
        )
