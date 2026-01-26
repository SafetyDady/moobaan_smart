"""
Phase G.2: Year / Period Export API

Purpose:
- Export accounting data for accountants
- READ ONLY from LOCKED snapshots
- No data mutation

Outputs:
1. Revenue by Account
2. Expense by Account  
3. AR Summary
4. Cash Received Summary

Explicit Non-Goals:
- No Journal
- No Ledger
- No recalculation
- No Balance Sheet
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
import csv
import io
import json
import zipfile

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.db.models import User, PeriodSnapshot, PeriodStatus
from app.db.models.export_audit_log import ExportAuditLog

router = APIRouter(prefix="/api/export", tags=["Accounting Export"])


# --- Pydantic Schemas ---

class ExportRequest(BaseModel):
    from_period: str  # YYYY-MM
    to_period: str    # YYYY-MM
    format: str = "csv"  # csv or xlsx


class ExportLogResponse(BaseModel):
    id: int
    user_name: Optional[str]
    from_period: str
    to_period: str
    export_type: str
    reports_included: str
    exported_at: str


# --- Helper Functions ---

def parse_period(period_str: str) -> tuple:
    """Parse YYYY-MM string to (year, month)"""
    try:
        parts = period_str.split("-")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail=f"Invalid period format: {period_str}. Use YYYY-MM")


def get_period_range(from_period: str, to_period: str) -> List[tuple]:
    """Generate list of (year, month) tuples between two periods"""
    from_year, from_month = parse_period(from_period)
    to_year, to_month = parse_period(to_period)
    
    periods = []
    year, month = from_year, from_month
    
    while (year, month) <= (to_year, to_month):
        periods.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    
    return periods


def get_locked_snapshots(db: Session, periods: List[tuple]) -> List[PeriodSnapshot]:
    """Get all LOCKED snapshots for given periods"""
    snapshots = []
    for year, month in periods:
        snapshot = db.query(PeriodSnapshot).filter(
            PeriodSnapshot.period_year == year,
            PeriodSnapshot.period_month == month,
            PeriodSnapshot.status == PeriodStatus.LOCKED
        ).first()
        if snapshot:
            snapshots.append(snapshot)
    return snapshots


def create_audit_log(
    db: Session, 
    user: User, 
    from_period: str, 
    to_period: str, 
    export_type: str,
    reports: List[str]
):
    """Create audit log entry for export"""
    log = ExportAuditLog(
        user_id=user.id,
        from_period=from_period,
        to_period=to_period,
        export_type=export_type,
        reports_included=json.dumps(reports),
    )
    db.add(log)
    db.commit()
    return log


# --- Report Generators (from Snapshot ONLY) ---

def generate_revenue_by_account(snapshots: List[PeriodSnapshot]) -> List[dict]:
    """
    Generate Revenue by Account report from snapshots.
    Source: snapshot_data.revenue (if exists)
    """
    rows = []
    for snapshot in snapshots:
        period_label = f"{snapshot.period_year}-{str(snapshot.period_month).zfill(2)}"
        data = snapshot.snapshot_data or {}
        
        # If snapshot has revenue breakdown
        revenue_data = data.get("revenue", {})
        if revenue_data and isinstance(revenue_data, dict):
            for account_code, account_info in revenue_data.items():
                rows.append({
                    "period": period_label,
                    "account_code": account_code,
                    "account_name": account_info.get("name", ""),
                    "total_amount": account_info.get("amount", 0),
                })
        else:
            # Fallback: use ar_total as general revenue
            rows.append({
                "period": period_label,
                "account_code": "4000",
                "account_name": "ค่าส่วนกลาง (รายรับ)",
                "total_amount": data.get("ar_total", 0),
            })
    
    return rows


def generate_expense_by_account(snapshots: List[PeriodSnapshot]) -> List[dict]:
    """
    Generate Expense by Account report from snapshots.
    Source: snapshot_data.expenses (if exists)
    """
    rows = []
    for snapshot in snapshots:
        period_label = f"{snapshot.period_year}-{str(snapshot.period_month).zfill(2)}"
        data = snapshot.snapshot_data or {}
        
        # If snapshot has expense breakdown
        expense_data = data.get("expenses", {})
        if expense_data and isinstance(expense_data, dict):
            for account_code, account_info in expense_data.items():
                rows.append({
                    "period": period_label,
                    "account_code": account_code,
                    "account_name": account_info.get("name", ""),
                    "total_amount": account_info.get("amount", 0),
                })
        else:
            # Fallback: use expense_paid_total as general expense
            rows.append({
                "period": period_label,
                "account_code": "5000",
                "account_name": "ค่าใช้จ่ายทั่วไป",
                "total_amount": data.get("expense_paid_total", 0),
            })
    
    return rows


def generate_ar_summary(snapshots: List[PeriodSnapshot]) -> List[dict]:
    """
    Generate AR Summary report from snapshots.
    Source: snapshot_data.ar
    """
    rows = []
    for snapshot in snapshots:
        period_label = f"{snapshot.period_year}-{str(snapshot.period_month).zfill(2)}"
        data = snapshot.snapshot_data or {}
        
        # AR data from snapshot
        ar_data = data.get("ar", {})
        if ar_data and isinstance(ar_data, dict):
            rows.append({
                "period": period_label,
                "total_invoiced": ar_data.get("total_invoiced", 0),
                "total_credited": ar_data.get("total_credited", 0),
                "total_paid": ar_data.get("total_paid", 0),
                "outstanding_balance": ar_data.get("outstanding_balance", 0),
            })
        else:
            # Fallback: use available totals
            ar_total = data.get("ar_total", 0)
            cash_received = data.get("cash_received_total", 0)
            credit_total = data.get("credit_total", 0)
            rows.append({
                "period": period_label,
                "total_invoiced": ar_total + cash_received + credit_total,  # Estimated
                "total_credited": credit_total,
                "total_paid": cash_received,
                "outstanding_balance": ar_total,
            })
    
    return rows


def generate_cash_received_summary(snapshots: List[PeriodSnapshot]) -> List[dict]:
    """
    Generate Cash Received Summary report from snapshots.
    Source: snapshot_data.cash_received
    """
    rows = []
    for snapshot in snapshots:
        period_label = f"{snapshot.period_year}-{str(snapshot.period_month).zfill(2)}"
        data = snapshot.snapshot_data or {}
        
        rows.append({
            "period": period_label,
            "total_cash_received": data.get("cash_received_total", 0),
        })
    
    return rows


# --- CSV/ZIP Generators ---

# UTF-8 BOM for Excel compatibility on Windows
UTF8_BOM = '\ufeff'

def dict_to_csv_string(rows: List[dict], fieldnames: List[str]) -> str:
    """Convert list of dicts to CSV string with UTF-8 BOM for Excel compatibility"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    # Prepend UTF-8 BOM for Excel on Windows to display Thai correctly
    return UTF8_BOM + output.getvalue()


