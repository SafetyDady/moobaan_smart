from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from app.core.timezone import utc_now
from app.models import Expense, ExpenseCreate, ExpenseUpdate, ExpenseStatus
from app.mock_data import MOCK_EXPENSES

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

# In-memory storage
expenses_db = list(MOCK_EXPENSES)
next_id = max([e.id for e in expenses_db]) + 1


@router.get("", response_model=List[Expense])
async def list_expenses(status: str = None, category: str = None):
    """List all expenses with optional filters"""
    result = expenses_db
    
    if status:
        result = [e for e in result if e.status.value == status]
    
    if category:
        result = [e for e in result if e.category == category]
    
    return sorted(result, key=lambda x: x.date, reverse=True)


@router.get("/{expense_id}", response_model=Expense)
async def get_expense(expense_id: int):
    """Get a specific expense by ID"""
    expense = next((e for e in expenses_db if e.id == expense_id), None)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.post("", response_model=Expense)
async def create_expense(expense: ExpenseCreate):
    """Create a new expense"""
    global next_id
    
    new_expense = Expense(
        id=next_id,
        date=expense.date,
        category=expense.category,
        amount=expense.amount,
        description=expense.description,
        receipt_url=expense.receipt_url,
        status=ExpenseStatus.DRAFT,
        created_at=utc_now(),
        updated_at=utc_now()
    )
    expenses_db.append(new_expense)
    next_id += 1
    return new_expense


@router.put("/{expense_id}", response_model=Expense)
async def update_expense(expense_id: int, expense: ExpenseUpdate):
    """Update an existing expense"""
    existing = next((e for e in expenses_db if e.id == expense_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Update fields if provided
    if expense.date is not None:
        existing.date = expense.date
    if expense.category is not None:
        existing.category = expense.category
    if expense.amount is not None:
        existing.amount = expense.amount
    if expense.description is not None:
        existing.description = expense.description
    if expense.receipt_url is not None:
        existing.receipt_url = expense.receipt_url
    if expense.status is not None:
        existing.status = expense.status
    
    existing.updated_at = utc_now()
    return existing


@router.delete("/{expense_id}")
async def delete_expense(expense_id: int):
    """Delete an expense"""
    global expenses_db
    expense = next((e for e in expenses_db if e.id == expense_id), None)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    expenses_db = [e for e in expenses_db if e.id != expense_id]
    return {"message": "Expense deleted successfully"}
