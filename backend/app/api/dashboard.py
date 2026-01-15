from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import DashboardSummary
from app.core.deps import get_db, get_current_user
from app.db.models import User, Invoice, HouseMember, House
from app.db.models.invoice import InvoiceStatus
from app.db.models.house import HouseStatus
from app.db.models.income_transaction import IncomeTransaction
from decimal import Decimal

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
        
        return DashboardSummary(
            current_balance=0.0,
            total_income=0.0,
            total_expenses=0.0,
            total_houses=len(houses),
            active_houses=len(active_houses),
            total_residents=db.query(HouseMember).count(),
            pending_invoices=len(invoices),
            total_outstanding=total_outstanding,
            pending_payins=0,
            overdue_invoices=0,
            recent_payments=0,
            monthly_revenue=0.0
        )
