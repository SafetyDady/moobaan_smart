"""
Phase F.1: Expense Core (Cash Out) API

Endpoints:
- GET /api/expenses - List expenses with filters
- POST /api/expenses - Create expense
- PUT /api/expenses/{id} - Update expense
- POST /api/expenses/{id}/mark-paid - Mark as paid
- POST /api/expenses/{id}/cancel - Cancel expense

RBAC:
- CREATE/UPDATE/MARK-PAID/CANCEL: super_admin, admin only
- READ: super_admin, admin, accounting
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal

from app.db.session import get_db
from app.db.models import Expense, ExpenseStatus, House, User, ChartOfAccount, AccountType
from app.db.models.vendor import Vendor
from app.core.deps import require_admin_or_accounting, require_admin, get_current_user
from app.core.period_lock import validate_period_not_locked


router = APIRouter(prefix="/api/expenses", tags=["expenses"])


# ============================================
# Pydantic Schemas
# ============================================

class ExpenseCreate(BaseModel):
    """Schema for creating an expense"""
    house_id: Optional[int] = Field(None, description="Related house ID (optional)")
    category: str = Field(..., min_length=1, max_length=100, description="Expense category")
    amount: float = Field(..., gt=0, description="Expense amount (must be > 0)")
    description: str = Field(..., min_length=1, max_length=255, description="Expense description")
    expense_date: date = Field(..., description="Date when expense occurred")
    vendor_name: Optional[str] = Field(None, max_length=255, description="Vendor name (auto-synced from vendor master)")
    vendor_id: int = Field(..., description="Vendor master ID (required for new expenses)")
    payment_method: Optional[str] = Field(None, max_length=50, description="CASH/TRANSFER/CHECK/OTHER")
    notes: Optional[str] = Field(None, description="Additional notes")
    account_id: Optional[int] = Field(None, description="Chart of Accounts ID (EXPENSE type)")


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense (only editable fields)"""
    house_id: Optional[int] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    expense_date: Optional[date] = None
    vendor_name: Optional[str] = Field(None, max_length=255)
    vendor_id: Optional[int] = Field(None, description="Vendor master ID (0 to clear)")
    payment_method: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    account_id: Optional[int] = Field(None, description="Chart of Accounts ID (0 to clear)")


class MarkPaidRequest(BaseModel):
    """Schema for marking expense as paid"""
    paid_date: date = Field(..., description="Date when expense was paid")
    payment_method: Optional[str] = Field(None, max_length=50, description="CASH/TRANSFER/CHECK/OTHER")


class ExpenseSummary(BaseModel):
    """Summary statistics for expense list"""
    total_paid: float
    total_pending: float
    count_paid: int
    count_pending: int
    count_cancelled: int


class ExpenseListResponse(BaseModel):
    """Response for expense list with summary"""
    expenses: List[dict]
    summary: ExpenseSummary
    total_count: int


# ============================================
# Expense Categories (reference)
# ============================================
EXPENSE_CATEGORIES = [
    "MAINTENANCE",
    "SECURITY", 
    "CLEANING",
    "UTILITIES",
    "ADMIN",
    "OTHER"
]


