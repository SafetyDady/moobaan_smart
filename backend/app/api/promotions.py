"""
Phase D.4: Promotion Policy API

Endpoints for promotion evaluation and management.

Key principles:
- Evaluate endpoint is READ-ONLY (no side effects)
- Never auto-create credits
- Suggest only, human decides
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field

from app.db.models import PromotionPolicy, PayinReport, PayinStatus
from app.db.models.user import User
from app.core.deps import get_db, require_admin_or_accounting, require_admin


router = APIRouter(prefix="/api/promotions", tags=["promotions"])


# ============================================
# Pydantic Schemas
# ============================================

class PromotionEvaluationResult(BaseModel):
    """Result of promotion eligibility evaluation - ADVISORY ONLY"""
    eligible: bool
    promotion_code: Optional[str] = None
    promotion_name: Optional[str] = None
    suggested_credit: float = 0
    reason: str
    # Additional context
    payin_id: int
    payin_amount: float


class PromotionPolicyResponse(BaseModel):
    """Promotion policy details"""
    id: int
    code: str
    name: str
    description: Optional[str]
    valid_from: str
    valid_to: str
    min_payin_amount: Optional[float]
    credit_amount: Optional[float]
    credit_percent: Optional[float]
    max_credit_total: Optional[float]
    scope: str
    scope_id: Optional[int]
    status: str
    created_at: Optional[str]


class PromotionPolicyCreate(BaseModel):
    """Schema for creating a promotion policy"""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    valid_from: str  # ISO date string
    valid_to: str    # ISO date string
    min_payin_amount: Optional[float] = None
    credit_amount: Optional[float] = None
    credit_percent: Optional[float] = Field(None, ge=0, le=100)
    max_credit_total: Optional[float] = None
    scope: str = "project"
    scope_id: Optional[int] = None


# ============================================
# Evaluation Service (Pure Logic)
# ============================================

def evaluate_promotion_for_payin(
    payin: PayinReport,
    db: Session
) -> PromotionEvaluationResult:
    """
    Evaluate if a pay-in qualifies for any active promotion.
    
    PURE EVALUATION - NO SIDE EFFECTS
    - Does NOT create credit notes
    - Does NOT modify any records
    - Only reads and calculates
    
    Returns advisory result for human decision.
    """
    payin_amount = float(payin.amount)
    paid_at = payin.transfer_date.date() if payin.transfer_date else date.today()
    house_id = payin.house_id
    
    # Find active promotions that could apply
    promotions = db.query(PromotionPolicy).filter(
        PromotionPolicy.status == 'active',
        PromotionPolicy.valid_from <= paid_at,
        PromotionPolicy.valid_to >= paid_at
    ).order_by(
        # Prefer higher credit, then more specific scope
        PromotionPolicy.credit_amount.desc().nullsfirst(),
        PromotionPolicy.credit_percent.desc().nullsfirst()
    ).all()
    
    if not promotions:
        return PromotionEvaluationResult(
            eligible=False,
            reason="No active promotions available",
            payin_id=payin.id,
            payin_amount=payin_amount
        )
    
    # Evaluate each promotion (first eligible wins)
    for promo in promotions:
        result = promo.check_eligibility(payin_amount, paid_at, house_id)
        
        if result["eligible"]:
            return PromotionEvaluationResult(
                eligible=True,
                promotion_code=promo.code,
                promotion_name=promo.name,
                suggested_credit=result["suggested_credit"],
                reason=result["reason"],
                payin_id=payin.id,
                payin_amount=payin_amount
            )
    
    # None eligible - return last failure reason
    return PromotionEvaluationResult(
        eligible=False,
        reason="Pay-in does not meet promotion criteria",
        payin_id=payin.id,
        payin_amount=payin_amount
    )


# ============================================
# API Endpoints
# ============================================

@router.get("/evaluate", response_model=PromotionEvaluationResult)
async def evaluate_promotion(
    payin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Evaluate if a pay-in qualifies for any active promotion.
    
    This is a READ-ONLY operation that:
    - Checks pay-in against active promotion rules
    - Returns suggested credit amount
    - Does NOT create any records
    
    Human must manually create Credit Note if desired.
    """
    # 1. Get pay-in
    payin = db.query(PayinReport).filter(PayinReport.id == payin_id).first()
    if not payin:
        raise HTTPException(status_code=404, detail="Pay-in not found")
    
    # 2. Verify pay-in is ACCEPTED (only accepted pay-ins can have credits)
    if payin.status != PayinStatus.ACCEPTED:
        return PromotionEvaluationResult(
            eligible=False,
            reason=f"Pay-in must be ACCEPTED (current: {payin.status.value})",
            payin_id=payin_id,
            payin_amount=float(payin.amount)
        )
    
    # 3. Evaluate (pure logic, no side effects)
    return evaluate_promotion_for_payin(payin, db)


