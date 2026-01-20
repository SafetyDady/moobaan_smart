"""
Phase F.2: Chart of Accounts (COA Lite) API

Endpoints:
- GET /api/accounts - List accounts (with filters)
- POST /api/accounts - Create account
- PUT /api/accounts/{id} - Update account (name, active only)
- DELETE /api/accounts/{id} - Soft delete (set active=false)
- GET /api/accounts/export - Export to CSV

IMPORTANT: This is COA LITE - NO GL, NO posting, NO balance tracking
Purpose: Classification, Reporting, Excel Export only

RBAC:
- READ: super_admin, admin, accounting
- CREATE/UPDATE: super_admin, admin
- DELETE: super_admin only
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import csv
import io

from app.db.session import get_db
from app.db.models import ChartOfAccount, AccountType, Expense, Invoice, User
from app.core.deps import require_admin_or_accounting, require_admin, require_roles


router = APIRouter(prefix="/api/accounts", tags=["accounts"])


# ============================================
# Pydantic Schemas
# ============================================

class AccountCreate(BaseModel):
    """Schema for creating an account"""
    account_code: str = Field(..., min_length=1, max_length=20, description="Unique account code (e.g., '4101')")
    account_name: str = Field(..., min_length=1, max_length=255, description="Account name")
    account_type: str = Field(..., description="Account type: ASSET, LIABILITY, REVENUE, EXPENSE")


class AccountUpdate(BaseModel):
    """Schema for updating an account (code is immutable)"""
    account_name: Optional[str] = Field(None, min_length=1, max_length=255)
    active: Optional[bool] = None


class AccountResponse(BaseModel):
    """Response schema for an account"""
    id: int
    account_code: str
    account_name: str
    account_type: str
    active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Usage counts (for reference)
    expense_count: Optional[int] = 0
    invoice_count: Optional[int] = 0


# ============================================
# List Accounts
# ============================================
@router.get("")
async def list_accounts(
    account_type: Optional[str] = Query(None, description="Filter by type: ASSET, LIABILITY, REVENUE, EXPENSE"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    List all accounts with optional filters.
    
    Permission: super_admin, admin, accounting
    """
    query = db.query(ChartOfAccount)
    
    # Apply type filter
    if account_type:
        try:
            type_enum = AccountType(account_type.upper())
            query = query.filter(ChartOfAccount.account_type == type_enum)
        except ValueError:
            pass
    
    # Apply active filter
    if active is not None:
        query = query.filter(ChartOfAccount.active == active)
    
    # Order by account_code
    query = query.order_by(ChartOfAccount.account_code)
    
    accounts = query.all()
    
    # Get usage counts for each account
    result = []
    for acc in accounts:
        expense_count = db.query(func.count(Expense.id)).filter(Expense.account_id == acc.id).scalar() or 0
        invoice_count = db.query(func.count(Invoice.id)).filter(Invoice.revenue_account_id == acc.id).scalar() or 0
        
        result.append({
            **acc.to_dict(),
            "expense_count": expense_count,
            "invoice_count": invoice_count,
        })
    
    return {
        "accounts": result,
        "total_count": len(result)
    }


# ============================================
# Get Account Types (helper) - MUST be before /{account_id}
# ============================================
@router.get("/meta/types")
async def get_account_types(
    current_user: User = Depends(require_admin_or_accounting)
):
    """Get available account types."""
    return {
        "types": [t.value for t in AccountType]
    }


# ============================================
# Export to CSV - MUST be before /{account_id}
# ============================================
@router.get("/export/csv")
async def export_accounts_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Export all accounts to CSV for Excel/accountant use.
    
    Permission: super_admin, admin, accounting
    
    Columns: account_code, account_name, account_type, active
    """
    accounts = db.query(ChartOfAccount).order_by(ChartOfAccount.account_code).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow(['account_code', 'account_name', 'account_type', 'active'])
    
    # Data rows
    for acc in accounts:
        writer.writerow([
            acc.account_code,
            acc.account_name,
            acc.account_type.value if acc.account_type else '',
            'Yes' if acc.active else 'No'
        ])
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=chart_of_accounts_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


# ============================================
# Get Single Account
# ============================================
@router.get("/{account_id}")
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Get a specific account by ID.
    
    Permission: super_admin, admin, accounting
    """
    account = db.query(ChartOfAccount).filter(ChartOfAccount.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get usage counts
    expense_count = db.query(func.count(Expense.id)).filter(Expense.account_id == account.id).scalar() or 0
    invoice_count = db.query(func.count(Invoice.id)).filter(Invoice.revenue_account_id == account.id).scalar() or 0
    
    return {
        **account.to_dict(),
        "expense_count": expense_count,
        "invoice_count": invoice_count,
    }


# ============================================
# Create Account
# ============================================
@router.post("")
async def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new account.
    
    Permission: super_admin, admin only
    
    Rules:
    - account_code must be unique
    - account_type must be valid enum
    """
    # Validate account_type
    try:
        account_type_enum = AccountType(data.account_type.upper())
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid account type: {data.account_type}. Must be ASSET, LIABILITY, REVENUE, or EXPENSE"
        )
    
    # Check unique account_code
    existing = db.query(ChartOfAccount).filter(
        ChartOfAccount.account_code == data.account_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Account code '{data.account_code}' already exists"
        )
    
    # Create account
    account = ChartOfAccount(
        account_code=data.account_code,
        account_name=data.account_name,
        account_type=account_type_enum,
        active=True
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return {
        **account.to_dict(),
        "message": "Account created successfully"
    }


# ============================================
# Update Account
# ============================================
@router.put("/{account_id}")
async def update_account(
    account_id: int,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update an existing account.
    
    Permission: super_admin, admin only
    
    Rules:
    - account_code is IMMUTABLE (cannot be changed)
    - account_type is IMMUTABLE (cannot be changed)
    - Only account_name and active can be updated
    """
    account = db.query(ChartOfAccount).filter(ChartOfAccount.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Update allowed fields only
    if data.account_name is not None:
        account.account_name = data.account_name
    
    if data.active is not None:
        account.active = data.active
    
    db.commit()
    db.refresh(account)
    
    return {
        **account.to_dict(),
        "message": "Account updated successfully"
    }


# ============================================
# Delete (Soft Delete) Account
# ============================================
@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin"]))
):
    """
    Soft delete an account (set active=false).
    
    Permission: super_admin only
    
    Rules:
    - Cannot delete if account is in use by expenses or invoices
    - Soft delete only (active=false), not hard delete
    """
    account = db.query(ChartOfAccount).filter(ChartOfAccount.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if in use
    expense_count = db.query(func.count(Expense.id)).filter(Expense.account_id == account.id).scalar() or 0
    invoice_count = db.query(func.count(Invoice.id)).filter(Invoice.revenue_account_id == account.id).scalar() or 0
    
    if expense_count > 0 or invoice_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete account: in use by {expense_count} expenses and {invoice_count} invoices"
        )
    
    # Soft delete
    account.active = False
    db.commit()
    
    return {
        "message": f"Account '{account.account_code}' has been disabled",
        "id": account.id
    }
