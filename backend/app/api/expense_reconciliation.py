"""
Expense ↔ Bank Allocation (Reconciliation) API

Endpoints:
- GET  /api/reconcile/expenses          — List expenses available for matching
- GET  /api/reconcile/bank-debits       — List bank debit transactions available for matching
- POST /api/reconcile/allocate          — Create an allocation (expense ↔ bank txn)
- DELETE /api/reconcile/allocate/{id}   — Remove an allocation
- GET  /api/reconcile/allocations       — List all allocations (with filters)

Business Rules:
- Only DEBIT transactions can be allocated to expenses
- SUM(matched_amount) for an expense must NOT exceed expense.amount
- SUM(matched_amount) for a bank txn must NOT exceed bank_transaction.debit
- When total_allocated == expense.amount → expense.status = PAID, paid_date set
- When total_allocated < expense.amount → expense.status = PENDING, paid_date cleared
- CANCELLED expenses cannot be allocated

RBAC: super_admin, accounting
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sa_func
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
import uuid

from app.db.session import get_db
from app.core.deps import require_role
from app.db.models.user import User
from app.db.models.expense import Expense, ExpenseStatus
from app.db.models.bank_transaction import BankTransaction
from app.db.models.expense_bank_allocation import ExpenseBankAllocation


router = APIRouter(prefix="/api/reconcile", tags=["expense-reconciliation"])


# ===== Pydantic Schemas =====

class AllocateRequest(BaseModel):
    expense_id: int
    bank_transaction_id: str  # UUID as string
    matched_amount: float = Field(..., gt=0)


class AllocateResponse(BaseModel):
    id: str
    expense_id: int
    bank_transaction_id: str
    matched_amount: float
    expense_new_status: str
    message: str


class RemoveResponse(BaseModel):
    success: bool
    message: str
    expense_id: int
    expense_new_status: str


# ===== Helper: get total allocated for expense =====

def _total_allocated_for_expense(db: Session, expense_id: int, exclude_alloc_id=None) -> Decimal:
    q = db.query(sa_func.coalesce(sa_func.sum(ExpenseBankAllocation.matched_amount), 0))
    q = q.filter(ExpenseBankAllocation.expense_id == expense_id)
    if exclude_alloc_id:
        q = q.filter(ExpenseBankAllocation.id != exclude_alloc_id)
    return q.scalar()


def _total_allocated_for_txn(db: Session, bank_transaction_id, exclude_alloc_id=None) -> Decimal:
    q = db.query(sa_func.coalesce(sa_func.sum(ExpenseBankAllocation.matched_amount), 0))
    q = q.filter(ExpenseBankAllocation.bank_transaction_id == bank_transaction_id)
    if exclude_alloc_id:
        q = q.filter(ExpenseBankAllocation.id != exclude_alloc_id)
    return q.scalar()


def _update_expense_status(db: Session, expense: Expense):
    """Recalculate expense status based on allocations."""
    total = _total_allocated_for_expense(db, expense.id)
    if total >= expense.amount:
        expense.status = ExpenseStatus.PAID
        # Set paid_date to latest bank txn effective_at
        latest = (
            db.query(sa_func.max(BankTransaction.effective_at))
            .join(ExpenseBankAllocation, ExpenseBankAllocation.bank_transaction_id == BankTransaction.id)
            .filter(ExpenseBankAllocation.expense_id == expense.id)
            .scalar()
        )
        if latest:
            expense.paid_date = latest.date() if hasattr(latest, 'date') else latest
    else:
        expense.status = ExpenseStatus.PENDING
        expense.paid_date = None


# ===== GET /api/reconcile/expenses =====

@router.get("/expenses")
async def list_reconcilable_expenses(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, PAID, ALL"),
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    List expenses available for reconciliation.
    Returns each expense with its current allocated total.
    """
    q = db.query(Expense).options(
        joinedload(Expense.vendor),
        joinedload(Expense.house),
    )

    if status and status.upper() == "PENDING":
        q = q.filter(Expense.status == ExpenseStatus.PENDING)
    elif status and status.upper() == "PAID":
        q = q.filter(Expense.status == ExpenseStatus.PAID)
    else:
        # Default: show PENDING + PAID (exclude CANCELLED)
        q = q.filter(Expense.status != ExpenseStatus.CANCELLED)

    q = q.order_by(Expense.expense_date.desc(), Expense.id.desc())
    expenses = q.all()

    # Batch-fetch allocated totals
    expense_ids = [e.id for e in expenses]
    alloc_totals = {}
    if expense_ids:
        rows = (
            db.query(
                ExpenseBankAllocation.expense_id,
                sa_func.sum(ExpenseBankAllocation.matched_amount).label("total_allocated"),
                sa_func.count(ExpenseBankAllocation.id).label("allocation_count"),
            )
            .filter(ExpenseBankAllocation.expense_id.in_(expense_ids))
            .group_by(ExpenseBankAllocation.expense_id)
            .all()
        )
        alloc_totals = {r.expense_id: {"total": float(r.total_allocated), "count": r.allocation_count} for r in rows}

    result = []
    for exp in expenses:
        d = exp.to_dict()
        info = alloc_totals.get(exp.id, {"total": 0, "count": 0})
        d["total_allocated"] = info["total"]
        d["allocation_count"] = info["count"]
        d["remaining"] = float(exp.amount) - info["total"]
        result.append(d)

    return result