@router.get("", response_model=List[PromotionPolicyResponse])
async def list_promotions(
    status: Optional[str] = None,
    include_expired: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    List promotion policies.
    
    Admin/Accounting can see all promotions.
    """
    query = db.query(PromotionPolicy)
    
    if status:
        query = query.filter(PromotionPolicy.status == status)
    elif not include_expired:
        # Default: only active promotions
        query = query.filter(PromotionPolicy.status == 'active')
    
    promotions = query.order_by(PromotionPolicy.valid_to.desc()).all()
    
    return [
        PromotionPolicyResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            valid_from=p.valid_from.isoformat() if p.valid_from else None,
            valid_to=p.valid_to.isoformat() if p.valid_to else None,
            min_payin_amount=float(p.min_payin_amount) if p.min_payin_amount else None,
            credit_amount=float(p.credit_amount) if p.credit_amount else None,
            credit_percent=float(p.credit_percent) if p.credit_percent else None,
            max_credit_total=float(p.max_credit_total) if p.max_credit_total else None,
            scope=p.scope if isinstance(p.scope, str) else p.scope,
            scope_id=p.scope_id,
            status=p.status if isinstance(p.status, str) else p.status,
            created_at=p.created_at.isoformat() if p.created_at else None
        )
        for p in promotions
    ]


@router.get("/{promotion_id}", response_model=PromotionPolicyResponse)
async def get_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """Get a single promotion by ID."""
    promo = db.query(PromotionPolicy).filter(PromotionPolicy.id == promotion_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    return PromotionPolicyResponse(
        id=promo.id,
        code=promo.code,
        name=promo.name,
        description=promo.description,
        valid_from=promo.valid_from.isoformat() if promo.valid_from else None,
        valid_to=promo.valid_to.isoformat() if promo.valid_to else None,
        min_payin_amount=float(promo.min_payin_amount) if promo.min_payin_amount else None,
        credit_amount=float(promo.credit_amount) if promo.credit_amount else None,
        credit_percent=float(promo.credit_percent) if promo.credit_percent else None,
        max_credit_total=float(promo.max_credit_total) if promo.max_credit_total else None,
        scope=promo.scope if isinstance(promo.scope, str) else promo.scope,
        scope_id=promo.scope_id,
        status=promo.status if isinstance(promo.status, str) else promo.status,
        created_at=promo.created_at.isoformat() if promo.created_at else None
    )


@router.post("", response_model=PromotionPolicyResponse, status_code=201)
async def create_promotion(
    data: PromotionPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new promotion policy.
    
    Admin only. Must specify either credit_amount or credit_percent.
    """
    from datetime import datetime
    
    # Validate credit type
    if data.credit_amount is None and data.credit_percent is None:
        raise HTTPException(
            status_code=400,
            detail="Must specify either credit_amount or credit_percent"
        )
    if data.credit_amount is not None and data.credit_percent is not None:
        raise HTTPException(
            status_code=400,
            detail="Cannot specify both credit_amount and credit_percent"
        )
    
    # Check code uniqueness
    existing = db.query(PromotionPolicy).filter(PromotionPolicy.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Promotion code '{data.code}' already exists")
    
    # Parse dates
    try:
        valid_from = datetime.fromisoformat(data.valid_from).date()
        valid_to = datetime.fromisoformat(data.valid_to).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")
    
    if valid_to < valid_from:
        raise HTTPException(status_code=400, detail="valid_to must be >= valid_from")
    
    # Create promotion
    promo = PromotionPolicy(
        code=data.code,
        name=data.name,
        description=data.description,
        valid_from=valid_from,
        valid_to=valid_to,
        min_payin_amount=data.min_payin_amount,
        credit_amount=data.credit_amount,
        credit_percent=data.credit_percent,
        max_credit_total=data.max_credit_total,
        scope=data.scope,
        scope_id=data.scope_id,
        status='active',
        created_by=current_user.id
    )
    
    db.add(promo)
    db.commit()
    db.refresh(promo)
    
    return PromotionPolicyResponse(
        id=promo.id,
        code=promo.code,
        name=promo.name,
        description=promo.description,
        valid_from=promo.valid_from.isoformat(),
        valid_to=promo.valid_to.isoformat(),
        min_payin_amount=float(promo.min_payin_amount) if promo.min_payin_amount else None,
        credit_amount=float(promo.credit_amount) if promo.credit_amount else None,
        credit_percent=float(promo.credit_percent) if promo.credit_percent else None,
        max_credit_total=float(promo.max_credit_total) if promo.max_credit_total else None,
        scope=promo.scope,
        scope_id=promo.scope_id,
        status=promo.status,
        created_at=promo.created_at.isoformat() if promo.created_at else None
    )
