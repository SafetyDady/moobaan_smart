"""
Phase G.1: Period Closing & Snapshot API

Endpoints:
- GET  /api/periods              - List all period snapshots
- GET  /api/periods/{year}/{month} - Get specific period snapshot
- POST /api/periods/{year}/{month}/snapshot - Generate snapshot & lock
- POST /api/periods/{year}/{month}/unlock   - Unlock (super_admin + reason required)
- GET  /api/periods/{year}/{month}/unlock-logs - View unlock audit logs

Purpose: Governance layer for locking historical data (soft lock)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
import calendar

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.db.models import (
    User, PeriodSnapshot, PeriodStatus, PeriodUnlockLog,
    Invoice, InvoiceStatus, PayinReport, PayinStatus,
    Expense, ExpenseStatus, CreditNote, CreditNoteStatus, House, HouseStatus
)

router = APIRouter(prefix="/api/periods", tags=["Period Closing"])


# --- Pydantic Schemas ---

class SnapshotCreateRequest(BaseModel):
    notes: Optional[str] = None


class UnlockRequest(BaseModel):
    reason: str  # Required


class PeriodCheckResponse(BaseModel):
    year: int
    month: int
    is_locked: bool
    status: Optional[str] = None
    message: str


# --- Helper Functions ---

def get_last_day_of_month(year: int, month: int) -> date:
    """Get the last day of a given month"""
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, last_day)


def check_period_locked(db: Session, year: int, month: int) -> bool:
    """Check if a period is locked"""
    snapshot = db.query(PeriodSnapshot).filter(
        PeriodSnapshot.period_year == year,
        PeriodSnapshot.period_month == month,
        PeriodSnapshot.status == PeriodStatus.LOCKED
    ).first()
    return snapshot is not None


def generate_snapshot_data(db: Session, year: int, month: int) -> dict:
    """
    Generate aggregated snapshot data for a period.
    
    Snapshot includes:
    - ar_total: Total accounts receivable (unpaid invoice amounts)
    - cash_received_total: Total confirmed payins
    - expense_paid_total: Total paid expenses
    - expense_pending_total: Total pending expenses
    - invoice_count: Number of invoices in period
    - house_count: Number of active houses
    """
    # Date range for the period
    start_date = date(year, month, 1)
    end_date = get_last_day_of_month(year, month)
    
    # Calculate AR Total (unpaid invoices up to this period)
    # Use total_amount for ISSUED/PARTIALLY_PAID invoices
    ar_total = db.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
        Invoice.due_date <= end_date,
        Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID])
    ).scalar()
    
    # Cash received in period (confirmed payins)
    # Note: transfer_date is DateTime, need to cast for date comparison
    from sqlalchemy import cast, Date as SQLDate
    cash_received_total = db.query(func.coalesce(func.sum(PayinReport.amount), 0)).filter(
        cast(PayinReport.transfer_date, SQLDate) >= start_date,
        cast(PayinReport.transfer_date, SQLDate) <= end_date,
        PayinReport.status == PayinStatus.ACCEPTED
    ).scalar()
    
    # Expenses paid in period
    expense_paid_total = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
        Expense.status == ExpenseStatus.PAID
    ).scalar()
    
    # Expenses pending in period
    expense_pending_total = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
        Expense.status == ExpenseStatus.PENDING
    ).scalar()
    
    # Invoice count for period
    invoice_count = db.query(func.count(Invoice.id)).filter(
        Invoice.issue_date >= start_date,
        Invoice.issue_date <= end_date
    ).scalar()
    
    # Credit notes total in period
    credit_total = db.query(func.coalesce(func.sum(CreditNote.credit_amount), 0)).filter(
        CreditNote.created_at >= start_date,
        CreditNote.created_at <= end_date,
        CreditNote.status == 'applied'  # Use raw string to match PgEnum definition
    ).scalar()
    
    # Active house count
    house_count = db.query(func.count(House.id)).filter(
        House.house_status == HouseStatus.ACTIVE
    ).scalar()
    
    return {
        "ar_total": float(ar_total or 0),
        "cash_received_total": float(cash_received_total or 0),
        "expense_paid_total": float(expense_paid_total or 0),
        "expense_pending_total": float(expense_pending_total or 0),
        "credit_total": float(credit_total or 0),
        "invoice_count": int(invoice_count or 0),
        "house_count": int(house_count or 0),
    }


# --- API Endpoints ---

@router.get("")
async def list_periods(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),  # Default 2 years
    status: Optional[str] = None,
):
    """List all period snapshots"""
    query = db.query(PeriodSnapshot)
    
    if status:
        try:
            status_enum = PeriodStatus(status)
            query = query.filter(PeriodSnapshot.status == status_enum)
        except ValueError:
            pass
    
    # Order by most recent first
    query = query.order_by(
        PeriodSnapshot.period_year.desc(),
        PeriodSnapshot.period_month.desc()
    )
    
    total = query.count()
    periods = query.offset(skip).limit(limit).all()
    
    return {
        "items": [p.to_dict() for p in periods],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/check/{year}/{month}")
async def check_period_status(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if a specific period is locked (for use by other APIs)"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    snapshot = db.query(PeriodSnapshot).filter(
        PeriodSnapshot.period_year == year,
        PeriodSnapshot.period_month == month
    ).first()
    
    if not snapshot:
        return PeriodCheckResponse(
            year=year,
            month=month,
            is_locked=False,
            status=None,
            message=f"Period {year}-{str(month).zfill(2)} has no snapshot"
        )
    
    return PeriodCheckResponse(
        year=year,
        month=month,
        is_locked=(snapshot.status == PeriodStatus.LOCKED),
        status=snapshot.status.value,
        message=f"Period {year}-{str(month).zfill(2)} is {snapshot.status.value}"
    )


@router.get("/{year}/{month}")
async def get_period_snapshot(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get specific period snapshot details"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    snapshot = db.query(PeriodSnapshot).filter(
        PeriodSnapshot.period_year == year,
        PeriodSnapshot.period_month == month
    ).first()
    
    if not snapshot:
        # Return generated data without saving (preview)
        return {
            "exists": False,
            "period_year": year,
            "period_month": month,
            "period_label": f"{year}-{str(month).zfill(2)}",
            "snapshot_data": generate_snapshot_data(db, year, month),
            "status": None,
            "message": "No snapshot exists. You can create one to lock this period.",
        }
    
    result = snapshot.to_dict()
    result["exists"] = True
    return result


@router.post("/{year}/{month}/snapshot")
async def create_period_snapshot(
    year: int,
    month: int,
    request: SnapshotCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create period snapshot and lock the period"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    # Check if already exists
    existing = db.query(PeriodSnapshot).filter(
        PeriodSnapshot.period_year == year,
        PeriodSnapshot.period_month == month
    ).first()
    
    if existing:
        if existing.status == PeriodStatus.LOCKED:
            raise HTTPException(
                status_code=400,
                detail=f"Period {year}-{str(month).zfill(2)} is already locked"
            )
        # If exists but DRAFT, update it
        existing.snapshot_data = generate_snapshot_data(db, year, month)
        existing.status = PeriodStatus.LOCKED
        existing.as_of_date = get_last_day_of_month(year, month)
        existing.updated_at = datetime.utcnow()
        if request.notes:
            existing.notes = request.notes
        db.commit()
        db.refresh(existing)
        return {
            "success": True,
            "message": f"Period {year}-{str(month).zfill(2)} has been locked",
            "snapshot": existing.to_dict()
        }
    
    # Create new snapshot
    snapshot = PeriodSnapshot(
        period_year=year,
        period_month=month,
        as_of_date=get_last_day_of_month(year, month),
        snapshot_data=generate_snapshot_data(db, year, month),
        status=PeriodStatus.LOCKED,
        created_by=current_user.id,
        notes=request.notes,
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return {
        "success": True,
        "message": f"Period {year}-{str(month).zfill(2)} has been locked",
        "snapshot": snapshot.to_dict()
    }


@router.post("/{year}/{month}/unlock")
async def unlock_period(
    year: int,
    month: int,
    request: UnlockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Unlock a locked period (requires reason, creates audit log)"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    if not request.reason or len(request.reason.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Reason must be at least 10 characters"
        )
    
    # Check if user is super_admin
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="Only super_admin can unlock a period"
        )
    
    snapshot = db.query(PeriodSnapshot).filter(
        PeriodSnapshot.period_year == year,
        PeriodSnapshot.period_month == month
    ).first()
    
    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail=f"No snapshot exists for period {year}-{str(month).zfill(2)}"
        )
    
    if snapshot.status != PeriodStatus.LOCKED:
        raise HTTPException(
            status_code=400,
            detail=f"Period {year}-{str(month).zfill(2)} is not locked"
        )
    
    # Create audit log
    unlock_log = PeriodUnlockLog(
        period_snapshot_id=snapshot.id,
        unlocked_by=current_user.id,
        reason=request.reason.strip(),
        previous_status=snapshot.status.value,
    )
    db.add(unlock_log)
    
    # Update snapshot status
    snapshot.status = PeriodStatus.DRAFT
    snapshot.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(snapshot)
    
    return {
        "success": True,
        "message": f"Period {year}-{str(month).zfill(2)} has been unlocked",
        "snapshot": snapshot.to_dict()
    }


@router.get("/{year}/{month}/unlock-logs")
async def get_unlock_logs(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get unlock audit logs for a period"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    snapshot = db.query(PeriodSnapshot).filter(
        PeriodSnapshot.period_year == year,
        PeriodSnapshot.period_month == month
    ).first()
    
    if not snapshot:
        return {"items": [], "total": 0}
    
    logs = db.query(PeriodUnlockLog).filter(
        PeriodUnlockLog.period_snapshot_id == snapshot.id
    ).order_by(PeriodUnlockLog.unlocked_at.desc()).all()
    
    return {
        "items": [log.to_dict() for log in logs],
        "total": len(logs),
    }
