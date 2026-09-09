"""
Phase E.1: Invoice Aging Report
Phase E.2: Cash Flow vs AR Report

READ-ONLY reports for financial analysis.
No ledger mutations, no auto reconciliation, no invoice modifications.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func, extract
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel
from collections import defaultdict

from app.db.models import Invoice, InvoiceStatus, IncomeTransaction
from app.db.models.income_transaction import LedgerStatus
from app.db.models.user import User
from app.core.deps import get_db, require_admin_or_accounting
from app.core.timezone import BANGKOK_TZ


router = APIRouter(prefix="/api/reports", tags=["reports"])


# ============================================
# Aging Buckets Definition (locked)
# ============================================
AGING_BUCKETS = {
    "0_30": (0, 30),
    "31_60": (31, 60),
    "61_90": (61, 90),
    "90_plus": (91, float('inf'))
}


def get_bucket_name(days_past_due: int) -> str:
    """Determine which aging bucket a given days_past_due falls into"""
    if days_past_due < 0:
        return "current"  # Not yet due
    elif days_past_due <= 30:
        return "0_30"
    elif days_past_due <= 60:
        return "31_60"
    elif days_past_due <= 90:
        return "61_90"
    else:
        return "90_plus"


# ============================================
# Pydantic Schemas
# ============================================

class AgingRow(BaseModel):
    """Single invoice row in aging report"""
    invoice_id: int
    house: str
    house_id: int
    owner_name: Optional[str] = None
    due_date: str
    days_past_due: int
    outstanding: float
    bucket: str
    cycle: Optional[str] = None  # e.g., "2026-01" or "Manual"


class AgingSummary(BaseModel):
    """Summary totals by bucket"""
    current: float = 0  # Not yet due
    bucket_0_30: float = 0
    bucket_31_60: float = 0
    bucket_61_90: float = 0
    bucket_90_plus: float = 0
    total: float = 0


class InvoiceAgingResponse(BaseModel):
    """Full aging report response"""
    as_of: str
    summary: dict  # { "0_30": amount, "31_60": amount, ... }
    total_outstanding: float
    invoice_count: int
    rows: List[AgingRow]


# ============================================
# API Endpoint
# ============================================

@router.get("/invoice-aging", response_model=InvoiceAgingResponse)
async def get_invoice_aging_report(
    house_id: Optional[int] = Query(None, description="Filter by specific house"),
    as_of_date: Optional[str] = Query(None, description="Calculate aging as of this date (YYYY-MM-DD), default=today"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Get Invoice Aging Report.
    
    Shows all outstanding invoices grouped by aging buckets (days past due).
    
    - **house_id**: Filter by specific house
    - **as_of_date**: Calculate days past due as of this date (default: today)
    
    Only includes:
    - Currently outstanding invoices, regardless of stored status
    - outstanding_amount > 0 (after allocations and credit notes)
    
    READ-ONLY: Does not modify any data.
    """
    # Parse as_of_date or use today
    if as_of_date:
        try:
            report_date = date.fromisoformat(as_of_date)
        except ValueError:
            report_date = datetime.now(BANGKOK_TZ).date()
    else:
        report_date = datetime.now(BANGKOK_TZ).date()
    
    # Query invoices with outstanding amounts
    query = db.query(Invoice).options(
        joinedload(Invoice.house),
        joinedload(Invoice.payments),
        joinedload(Invoice.credit_notes)
    )
    
    # Apply house filter
    if house_id:
        query = query.filter(Invoice.house_id == house_id)
    
    # Order by due date (oldest first)
    query = query.order_by(Invoice.due_date.asc())
    
    invoices = query.all()
    
    # Process invoices and calculate aging
    rows: List[AgingRow] = []
    summary = {
        "current": Decimal(0),
        "0_30": Decimal(0),
        "31_60": Decimal(0),
        "61_90": Decimal(0),
        "90_plus": Decimal(0)
    }
    total_outstanding = Decimal(0)
    
    for inv in invoices:
        # Calculate outstanding (after payments and credits)
        outstanding = inv.get_remaining_balance_decimal()
        
        # Skip if nothing outstanding
        if outstanding <= 0:
            continue
        
        # Calculate days past due
        if inv.due_date:
            days_past_due = (report_date - inv.due_date).days
        else:
            days_past_due = 0
        
        # Determine bucket
        bucket = get_bucket_name(days_past_due)
        
        # Build cycle string
        if inv.is_manual:
            cycle_str = "Manual"
        elif inv.cycle_year and inv.cycle_month:
            cycle_str = f"{inv.cycle_year}-{inv.cycle_month:02d}"
        else:
            cycle_str = None
        
        # Create row
        row = AgingRow(
            invoice_id=inv.id,
            house=inv.house.house_code if inv.house else f"House#{inv.house_id}",
            house_id=inv.house_id,
            owner_name=inv.house.owner_name if inv.house else None,
            due_date=inv.due_date.isoformat() if inv.due_date else "",
            days_past_due=days_past_due,
            outstanding=round(outstanding, 2),
            bucket=bucket,
            cycle=cycle_str
        )
        rows.append(row)
        
        # Update summary
        summary[bucket] = summary.get(bucket, Decimal(0)) + outstanding
        total_outstanding += outstanding
    
    # Round summary values
    for key in summary:
        summary[key] = round(summary[key], 2)
    
    return InvoiceAgingResponse(
        as_of=report_date.isoformat(),
        summary=summary,
        total_outstanding=round(total_outstanding, 2),
        invoice_count=len(rows),
        rows=rows
    )


# ============================================
# Phase E.2: Cash Flow vs AR Report
# ============================================