def create_export_zip(
    revenue_rows: List[dict],
    expense_rows: List[dict],
    ar_rows: List[dict],
    cash_rows: List[dict],
) -> bytes:
    """Create ZIP file with all CSV reports"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Revenue by Account
        if revenue_rows:
            csv_content = dict_to_csv_string(
                revenue_rows, 
                ["period", "account_code", "account_name", "total_amount"]
            )
            zf.writestr("revenue_by_account.csv", csv_content)
        
        # Expense by Account
        if expense_rows:
            csv_content = dict_to_csv_string(
                expense_rows,
                ["period", "account_code", "account_name", "total_amount"]
            )
            zf.writestr("expense_by_account.csv", csv_content)
        
        # AR Summary
        if ar_rows:
            csv_content = dict_to_csv_string(
                ar_rows,
                ["period", "total_invoiced", "total_credited", "total_paid", "outstanding_balance"]
            )
            zf.writestr("ar_summary.csv", csv_content)
        
        # Cash Received
        if cash_rows:
            csv_content = dict_to_csv_string(
                cash_rows,
                ["period", "total_cash_received"]
            )
            zf.writestr("cash_received.csv", csv_content)
    
    return zip_buffer.getvalue()


# --- API Endpoints ---

@router.post("/accounting")
async def export_accounting_data(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Export accounting data for accountants.
    
    - Only reads from LOCKED snapshots
    - Returns ZIP file with 4 CSV reports
    - Creates audit log
    """
    # Validate periods
    from_year, from_month = parse_period(request.from_period)
    to_year, to_month = parse_period(request.to_period)
    
    if (to_year, to_month) < (from_year, from_month):
        raise HTTPException(
            status_code=400, 
            detail="to_period must be >= from_period"
        )
    
    # Get period range
    periods = get_period_range(request.from_period, request.to_period)
    
    # Get LOCKED snapshots only
    snapshots = get_locked_snapshots(db, periods)
    
    if not snapshots:
        raise HTTPException(
            status_code=404,
            detail=f"No LOCKED snapshots found for period {request.from_period} to {request.to_period}"
        )
    
    # Generate reports from snapshots
    revenue_rows = generate_revenue_by_account(snapshots)
    expense_rows = generate_expense_by_account(snapshots)
    ar_rows = generate_ar_summary(snapshots)
    cash_rows = generate_cash_received_summary(snapshots)
    
    # Create audit log
    reports_list = ["revenue_by_account", "expense_by_account", "ar_summary", "cash_received"]
    create_audit_log(
        db, current_user, 
        request.from_period, request.to_period,
        request.format, reports_list
    )
    
    # Create ZIP with all CSVs
    zip_content = create_export_zip(revenue_rows, expense_rows, ar_rows, cash_rows)
    
    # Generate filename
    filename = f"moobaan_accounting_export_{request.from_period}_{request.to_period}.zip"
    
    return StreamingResponse(
        io.BytesIO(zip_content),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/preview")
async def preview_export_data(
    from_period: str = Query(..., description="Start period (YYYY-MM)"),
    to_period: str = Query(..., description="End period (YYYY-MM)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Preview export data without downloading.
    Shows what periods are available and their status.
    """
    # Validate periods
    from_year, from_month = parse_period(from_period)
    to_year, to_month = parse_period(to_period)
    
    if (to_year, to_month) < (from_year, from_month):
        raise HTTPException(
            status_code=400, 
            detail="to_period must be >= from_period"
        )
    
    # Get period range
    periods = get_period_range(from_period, to_period)
    
    # Check each period
    period_status = []
    locked_count = 0
    
    for year, month in periods:
        snapshot = db.query(PeriodSnapshot).filter(
            PeriodSnapshot.period_year == year,
            PeriodSnapshot.period_month == month
        ).first()
        
        status = "NO_SNAPSHOT"
        if snapshot:
            status = snapshot.status.value
            if snapshot.status == PeriodStatus.LOCKED:
                locked_count += 1
        
        period_status.append({
            "period": f"{year}-{str(month).zfill(2)}",
            "status": status,
            "exportable": status == "LOCKED"
        })
    
    # Get snapshots for preview
    snapshots = get_locked_snapshots(db, periods)
    
    # Generate preview data
    preview_data = {
        "revenue_by_account": generate_revenue_by_account(snapshots),
        "expense_by_account": generate_expense_by_account(snapshots),
        "ar_summary": generate_ar_summary(snapshots),
        "cash_received": generate_cash_received_summary(snapshots),
    }
    
    return {
        "from_period": from_period,
        "to_period": to_period,
        "total_periods": len(periods),
        "locked_periods": locked_count,
        "exportable": locked_count > 0,
        "periods": period_status,
        "preview": preview_data,
    }


@router.get("/logs")
async def list_export_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List export audit logs"""
    query = db.query(ExportAuditLog).order_by(ExportAuditLog.exported_at.desc())
    
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "items": [log.to_dict() for log in logs],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