# ===== GET /api/reconcile/bank-debits =====

@router.get("/bank-debits")
async def list_bank_debits(
    unallocated_only: bool = Query(False, description="Only show transactions with remaining capacity"),
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    List bank DEBIT transactions available for expense allocation.
    Returns each with allocated total and remaining capacity.
    """
    q = db.query(BankTransaction).filter(
        BankTransaction.debit.isnot(None),
        BankTransaction.debit > 0,
    ).order_by(BankTransaction.effective_at.desc())

    txns = q.all()

    # Batch-fetch allocated totals for all txns
    txn_ids = [t.id for t in txns]
    alloc_totals = {}
    if txn_ids:
        rows = (
            db.query(
                ExpenseBankAllocation.bank_transaction_id,
                sa_func.sum(ExpenseBankAllocation.matched_amount).label("total_allocated"),
                sa_func.count(ExpenseBankAllocation.id).label("allocation_count"),
            )
            .filter(ExpenseBankAllocation.bank_transaction_id.in_(txn_ids))
            .group_by(ExpenseBankAllocation.bank_transaction_id)
            .all()
        )
        alloc_totals = {r.bank_transaction_id: {"total": float(r.total_allocated), "count": r.allocation_count} for r in rows}

    result = []
    for txn in txns:
        d = txn.to_dict()
        info = alloc_totals.get(txn.id, {"total": 0, "count": 0})
        d["total_allocated"] = info["total"]
        d["allocation_count"] = info["count"]
        d["remaining"] = float(txn.debit) - info["total"]
        if unallocated_only and d["remaining"] <= 0:
            continue
        result.append(d)

    return result


# ===== POST /api/reconcile/allocate =====

@router.post("/allocate", response_model=AllocateResponse)
async def create_allocation(
    data: AllocateRequest,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Create an expense ↔ bank transaction allocation.

    Validates:
    1. Expense exists and is not CANCELLED
    2. Bank transaction exists and is a DEBIT
    3. matched_amount does not exceed expense remaining
    4. matched_amount does not exceed bank txn remaining debit
    5. No duplicate (expense_id, bank_transaction_id) pair
    """
    # Parse bank txn UUID
    try:
        txn_uuid = uuid.UUID(data.bank_transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bank_transaction_id format")

    matched_amount = Decimal(str(data.matched_amount))

    # 1. Get expense (FOR UPDATE — row lock to prevent race condition)
    expense = db.query(Expense).filter(Expense.id == data.expense_id).with_for_update().first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.status == ExpenseStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot allocate to a cancelled expense")

    # 2. Get bank transaction (FOR UPDATE — row lock to prevent race condition)
    bank_txn = db.query(BankTransaction).filter(BankTransaction.id == txn_uuid).with_for_update().first()
    if not bank_txn:
        raise HTTPException(status_code=404, detail="Bank transaction not found")
    if not bank_txn.debit or bank_txn.debit <= 0:
        raise HTTPException(status_code=400, detail="Only debit transactions can be allocated to expenses")

    # 3. Check expense remaining capacity
    expense_allocated = _total_allocated_for_expense(db, expense.id)
    expense_remaining = expense.amount - expense_allocated
    if matched_amount > expense_remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Amount {float(matched_amount)} exceeds expense remaining capacity {float(expense_remaining)}"
        )

    # 4. Check bank txn remaining capacity
    txn_allocated = _total_allocated_for_txn(db, txn_uuid)
    txn_remaining = bank_txn.debit - txn_allocated
    if matched_amount > txn_remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Amount {float(matched_amount)} exceeds bank transaction remaining debit {float(txn_remaining)}"
        )

    # 5. Check duplicate
    existing = db.query(ExpenseBankAllocation).filter(
        ExpenseBankAllocation.expense_id == data.expense_id,
        ExpenseBankAllocation.bank_transaction_id == txn_uuid,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Allocation already exists for this expense + bank transaction pair"
        )

    # Create allocation
    alloc = ExpenseBankAllocation(
        expense_id=data.expense_id,
        bank_transaction_id=txn_uuid,
        matched_amount=matched_amount,
    )
    db.add(alloc)

    # Recalculate expense status
    db.flush()  # ensure alloc is persisted before recalc
    _update_expense_status(db, expense)

    db.commit()
    db.refresh(alloc)
    db.refresh(expense)

    return AllocateResponse(
        id=str(alloc.id),
        expense_id=alloc.expense_id,
        bank_transaction_id=str(alloc.bank_transaction_id),
        matched_amount=float(alloc.matched_amount),
        expense_new_status=expense.status.value,
        message=f"Allocated ฿{float(matched_amount):,.2f} — expense is now {expense.status.value}",
    )