class CashFlowRow(BaseModel):
    """Single row in cash flow vs AR report"""
    period: str  # e.g., "2026-01" for monthly
    ar_amount: float  # Accrual (invoices issued - credits)
    cash_amount: float  # Cash received (POSTED receipts)
    gap: float  # AR - Cash
    gap_percent: Optional[float] = None  # gap / AR * 100


class CashFlowSummary(BaseModel):
    """Summary totals for cash flow report"""
    total_ar: float
    total_cash: float
    total_gap: float
    gap_percent: Optional[float] = None


class CashFlowResponse(BaseModel):
    """Full cash flow vs AR response"""
    from_date: str
    to_date: str
    group_by: str  # "month" or "week"
    summary: CashFlowSummary
    rows: List[CashFlowRow]
    # Additional context
    invoice_count: int
    payin_count: int


@router.get("/cashflow-vs-ar", response_model=CashFlowResponse)
async def get_cashflow_vs_ar_report(
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), default=first of current year"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD), default=today"),
    house_id: Optional[int] = Query(None, description="Filter by specific house"),
    group_by: str = Query("month", description="Group by: 'month' or 'week'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Get Cash Flow vs AR (Accrual) Report.
    
    Compares:
    - **AR (Accrual)**: Invoice amounts issued (total - credits) grouped by issue_date
    - **Cash**: Pay-in amounts received (ACCEPTED only) grouped by transfer_date
    - **Gap**: AR - Cash (positive = under-collected, negative = over-collected)
    
    READ-ONLY: Does not modify any data.
    
    Business Rules:
    - Credits reduce AR only (not cash)
    - FIFO allocation does NOT affect cash totals
    - Only POSTED ledger receipts count as cash, including Statement-only receipts
    """
    # Parse dates
    today = datetime.now(BANGKOK_TZ).date()
    
    if from_date:
        try:
            start_date = date.fromisoformat(from_date)
        except ValueError:
            start_date = date(today.year, 1, 1)
    else:
        start_date = date(today.year, 1, 1)
    
    if to_date:
        try:
            end_date = date.fromisoformat(to_date)
        except ValueError:
            end_date = today
    else:
        end_date = today
    
    # Ensure valid range
    if end_date < start_date:
        end_date = start_date
    
    # ========================================
    # 1. Calculate AR (Invoices - Credits)
    # ========================================
    invoice_query = db.query(Invoice).options(
        joinedload(Invoice.credit_notes)
    ).filter(
        Invoice.issue_date >= start_date,
        Invoice.issue_date <= end_date,
        Invoice.status != InvoiceStatus.CANCELLED
    )
    
    if house_id:
        invoice_query = invoice_query.filter(Invoice.house_id == house_id)
    
    invoices = invoice_query.all()
    
    # Group AR by period
    ar_by_period = defaultdict(Decimal)
    invoice_count = 0
    
    for inv in invoices:
        invoice_count += 1
        # AR = total - credits
        total = Decimal(inv.total_amount)
        credits = inv.get_total_credited_decimal()
        ar_amount = total - credits
        
        # Get period key
        if group_by == "week":
            # ISO week number
            period_key = inv.issue_date.strftime("%Y-W%W")
        else:
            # Monthly (default)
            period_key = inv.issue_date.strftime("%Y-%m")
        
        ar_by_period[period_key] += ar_amount
    
    # ========================================
    # 2. Confirmed cash is POSTED ledger money, including Statement-only receipts.
    receipts = db.query(IncomeTransaction).filter(
        IncomeTransaction.status == LedgerStatus.POSTED,
        IncomeTransaction.received_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=BANGKOK_TZ),
        IncomeTransaction.received_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=BANGKOK_TZ),
    )
    if house_id:
        receipts = receipts.filter(IncomeTransaction.house_id == house_id)
    cash_by_period = defaultdict(Decimal)
    payin_count = 0  # Legacy response key: counts confirmed receipts, including no-slip receipts.
    for receipt in receipts.all():
        payin_count += 1
        received_local = receipt.received_at.astimezone(BANGKOK_TZ)
        period_key = received_local.strftime('%Y-W%W' if group_by == 'week' else '%Y-%m')
        cash_by_period[period_key] += Decimal(receipt.amount)

    # 3. Combine AR and Cash into rows
    # ========================================
    all_periods = sorted(set(ar_by_period.keys()) | set(cash_by_period.keys()))
    
    rows: List[CashFlowRow] = []
    total_ar = Decimal(0)
    total_cash = Decimal(0)
    
    for period in all_periods:
        ar = ar_by_period.get(period, Decimal(0))
        cash = cash_by_period.get(period, Decimal(0))
        gap = ar - cash
        gap_pct = (gap / ar * 100) if ar > 0 else None
        
        rows.append(CashFlowRow(
            period=period,
            ar_amount=round(ar, 2),
            cash_amount=round(cash, 2),
            gap=round(gap, 2),
            gap_percent=round(gap_pct, 1) if gap_pct is not None else None
        ))
        
        total_ar += ar
        total_cash += cash
    
    total_gap = total_ar - total_cash
    total_gap_pct = (total_gap / total_ar * 100) if total_ar > 0 else None
    
    return CashFlowResponse(
        from_date=start_date.isoformat(),
        to_date=end_date.isoformat(),
        group_by=group_by,
        summary=CashFlowSummary(
            total_ar=round(total_ar, 2),
            total_cash=round(total_cash, 2),
            total_gap=round(total_gap, 2),
            gap_percent=round(total_gap_pct, 1) if total_gap_pct is not None else None
        ),
        rows=rows,
        invoice_count=invoice_count,
        payin_count=payin_count
    )
