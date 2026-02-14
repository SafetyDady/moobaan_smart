from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import DashboardSummary
from app.core.deps import get_db, get_current_user
from app.db.models import User, Invoice, HouseMember, House
from app.db.models.invoice import InvoiceStatus
from app.db.models.house import HouseStatus
from app.db.models.income_transaction import IncomeTransaction, LedgerStatus
from app.db.models.payin_report import PayinReport, PayinStatus
from decimal import Decimal
from datetime import datetime, date
from app.core.timezone import BANGKOK_TZ, utc_now

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
            Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID])
        ).all()
        
        total_outstanding = sum(inv.get_outstanding_amount() for inv in invoices)
        
        # Get total income (payments received) — only POSTED ledger entries
        income_transactions = db.query(IncomeTransaction).filter(
            IncomeTransaction.house_id == membership.house_id,
            IncomeTransaction.status == LedgerStatus.POSTED,
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
        
        invoices = db.query(Invoice).filter(
            Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID])
        ).all()
        total_outstanding = sum(inv.get_outstanding_amount() for inv in invoices)
        
        # Count overdue invoices (due_date < today and not paid)
        today = date.today()
        overdue_invoices = [inv for inv in invoices if inv.due_date and inv.due_date < today]
        
        # Get total income from all POSTED ledger entries
        income_transactions = db.query(IncomeTransaction).filter(
            IncomeTransaction.status == LedgerStatus.POSTED,
        ).all()
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
    from app.db.models.bank_transaction import BankTransaction
    from app.db.models.bank_statement_batch import BankStatementBatch
    from dateutil.relativedelta import relativedelta
    
    now = datetime.now(BANGKOK_TZ)
    # Current month boundaries (1st of month 00:00 → 1st of next month 00:00)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_end = current_month_start + relativedelta(months=1)
    
    # ── Latest bank statement balance ──
    latest_txn = db.query(BankTransaction)\
        .filter(BankTransaction.balance.isnot(None))\
        .order_by(BankTransaction.effective_at.desc())\
        .first()
    
    if latest_txn:
        total_balance = float(latest_txn.balance)
        balance_as_of = latest_txn.effective_at.isoformat() if latest_txn.effective_at else None
    else:
        total_balance = 0
        balance_as_of = None
    
    # ── Income & Expense from the latest confirmed bank statement batch ──
    latest_batch = db.query(BankStatementBatch)\
        .order_by(BankStatementBatch.year.desc(), BankStatementBatch.month.desc())\
        .first()
    
    if latest_batch:
        # Sum credit (income) and debit (expense) from all transactions in this batch
        month_income = db.query(func.coalesce(func.sum(BankTransaction.credit), 0))\
            .filter(BankTransaction.bank_statement_batch_id == latest_batch.id)\
            .scalar()
        
        month_expense = db.query(func.coalesce(func.sum(BankTransaction.debit), 0))\
            .filter(BankTransaction.bank_statement_batch_id == latest_batch.id)\
            .scalar()
        
        statement_period = f"{latest_batch.year}-{latest_batch.month:02d}"
    else:
        month_income = 0
        month_expense = 0
        statement_period = None
    
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
    
    # ── Monthly stats from BankStatementBatch (last 12 months) ──
    monthly_income = []
    thai_months = {
        1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
        7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."
    }
    
    from app.db.models.bank_statement_batch import BankStatementBatch as BSB
    monthly_rows = (
        db.query(
            BSB.year,
            BSB.month,
            func.coalesce(func.sum(BankTransaction.credit), 0).label("credit_total"),
            func.coalesce(func.sum(BankTransaction.debit), 0).label("debit_total"),
        )
        .join(BankTransaction, BankTransaction.bank_statement_batch_id == BSB.id)
        .filter(BSB.status.in_(["CONFIRMED", "PARSED"]))
        .group_by(BSB.year, BSB.month)
        .order_by(BSB.year.desc(), BSB.month.desc())
        .limit(12)
        .all()
    )
    
    # Reverse so oldest first
    for row in reversed(monthly_rows):
        y, m = row.year, row.month
        monthly_income.append({
            "period": f"{y}-{m:02d}",
            "label": f"{thai_months.get(m, str(m))}",
            "year_label": f"{(y + 543) % 100:02d}",
            "income": float(row.credit_total),
            "expense": float(row.debit_total),
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
    
    # ── Expense by category (last 3 months) ──
    # Query non-cancelled expenses grouped by category + month for the last 3 calendar months
    three_months_ago = (current_month_start - relativedelta(months=2)).date()  # include current + 2 prior
    
    cat_rows = (
        db.query(
            Expense.category,
            func.extract('year', Expense.expense_date).label('yr'),
            func.extract('month', Expense.expense_date).label('mo'),
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('cnt'),
        )
        .filter(
            Expense.status != ExpenseStatus.CANCELLED,
            Expense.expense_date >= three_months_ago,
        )
        .group_by(Expense.category, 'yr', 'mo')
        .order_by(func.extract('year', Expense.expense_date), func.extract('month', Expense.expense_date))
        .all()
    )
    
    # Build period list (last 3 months, oldest first)
    expense_periods = []
    for offset in [2, 1, 0]:
        dt = current_month_start - relativedelta(months=offset)
        y, m = dt.year, dt.month
        expense_periods.append({
            "period": f"{y}-{m:02d}",
            "label": thai_months.get(m, str(m)),
            "year_label": f"{(y + 543) % 100:02d}",
        })
    
    # Organise into { category: { "YYYY-MM": { total, count } } }
    cat_map = {}
    for row in cat_rows:
        cat = row.category or "OTHER"
        period_key = f"{int(row.yr)}-{int(row.mo):02d}"
        if cat not in cat_map:
            cat_map[cat] = {}
        cat_map[cat][period_key] = {"total": float(row.total), "count": int(row.cnt)}
    
    # Build final list sorted by total descending
    expense_by_category = []
    for cat, months_data in cat_map.items():
        grand = sum(v["total"] for v in months_data.values())
        monthly = []
        for p in expense_periods:
            d = months_data.get(p["period"], {"total": 0, "count": 0})
            monthly.append({
                "period": p["period"],
                "label": p["label"],
                "year_label": p["year_label"],
                "total": d["total"],
                "count": d["count"],
            })
        expense_by_category.append({
            "category": cat,
            "grand_total": grand,
            "monthly": monthly,
        })
    expense_by_category.sort(key=lambda x: x["grand_total"], reverse=True)
    
    return {
        "total_balance": total_balance,
        "balance_as_of": balance_as_of,
        "total_income": float(month_income),
        "total_expense": float(month_expense),
        "statement_period": statement_period,
        "debtor_count": debtor_count,
        "total_debt": total_debt,
        "monthly_income": monthly_income,
        "recent_activities": activities[:5],
        "expense_by_category": expense_by_category,
        "expense_periods": expense_periods,
    }
