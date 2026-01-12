from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from app.models import (
    PayInReport as PayInReportSchema, PayInReportCreate, PayInReportUpdate,
    RejectPayInRequest, PayInStatus
)
from app.db.models.payin_report import PayinReport as PayinReportModel
from app.db.models.house import House as HouseModel
from app.db.models.user import User
from app.db.session import get_db
from app.core.deps import require_user, require_admin, require_admin_or_accounting, get_user_house_id

router = APIRouter(prefix="/api/payin-reports", tags=["payin-reports"])


@router.get("", response_model=List[dict])
async def list_payin_reports(
    house_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = require_user,
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
        "house_number": payin.house.house_no,
        "amount": float(payin.amount),
        "transfer_date": payin.transfer_date,
        "transfer_hour": payin.transfer_hour,
        "transfer_minute": payin.transfer_minute,
        "slip_image_url": payin.slip_image_url,
        "status": payin.status,
        "reject_reason": payin.reject_reason,
        "matched_statement_row_id": payin.matched_statement_row_id,
        "created_at": payin.created_at,
        "updated_at": payin.updated_at
    } for payin in payins]


@router.get("/{payin_id}", response_model=dict)
async def get_payin_report(
    payin_id: int, 
    db: Session = Depends(get_db),
    current_user: User = require_user,
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
        "house_number": payin.house.house_no,
        "amount": float(payin.amount),
        "transfer_date": payin.transfer_date,
        "transfer_hour": payin.transfer_hour,
        "transfer_minute": payin.transfer_minute,
        "slip_image_url": payin.slip_image_url,
        "status": payin.status,
        "reject_reason": payin.reject_reason,
        "matched_statement_row_id": payin.matched_statement_row_id,
        "created_at": payin.created_at,
        "updated_at": payin.updated_at
    }


@router.post("", response_model=dict)
async def create_payin_report(
    payin: PayInReportCreate, 
    db: Session = Depends(get_db),
    current_user: User = require_user,
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    """Create a new pay-in report (resident submits)"""
    # Only residents can create payins, and only for their own house
    if current_user.role != "resident":
        raise HTTPException(status_code=403, detail="Only residents can create pay-in reports")
    
    if user_house_id is None:
        raise HTTPException(status_code=403, detail="Resident not linked to any house")
    
    if payin.house_id != user_house_id:
        raise HTTPException(status_code=403, detail="Can only create pay-in reports for your own house")
    
    # Check house exists
    house = db.query(HouseModel).filter(HouseModel.id == payin.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    new_payin = PayinReportModel(
        house_id=payin.house_id,
        amount=payin.amount,
        transfer_date=payin.transfer_date,
        transfer_hour=payin.transfer_hour,
        transfer_minute=payin.transfer_minute,
        slip_image_url=payin.slip_image_url,
        status="SUBMITTED",
        reject_reason=None,
        matched_statement_row_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.add(new_payin)
    db.commit()
    db.refresh(new_payin)
    
    return {
        "id": new_payin.id,
        "house_id": new_payin.house_id,
        "house_number": house.house_no,
        "amount": float(new_payin.amount),
        "transfer_date": new_payin.transfer_date,
        "transfer_hour": new_payin.transfer_hour,
        "transfer_minute": new_payin.transfer_minute,
        "slip_image_url": new_payin.slip_image_url,
        "status": new_payin.status,
        "reject_reason": new_payin.reject_reason,
        "matched_statement_row_id": new_payin.matched_statement_row_id,
        "created_at": new_payin.created_at,
        "updated_at": new_payin.updated_at
    }


@router.put("/{payin_id}", response_model=dict)
async def update_payin_report(payin_id: int, payin: PayInReportUpdate, db: Session = Depends(get_db)):
    """Update a pay-in report (only when REJECTED)"""
    existing = db.query(PayinReportModel).options(
        joinedload(PayinReportModel.house)
    ).filter(PayinReportModel.id == payin_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Only allow update when status is REJECTED
    if existing.status != "REJECTED":
        raise HTTPException(
            status_code=400,
            detail="Can only edit pay-in reports with REJECTED status"
        )
    
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
        existing.slip_image_url = payin.slip_image_url
    
    # Reset to SUBMITTED after edit
    existing.status = "SUBMITTED"
    existing.reject_reason = None
    existing.updated_at = datetime.now()
    
    db.commit()
    db.refresh(existing)
    
    return {
        "id": existing.id,
        "house_id": existing.house_id,
        "house_number": existing.house.house_no,
        "amount": float(existing.amount),
        "transfer_date": existing.transfer_date,
        "transfer_hour": existing.transfer_hour,
        "transfer_minute": existing.transfer_minute,
        "slip_image_url": existing.slip_image_url,
        "status": existing.status,
        "reject_reason": existing.reject_reason,
        "matched_statement_row_id": existing.matched_statement_row_id,
        "created_at": existing.created_at,
        "updated_at": existing.updated_at
    }


@router.post("/{payin_id}/reject")
async def reject_payin_report(
    payin_id: int, 
    request: RejectPayInRequest, 
    db: Session = Depends(get_db),
    current_user: User = require_admin_or_accounting
):
    """Reject a pay-in report (Accounting/Admin)"""
    payin = db.query(PayinReportModel).filter(PayinReportModel.id == payin_id).first()
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status == "ACCEPTED":
        raise HTTPException(
            status_code=400,
            detail="Cannot reject an accepted pay-in report"
        )
    
    payin.status = "REJECTED"
    payin.reject_reason = request.reason
    payin.matched_statement_row_id = None
    payin.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "message": "Pay-in report rejected",
        "payin_id": payin_id,
        "reason": request.reason
    }


@router.post("/{payin_id}/match")
async def match_payin_report(
    payin_id: int, 
    statement_row_id: int, 
    db: Session = Depends(get_db),
    current_user: User = require_admin_or_accounting
):
    """Match a pay-in report with a bank statement row (Accounting)"""
    payin = db.query(PayinReportModel).filter(PayinReportModel.id == payin_id).first()
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status not in ["SUBMITTED", "MATCHED"]:
        raise HTTPException(
            status_code=400,
            detail="Can only match SUBMITTED or MATCHED pay-in reports"
        )
    
    payin.status = "MATCHED"
    payin.matched_statement_row_id = statement_row_id
    payin.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "message": "Pay-in report matched with statement row",
        "payin_id": payin_id,
        "statement_row_id": statement_row_id
    }


@router.post("/{payin_id}/accept")
async def accept_payin_report(
    payin_id: int, 
    db: Session = Depends(get_db),
    current_user: User = require_admin
):
    """Accept a pay-in report (Super Admin only - final confirmation)"""
    payin = db.query(PayinReportModel).filter(PayinReportModel.id == payin_id).first()
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status == "ACCEPTED":
        raise HTTPException(
            status_code=400,
            detail="Pay-in report is already accepted"
        )
    
    if payin.status != "MATCHED":
        raise HTTPException(
            status_code=400,
            detail="Can only accept MATCHED pay-in reports"
        )
    
    payin.status = "ACCEPTED"
    payin.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "message": "Pay-in report accepted and locked",
        "payin_id": payin_id
    }


@router.delete("/{payin_id}")
async def delete_payin_report(payin_id: int, db: Session = Depends(get_db)):
    """Delete a pay-in report"""
    payin = db.query(PayinReportModel).filter(PayinReportModel.id == payin_id).first()
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status == "ACCEPTED":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an accepted pay-in report"
        )
    
    db.delete(payin)
    db.commit()
    
    return {"message": "Pay-in report deleted successfully"}
