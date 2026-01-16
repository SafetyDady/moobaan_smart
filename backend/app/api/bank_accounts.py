"""
Bank Accounts API - System-level resource endpoints
Separate from bank-statements to maintain clean API contract
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import require_role
from app.db.models.user import User
from app.db.models.bank_account import BankAccount


router = APIRouter(prefix="/api/bank-accounts", tags=["bank-accounts"])


# ===== Request/Response Models =====

class BankAccountCreate(BaseModel):
    bank_code: str
    account_no_masked: str
    account_type: str = "CASHFLOW"
    currency: str = "THB"


class BankAccountResponse(BaseModel):
    id: str
    bank_code: str
    account_no_masked: str
    account_type: str
    currency: str
    is_active: bool
    created_at: str
    updated_at: str


# ===== Endpoints =====

@router.get("", response_model=List[BankAccountResponse])
async def list_bank_accounts(
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """List all active bank accounts (system-level resource)"""
    accounts = db.query(BankAccount).filter(BankAccount.is_active == True).all()
    return [account.to_dict() for account in accounts]


@router.post("", response_model=BankAccountResponse, status_code=201)
async def create_bank_account(
    data: BankAccountCreate,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """Create a new bank account (system-level resource)"""
    account = BankAccount(
        bank_code=data.bank_code,
        account_no_masked=data.account_no_masked,
        account_type=data.account_type,
        currency=data.currency,
        is_active=True,
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return account.to_dict()


@router.get("/{account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    account_id: str,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """Get a specific bank account by ID"""
    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    return account.to_dict()


@router.patch("/{account_id}", response_model=BankAccountResponse)
async def update_bank_account(
    account_id: str,
    data: BankAccountCreate,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """Update a bank account"""
    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    account.bank_code = data.bank_code
    account.account_no_masked = data.account_no_masked
    account.account_type = data.account_type
    account.currency = data.currency
    
    db.commit()
    db.refresh(account)
    
    return account.to_dict()


@router.delete("/{account_id}")
async def deactivate_bank_account(
    account_id: str,
    current_user: User = Depends(require_role(["super_admin"])),
    db: Session = Depends(get_db),
):
    """Deactivate a bank account (soft delete)"""
    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    account.is_active = False
    db.commit()
    
    return {"message": "Bank account deactivated successfully"}
