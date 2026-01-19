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
    from sqlalchemy import func
    from app.db.models.expense import Expense
    from dateutil.relativedelta import relativedelta
    
    # Total income (from accepted income transactions)
    total_income = db.query(func.sum(IncomeTransaction.amount))\
        .scalar() or Decimal(0)
    
    # Total expenses
    total_expense = db.query(func.sum(Expense.amount))\
        .scalar() or Decimal(0)
    
    # Total balance
    total_balance = float(total_income) - float(total_expense)
    
    # Debtor count (houses with unpaid invoices)
    debtor_count = db.query(func.count(func.distinct(Invoice.house_id)))\
        .filter(Invoice.status == InvoiceStatus.UNPAID)\
        .scalar() or 0
    
    # Total debt (sum of unpaid invoices)
    total_debt = db.query(func.sum(Invoice.total_amount))\
        .filter(Invoice.status == InvoiceStatus.UNPAID)\
        .scalar() or Decimal(0)
    
    # Monthly income (last 3 months)
    monthly_income = []
    thai_months = {
        1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
        7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."
    }
    
    for i in range(3):
        month_start = datetime.now() - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)
        
        amount = db.query(func.sum(IncomeTransaction.amount))\
            .filter(
                IncomeTransaction.created_at >= month_start,
                IncomeTransaction.created_at < month_end
            )\
            .scalar() or Decimal(0)
        
        monthly_income.append({
            "period": month_start.strftime("%Y-%m"),
            "label": thai_months.get(month_start.month, month_start.strftime("%b")),
            "amount": float(amount)
        })
    
    # Recent activities (last 5 transactions, generic descriptions)
    activities = []
    
    # Get recent income transactions
    recent_income = db.query(IncomeTransaction)\
        .order_by(IncomeTransaction.created_at.desc())\
        .limit(3)\
        .all()
    
    for inc in recent_income:
        activities.append({
            "icon": "🏠",
            "description": f"รับชำระค่าส่วนกลาง {inc.period or ''}",
            "timestamp": inc.created_at.strftime("%d %b, %H:%M น.") if inc.created_at else "",
            "amount": float(inc.amount),
            "type": "income"
        })
    
    # Get recent expenses
    recent_expenses = db.query(Expense)\
        .order_by(Expense.created_at.desc())\
        .limit(2)\
        .all()
    
    for exp in recent_expenses:
        activities.append({
            "icon": "💡",
            "description": exp.description or "รายจ่ายหมู่บ้าน",
            "timestamp": exp.created_at.strftime("%d %b, %H:%M น.") if exp.created_at else "",
            "amount": float(exp.amount),
            "type": "expense"
        })
    
    # Sort by timestamp (most recent first)
    activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return {
        "total_balance": total_balance,
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "debtor_count": debtor_count,
        "total_debt": float(total_debt),
        "monthly_income": monthly_income,
        "recent_activities": activities[:5]
    }
