from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import DashboardSummary
from app.core.deps import get_db, get_current_user
from app.db.models import User, Invoice, HouseMember, House
from app.db.models.invoice import InvoiceStatus
from app.db.models.house import HouseStatus
from app.db.models.income_transaction import IncomeTransaction
from app.db.models.payin_report import PayinReport, PayinStatus
from decimal import Decimal
from datetime import datetime, date

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary statistics for current user"""
    
    # For residents, get their house invoices
    if current_user.role == "resident":
        # Get user's house via HouseMember
        membership = db.query(HouseMember).filter(
            HouseMember.user_id == current_user.id
        ).first()
        
        if not membership:
            # No house assigned - return empty summary
            return DashboardSummary(
                current_balance=0.0,
                total_income=0.0,
                total_expenses=0.0,
                total_houses=0,
                active_houses=0,
                total_residents=0,
                pending_invoices=0,
                total_outstanding=0.0,
                pending_payins=0,
                overdue_invoices=0,
                recent_payments=0,
                monthly_revenue=0.0
            )
        
        # Get all unpaid invoices for user's house
        invoices = db.query(Invoice).filter(
            Invoice.house_id == membership.house_id,
            Invoice.status != InvoiceStatus.PAID
        ).all()
        
        total_outstanding = sum(float(inv.total_amount) for inv in invoices)
        
        # Get total income (payments received)
        income_transactions = db.query(IncomeTransaction).filter(
            IncomeTransaction.house_id == membership.house_id
        ).all()
        
        total_income = sum(float(inc.amount) for inc in income_transactions)
        
        # Calculate current balance (negative = house owes, positive = overpaid)
        current_balance = total_income - total_outstanding
        
        return DashboardSummary(
            current_balance=current_balance,
            total_income=total_income,
            total_expenses=0.0,    # TODO: Calculate from expense records
            total_houses=1,
            active_houses=1,
            total_residents=1,
            pending_invoices=len(invoices),
            total_outstanding=total_outstanding,
            pending_payins=0,      # TODO: Get from payin_reports
            overdue_invoices=0,    # TODO: Filter by due_date
            recent_payments=len(income_transactions),
            monthly_revenue=0.0
        )
    
    # For admins/accounting, show all data
    else:
        houses = db.query(House).all()
        active_houses = [h for h in houses if h.house_status == HouseStatus.ACTIVE]
        
        invoices = db.query(Invoice).filter(Invoice.status != InvoiceStatus.PAID).all()
        total_outstanding = sum(float(inv.total_amount) for inv in invoices)
        
        # Count overdue invoices (due_date < today and not paid)
        today = date.today()
        overdue_invoices = [inv for inv in invoices if inv.due_date and inv.due_date < today]
        
        # Get total income from all accepted payins
        income_transactions = db.query(IncomeTransaction).all()
        total_income = sum(float(inc.amount) for inc in income_transactions)
        
        # Count pending payins
        pending_payins = db.query(PayinReport).filter(
            PayinReport.status == PayinStatus.PENDING
        ).count()
        
        # Calculate current balance
        current_balance = total_income - total_outstanding
        
        return DashboardSummary(
            current_balance=current_balance,
            total_income=total_income,
            total_expenses=0.0,
            total_houses=len(houses),
            active_houses=len(active_houses),
            total_residents=db.query(HouseMember).count(),
            pending_invoices=len(invoices),
            total_outstanding=total_outstanding,
            pending_payins=pending_payins,
            overdue_invoices=len(overdue_invoices),
            recent_payments=len(income_transactions),
            monthly_revenue=0.0
        )


@router.get("/village-summary")
async def get_village_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get overall village financial summary (for residents)
    Shows aggregate statistics without exposing personal data (PDPA compliant)
    """
    from sqlalchemy import func, case
    from app.db.models.expense import Expense, ExpenseStatus
    from app.db.models.invoice_payment import InvoicePayment
    from dateutil.relativedelta import relativedelta
    
    now = datetime.now()
    # Current month boundaries (1st of month 00:00 → 1st of next month 00:00)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_end = current_month_start + relativedelta(months=1)
    
    # ── All-time totals for balance calculation ──
    all_time_income = db.query(func.coalesce(func.sum(IncomeTransaction.amount), 0))\
        .scalar()
    
    all_time_expense = db.query(func.coalesce(func.sum(Expense.amount), 0))\
        .filter(Expense.status != ExpenseStatus.CANCELLED)\
        .scalar()
    
    total_balance = float(all_time_income) - float(all_time_expense)
    
    # ── Current month income & expense ──
    month_income = db.query(func.coalesce(func.sum(IncomeTransaction.amount), 0))\
        .filter(
            IncomeTransaction.received_at >= current_month_start,
            IncomeTransaction.received_at < current_month_end
        ).scalar()
    
    month_expense = db.query(func.coalesce(func.sum(Expense.amount), 0))\
        .filter(
            Expense.status != ExpenseStatus.CANCELLED,
            Expense.expense_date >= current_month_start.date(),
            Expense.expense_date < current_month_end.date()
        ).scalar()
    
    # ── Debtor count & total debt (ISSUED or PARTIALLY_PAID invoices) ──
    # FIX: InvoiceStatus has no UNPAID — use ISSUED + PARTIALLY_PAID
    unpaid_statuses = [InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID]
    
    debtor_count = db.query(func.count(func.distinct(Invoice.house_id)))\
        .filter(Invoice.status.in_(unpaid_statuses))\
        .scalar() or 0
    
    # FIX: Calculate actual remaining debt (total_amount - paid - credited)
    # Use subquery to get paid amounts per invoice
    paid_subq = db.query(
        InvoicePayment.invoice_id,
        func.coalesce(func.sum(InvoicePayment.amount), 0).label("total_paid")
    ).group_by(InvoicePayment.invoice_id).subquery()
    
    total_debt_rows = db.query(
        Invoice.total_amount,
        func.coalesce(paid_subq.c.total_paid, 0).label("paid")
    ).outerjoin(
        paid_subq, Invoice.id == paid_subq.c.invoice_id
    ).filter(
        Invoice.status.in_(unpaid_statuses)
    ).all()
    
    total_debt = sum(float(row.total_amount) - float(row.paid) for row in total_debt_rows)
    total_debt = max(0, total_debt)
    
    # ── Monthly income chart (last 4 months) ──
    monthly_income = []
    thai_months = {
        1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
        7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."
    }
    
    for i in range(4):
        # FIX: Use first-of-month boundaries, not mid-month offsets
        m_start = current_month_start - relativedelta(months=i)
        m_end = m_start + relativedelta(months=1)
        
        inc_amount = db.query(func.coalesce(func.sum(IncomeTransaction.amount), 0))\
            .filter(
                IncomeTransaction.received_at >= m_start,
                IncomeTransaction.received_at < m_end
            ).scalar()
        
        exp_amount = db.query(func.coalesce(func.sum(Expense.amount), 0))\
            .filter(
                Expense.status != ExpenseStatus.CANCELLED,
                Expense.expense_date >= m_start.date(),
                Expense.expense_date < m_end.date()
            ).scalar()
        
        monthly_income.append({
            "period": m_start.strftime("%Y-%m"),
            "label": thai_months.get(m_start.month, m_start.strftime("%b")),
            "amount": float(inc_amount),
            "expense": float(exp_amount),
        })
    
    # ── Recent activities (last 5 transactions) ──
    activities = []
    
    # Recent income with house info for description
    recent_income = db.query(IncomeTransaction)\
        .order_by(IncomeTransaction.received_at.desc())\
        .limit(3)\
        .all()
    
    for inc in recent_income:
        # FIX: IncomeTransaction has no 'period' field — derive from received_at
        month_label = thai_months.get(inc.received_at.month, "") if inc.received_at else ""
        activities.append({
            "icon": "🏠",
            "description": f"รับชำระค่าส่วนกลาง {month_label}".strip(),
            "timestamp": inc.received_at.strftime("%d/%m/%Y %H:%M") if inc.received_at else "",
            "sort_key": inc.received_at.isoformat() if inc.received_at else "",
            "amount": float(inc.amount),
            "type": "income"
        })
    
    # Recent expenses (FIX: exclude CANCELLED)
    recent_expenses = db.query(Expense)\
        .filter(Expense.status != ExpenseStatus.CANCELLED)\
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())\
        .limit(2)\
        .all()
    
    for exp in recent_expenses:
        exp_dt = exp.expense_date or exp.created_at
        activities.append({
            "icon": "💡",
            "description": exp.description or "รายจ่ายหมู่บ้าน",
            "timestamp": exp_dt.strftime("%d/%m/%Y") if exp_dt else "",
            "sort_key": (exp.expense_date.isoformat() if exp.expense_date 
                        else (exp.created_at.isoformat() if exp.created_at else "")),
            "amount": float(exp.amount),
            "type": "expense"
        })
    
    # Sort by sort_key (most recent first), then strip sort_key from output
    activities.sort(key=lambda x: x.get('sort_key', ''), reverse=True)
    for a in activities:
        a.pop('sort_key', None)
    
    return {
        "total_balance": total_balance,
        "total_income": float(month_income),
        "total_expense": float(month_expense),
        "debtor_count": debtor_count,
        "total_debt": total_debt,
        "monthly_income": monthly_income,
        "recent_activities": activities[:5]
    }