# ===== DELETE /api/reconcile/allocate/{id} =====

@router.delete("/allocate/{alloc_id}", response_model=RemoveResponse)
async def remove_allocation(
    alloc_id: str,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Remove an allocation. Recalculates expense status afterwards.
    """
    try:
        alloc_uuid = uuid.UUID(alloc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid allocation ID format")

    alloc = db.query(ExpenseBankAllocation).filter(ExpenseBankAllocation.id == alloc_uuid).first()
    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")

    expense_id = alloc.expense_id
    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    db.delete(alloc)
    db.flush()

    # Recalculate status
    if expense and expense.status != ExpenseStatus.CANCELLED:
        _update_expense_status(db, expense)

    db.commit()
    if expense:
        db.refresh(expense)

    return RemoveResponse(
        success=True,
        message="Allocation removed",
        expense_id=expense_id,
        expense_new_status=expense.status.value if expense else "UNKNOWN",
    )


# ===== GET /api/reconcile/allocations =====

@router.get("/allocations")
async def list_allocations(
    expense_id: Optional[int] = Query(None),
    bank_transaction_id: Optional[str] = Query(None),
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    List allocations with optional filters.
    """
    q = db.query(ExpenseBankAllocation).options(
        joinedload(ExpenseBankAllocation.expense),
        joinedload(ExpenseBankAllocation.bank_transaction),
    )

    if expense_id:
        q = q.filter(ExpenseBankAllocation.expense_id == expense_id)

    if bank_transaction_id:
        try:
            txn_uuid = uuid.UUID(bank_transaction_id)
            q = q.filter(ExpenseBankAllocation.bank_transaction_id == txn_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid bank_transaction_id format")

    q = q.order_by(ExpenseBankAllocation.created_at.desc())
    allocations = q.all()

    result = []
    for a in allocations:
        d = a.to_dict()
        if a.expense:
            d["expense_description"] = a.expense.description
            d["expense_amount"] = float(a.expense.amount) if a.expense.amount else 0
            d["expense_status"] = a.expense.status.value if a.expense.status else None
            d["expense_vendor_name"] = a.expense.vendor.name if a.expense.vendor else a.expense.vendor_name
        if a.bank_transaction:
            d["bank_description"] = a.bank_transaction.description
            d["bank_debit"] = float(a.bank_transaction.debit) if a.bank_transaction.debit else 0
            d["bank_effective_at"] = a.bank_transaction.effective_at.isoformat() if a.bank_transaction.effective_at else None
        result.append(d)

    return result