# ============================================
# List Expenses
# ============================================
@router.get("", response_model=ExpenseListResponse)
async def list_expenses(
    from_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING/PAID/CANCELLED)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    house_id: Optional[int] = Query(None, description="Filter by house"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    List all expenses with optional filters.
    
    Permission: super_admin, admin, accounting
    
    Filters:
    - from_date, to_date: filter by expense_date range
    - status: PENDING, PAID, CANCELLED
    - category: MAINTENANCE, SECURITY, CLEANING, UTILITIES, ADMIN, OTHER
    - house_id: filter by specific house
    """
    query = db.query(Expense).options(
        joinedload(Expense.house),
        joinedload(Expense.created_by),
        joinedload(Expense.vendor)  # Phase H.1.1
    )
    
    # Apply date range filter
    if from_date:
        try:
            start_date = date.fromisoformat(from_date)
            query = query.filter(Expense.expense_date >= start_date)
        except ValueError:
            pass
    
    if to_date:
        try:
            end_date = date.fromisoformat(to_date)
            query = query.filter(Expense.expense_date <= end_date)
        except ValueError:
            pass
    
    # Apply status filter
    if status:
        try:
            status_enum = ExpenseStatus(status)
            query = query.filter(Expense.status == status_enum)
        except ValueError:
            pass
    
    # Apply category filter
    if category:
        query = query.filter(Expense.category == category)
    
    # Apply house filter
    if house_id:
        query = query.filter(Expense.house_id == house_id)
    
    # Order by expense_date descending
    query = query.order_by(Expense.expense_date.desc(), Expense.id.desc())
    
    expenses = query.all()
    
    # Calculate summary
    total_paid = sum(float(e.amount) for e in expenses if e.status == ExpenseStatus.PAID)
    total_pending = sum(float(e.amount) for e in expenses if e.status == ExpenseStatus.PENDING)
    count_paid = sum(1 for e in expenses if e.status == ExpenseStatus.PAID)
    count_pending = sum(1 for e in expenses if e.status == ExpenseStatus.PENDING)
    count_cancelled = sum(1 for e in expenses if e.status == ExpenseStatus.CANCELLED)
    
    return ExpenseListResponse(
        expenses=[e.to_dict() for e in expenses],
        summary=ExpenseSummary(
            total_paid=round(total_paid, 2),
            total_pending=round(total_pending, 2),
            count_paid=count_paid,
            count_pending=count_pending,
            count_cancelled=count_cancelled
        ),
        total_count=len(expenses)
    )


# ============================================
# Get Single Expense
# ============================================
@router.get("/{expense_id}")
async def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Get a specific expense by ID.
    
    Permission: super_admin, admin, accounting
    """
    expense = db.query(Expense).options(
        joinedload(Expense.house),
        joinedload(Expense.created_by),
        joinedload(Expense.vendor)  # Phase H.1.1
    ).filter(Expense.id == expense_id).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return expense.to_dict()


# ============================================
# Create Expense
# ============================================
@router.post("")
async def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new expense.
    
    Permission: super_admin, admin only
    
    Rules:
    - amount > 0 (enforced by schema)
    - status defaults to PENDING
    - account_id must be EXPENSE type if provided
    """
    # Validate house if provided
    if data.house_id:
        house = db.query(House).filter(House.id == data.house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="House not found")
    
    # Phase G.1: Check period lock
    validate_period_not_locked(db, data.expense_date, "expense")
    
    # Validate account if provided (must be EXPENSE type)
    if data.account_id:
        account = db.query(ChartOfAccount).filter(ChartOfAccount.id == data.account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        if account.account_type != AccountType.EXPENSE:
            raise HTTPException(status_code=400, detail="Account must be EXPENSE type")
        if not account.active:
            raise HTTPException(status_code=400, detail="Account is inactive")
    
    # Phase H.1.1: Validate vendor and auto-sync vendor_name
    vendor = db.query(Vendor).filter(Vendor.id == data.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    if not vendor.is_active:
        raise HTTPException(status_code=400, detail="Vendor is inactive")
    synced_vendor_name = vendor.name  # Always sync from master
    
    # Create expense
    expense = Expense(
        house_id=data.house_id,
        category=data.category.upper(),  # Normalize to uppercase
        amount=Decimal(str(data.amount)),
        description=data.description,
        expense_date=data.expense_date,
        vendor_name=synced_vendor_name,  # Auto-synced from vendor master
        vendor_id=data.vendor_id,  # Phase H.1.1: Vendor master link
        payment_method=data.payment_method.upper() if data.payment_method else None,
        notes=data.notes,
        status=ExpenseStatus.PENDING,
        created_by_user_id=current_user.id,
        account_id=data.account_id  # Phase F.2: COA link
    )
    
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    # Load relationships for response
    db.refresh(expense)
    
    return {
        **expense.to_dict(),
        "message": "Expense created successfully"
    }


# ============================================
# Update Expense
# ============================================
@router.put("/{expense_id}")
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update an existing expense.
    
    Permission: super_admin, admin only
    
    Rules:
    - Cannot update CANCELLED expenses
    - Cannot update PAID expenses (except notes)
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense.status == ExpenseStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot update cancelled expense")
    
    # Phase G.1: Check period lock for original date
    validate_period_not_locked(db, expense.expense_date, "expense")
    
    # For PAID expenses, only allow updating notes
    if expense.status == ExpenseStatus.PAID:
        if data.notes is not None:
            expense.notes = data.notes
        else:
            raise HTTPException(status_code=400, detail="Can only update notes for paid expenses")
    else:
        # Update PENDING expense fields
        if data.house_id is not None:
            if data.house_id != 0:  # 0 means clear house_id
                house = db.query(House).filter(House.id == data.house_id).first()
                if not house:
                    raise HTTPException(status_code=404, detail="House not found")
                expense.house_id = data.house_id
            else:
                expense.house_id = None
        
        if data.category is not None:
            expense.category = data.category.upper()
        
        if data.amount is not None:
            expense.amount = Decimal(str(data.amount))
        
        if data.description is not None:
            expense.description = data.description
        
        if data.expense_date is not None:
            expense.expense_date = data.expense_date
        
        if data.vendor_id is not None:
            if data.vendor_id == 0:
                expense.vendor_id = None
                # Keep existing vendor_name as legacy fallback
            else:
                vendor_obj = db.query(Vendor).filter(Vendor.id == data.vendor_id).first()
                if vendor_obj:
                    expense.vendor_id = data.vendor_id
                    expense.vendor_name = vendor_obj.name  # Auto-sync from master
                else:
                    raise HTTPException(status_code=404, detail="Vendor not found")
        elif data.vendor_name is not None:
            # Only allow direct vendor_name update if no vendor_id change
            expense.vendor_name = data.vendor_name
        
        if data.payment_method is not None:
            expense.payment_method = data.payment_method.upper() if data.payment_method else None
        
        if data.notes is not None:
            expense.notes = data.notes
    
    # Handle account_id update (allowed for both PENDING and PAID)
    if data.account_id is not None:
        if data.account_id != 0:  # 0 means clear account_id
            account = db.query(ChartOfAccount).filter(ChartOfAccount.id == data.account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            if account.account_type != AccountType.EXPENSE:
                raise HTTPException(status_code=400, detail="Account must be EXPENSE type")
            expense.account_id = data.account_id
        else:
            expense.account_id = None
    
    db.commit()
    db.refresh(expense)
    
    return {
        **expense.to_dict(),
        "message": "Expense updated successfully"
    }


# ============================================
# Mark Expense as Paid
# ============================================
@router.post("/{expense_id}/mark-paid")
async def mark_expense_paid(
    expense_id: int,
    data: MarkPaidRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Mark expense as PAID.
    
    Permission: super_admin, admin only
    
    Rules:
    - Cannot mark-paid if status is CANCELLED
    - Cannot mark-paid if already PAID
    - paid_date cannot be earlier than expense_date
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense.status == ExpenseStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot mark cancelled expense as paid")
    
    if expense.status == ExpenseStatus.PAID:
        raise HTTPException(status_code=400, detail="Expense is already paid")
    
    # Validate paid_date >= expense_date
    if data.paid_date < expense.expense_date:
        raise HTTPException(
            status_code=400, 
            detail=f"Paid date ({data.paid_date}) cannot be earlier than expense date ({expense.expense_date})"
        )
    
    # Update expense
    expense.status = ExpenseStatus.PAID
    expense.paid_date = data.paid_date
    if data.payment_method:
        expense.payment_method = data.payment_method.upper()
    
    db.commit()
    db.refresh(expense)
    
    return {
        **expense.to_dict(),
        "message": "Expense marked as paid"
    }


# ============================================
# Cancel Expense
# ============================================
@router.post("/{expense_id}/cancel")
async def cancel_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Cancel an expense.
    
    Permission: super_admin, admin only
    
    Rules:
    - Cannot cancel if already PAID
    - Cannot cancel if already CANCELLED
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense.status == ExpenseStatus.PAID:
        raise HTTPException(status_code=400, detail="Cannot cancel paid expense")
    
    if expense.status == ExpenseStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Expense is already cancelled")
    
    # Update status
    expense.status = ExpenseStatus.CANCELLED
    
    db.commit()
    db.refresh(expense)
    
    return {
        **expense.to_dict(),
        "message": "Expense cancelled"
    }


# ============================================
# Get Categories (helper endpoint)
# ============================================
@router.get("/meta/categories")
async def get_expense_categories(
    current_user: User = Depends(require_admin_or_accounting)
):
    """Get available expense categories."""
    return {
        "categories": EXPENSE_CATEGORIES
    }
