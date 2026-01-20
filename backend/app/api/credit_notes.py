"""
Credit Notes API (Phase D.2)

Endpoints:
- POST /api/credit-notes — Create a credit note (Admin only)
- GET /api/credit-notes — List credit notes (optionally by invoice_id)

Rules:
- Credit notes are IMMUTABLE (no PUT/DELETE endpoints)
- credit_amount must be positive and <= remaining balance
- Invoice is NEVER modified
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.models import Invoice as InvoiceDB, CreditNote as CreditNoteDB
from app.db.models.user import User
from app.core.deps import get_db, require_admin_or_accounting


router = APIRouter(prefix="/api/credit-notes", tags=["credit-notes"])


# ============================================
# Pydantic Schemas
# ============================================

class CreditNoteCreate(BaseModel):
    invoice_id: int
    credit_amount: float = Field(..., gt=0, description="Amount to credit (must be positive)")
    reason: str = Field(..., min_length=1, description="Reason for credit note")
    is_full_credit: bool = Field(default=False, description="If true, credit entire remaining balance")


class CreditNoteResponse(BaseModel):
    id: int
    invoice_id: int
    credit_amount: float
    reason: str
    is_full_credit: bool
    status: str
    created_by_user_id: Optional[int]
    created_by_name: Optional[str]
    created_at: Optional[str]


# ============================================
# API Endpoints
# ============================================

@router.post("", response_model=CreditNoteResponse)
async def create_credit_note(
    data: CreditNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Create a credit note for an invoice.
    
    Permission: SUPER_ADMIN, ADMIN only
    
    Rules:
    - Invoice must exist
    - Invoice must not be fully credited already
    - credit_amount must be > 0 and <= remaining balance
    - If is_full_credit = true, credit_amount = net_amount
    
    IMPORTANT: Invoice record is NEVER modified.
    """
    # 1. Validate invoice exists
    invoice = db.query(InvoiceDB).filter(InvoiceDB.id == data.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # 2. Check if already fully credited
    if invoice.is_fully_credited():
        raise HTTPException(
            status_code=400, 
            detail="Invoice is already fully credited (cancelled)"
        )
    
    # 3. Calculate remaining creditable amount
    remaining_balance = invoice.get_remaining_balance()
    
    # 4. Determine credit amount
    if data.is_full_credit:
        # Full credit: use net amount (total - already credited)
        credit_amount = invoice.get_net_amount()
    else:
        credit_amount = data.credit_amount
    
    # 5. Validate credit amount
    if credit_amount <= 0:
        raise HTTPException(status_code=400, detail="Credit amount must be greater than 0")
    
    if credit_amount > invoice.get_net_amount():
        raise HTTPException(
            status_code=400, 
            detail=f"Credit amount (฿{credit_amount:,.2f}) exceeds remaining creditable amount (฿{invoice.get_net_amount():,.2f})"
        )
    
    # 6. Create credit note (IMMUTABLE after this point)
    credit_note = CreditNoteDB(
        invoice_id=data.invoice_id,
        credit_amount=Decimal(str(credit_amount)),
        reason=data.reason,
        is_full_credit=data.is_full_credit,
        status='applied',  # Use string value for PostgreSQL enum
        created_by_user_id=current_user.id
    )
    
    db.add(credit_note)
    db.commit()
    db.refresh(credit_note)
    
    return CreditNoteResponse(
        id=credit_note.id,
        invoice_id=credit_note.invoice_id,
        credit_amount=float(credit_note.credit_amount),
        reason=credit_note.reason,
        is_full_credit=credit_note.is_full_credit,
        status=credit_note.status if credit_note.status else "applied",  # status is string now
        created_by_user_id=credit_note.created_by_user_id,
        created_by_name=current_user.full_name,
        created_at=credit_note.created_at.isoformat() if credit_note.created_at else None
    )


@router.get("", response_model=List[CreditNoteResponse])
async def list_credit_notes(
    invoice_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    List credit notes, optionally filtered by invoice_id.
    
    Permission: SUPER_ADMIN, ADMIN, ACCOUNTING
    """
    query = db.query(CreditNoteDB)
    
    if invoice_id:
        query = query.filter(CreditNoteDB.invoice_id == invoice_id)
    
    query = query.order_by(CreditNoteDB.created_at.desc())
    
    credit_notes = query.all()
    
    result = []
    for cn in credit_notes:
        result.append(CreditNoteResponse(
            id=cn.id,
            invoice_id=cn.invoice_id,
            credit_amount=float(cn.credit_amount),
            reason=cn.reason,
            is_full_credit=cn.is_full_credit,
            status=cn.status if cn.status else "applied",  # status is now a string
            created_by_user_id=cn.created_by_user_id,
            created_by_name=cn.created_by.full_name if cn.created_by else None,
            created_at=cn.created_at.isoformat() if cn.created_at else None
        ))
    
    return result


@router.get("/{credit_note_id}", response_model=CreditNoteResponse)
async def get_credit_note(
    credit_note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Get a single credit note by ID.
    """
    cn = db.query(CreditNoteDB).filter(CreditNoteDB.id == credit_note_id).first()
    if not cn:
        raise HTTPException(status_code=404, detail="Credit note not found")
    
    return CreditNoteResponse(
        id=cn.id,
        invoice_id=cn.invoice_id,
        credit_amount=float(cn.credit_amount),
        reason=cn.reason,
        is_full_credit=cn.is_full_credit,
        status=cn.status if cn.status else "applied",  # status is now a string
        created_by_user_id=cn.created_by_user_id,
        created_by_name=cn.created_by.full_name if cn.created_by else None,
        created_at=cn.created_at.isoformat() if cn.created_at else None
    )


# NOTE: No PUT/DELETE endpoints - Credit notes are IMMUTABLE
