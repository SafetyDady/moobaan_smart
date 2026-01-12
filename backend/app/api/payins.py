from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from app.models import (
    PayInReport, PayInReportCreate, PayInReportUpdate,
    RejectPayInRequest, PayInStatus
)
from app.mock_data import MOCK_PAYIN_REPORTS, MOCK_HOUSES

router = APIRouter(prefix="/api/payin-reports", tags=["payin-reports"])

# In-memory storage
payins_db = list(MOCK_PAYIN_REPORTS)
next_id = max([p.id for p in payins_db]) + 1


@router.get("", response_model=List[PayInReport])
async def list_payin_reports(
    house_id: int = None,
    status: str = None
):
    """List all pay-in reports with optional filters"""
    result = payins_db
    
    if house_id:
        result = [p for p in result if p.house_id == house_id]
    
    if status:
        result = [p for p in result if p.status.value == status]
    
    return sorted(result, key=lambda x: x.created_at, reverse=True)


@router.get("/{payin_id}", response_model=PayInReport)
async def get_payin_report(payin_id: int):
    """Get a specific pay-in report by ID"""
    payin = next((p for p in payins_db if p.id == payin_id), None)
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    return payin


@router.post("", response_model=PayInReport)
async def create_payin_report(payin: PayInReportCreate):
    """Create a new pay-in report (resident submits)"""
    global next_id
    
    # Check house exists
    house = next((h for h in MOCK_HOUSES if h.id == payin.house_id), None)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    new_payin = PayInReport(
        id=next_id,
        house_id=payin.house_id,
        house_number=house.house_number,
        amount=payin.amount,
        transfer_date=payin.transfer_date,
        transfer_hour=payin.transfer_hour,
        transfer_minute=payin.transfer_minute,
        slip_image_url=payin.slip_image_url,
        status=PayInStatus.SUBMITTED,
        reject_reason=None,
        matched_statement_row_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    payins_db.append(new_payin)
    next_id += 1
    return new_payin


@router.put("/{payin_id}", response_model=PayInReport)
async def update_payin_report(payin_id: int, payin: PayInReportUpdate):
    """Update a pay-in report (only when REJECTED)"""
    existing = next((p for p in payins_db if p.id == payin_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    # Only allow update when status is REJECTED
    if existing.status != PayInStatus.REJECTED:
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
    existing.status = PayInStatus.SUBMITTED
    existing.reject_reason = None
    existing.updated_at = datetime.now()
    
    return existing


@router.post("/{payin_id}/reject")
async def reject_payin_report(payin_id: int, request: RejectPayInRequest):
    """Reject a pay-in report (Accounting/Admin)"""
    payin = next((p for p in payins_db if p.id == payin_id), None)
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status == PayInStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot reject an accepted pay-in report"
        )
    
    payin.status = PayInStatus.REJECTED
    payin.reject_reason = request.reason
    payin.matched_statement_row_id = None
    payin.updated_at = datetime.now()
    
    return {
        "message": "Pay-in report rejected",
        "payin_id": payin_id,
        "reason": request.reason
    }


@router.post("/{payin_id}/match")
async def match_payin_report(payin_id: int, statement_row_id: int):
    """Match a pay-in report with a bank statement row (Accounting)"""
    payin = next((p for p in payins_db if p.id == payin_id), None)
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status not in [PayInStatus.SUBMITTED, PayInStatus.MATCHED]:
        raise HTTPException(
            status_code=400,
            detail="Can only match SUBMITTED or MATCHED pay-in reports"
        )
    
    payin.status = PayInStatus.MATCHED
    payin.matched_statement_row_id = statement_row_id
    payin.updated_at = datetime.now()
    
    return {
        "message": "Pay-in report matched with statement row",
        "payin_id": payin_id,
        "statement_row_id": statement_row_id
    }


@router.post("/{payin_id}/accept")
async def accept_payin_report(payin_id: int):
    """Accept a pay-in report (Super Admin only - final confirmation)"""
    payin = next((p for p in payins_db if p.id == payin_id), None)
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status == PayInStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="Pay-in report is already accepted"
        )
    
    if payin.status != PayInStatus.MATCHED:
        raise HTTPException(
            status_code=400,
            detail="Can only accept MATCHED pay-in reports"
        )
    
    payin.status = PayInStatus.ACCEPTED
    payin.updated_at = datetime.now()
    
    return {
        "message": "Pay-in report accepted and locked",
        "payin_id": payin_id
    }


@router.delete("/{payin_id}")
async def delete_payin_report(payin_id: int):
    """Delete a pay-in report"""
    global payins_db
    payin = next((p for p in payins_db if p.id == payin_id), None)
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in report not found")
    
    if payin.status == PayInStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an accepted pay-in report"
        )
    
    payins_db = [p for p in payins_db if p.id != payin_id]
    return {"message": "Pay-in report deleted successfully"}
