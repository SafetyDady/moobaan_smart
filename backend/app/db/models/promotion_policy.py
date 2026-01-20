"""
Phase D.4: PromotionPolicy Model

Promotion policies define rules for suggesting credit notes.
They are ADVISORY ONLY - they never auto-apply credits.

Key principles:
- Promotions suggest, never auto-create
- Pure evaluation logic with no side effects
- No hard-coded amounts or periods
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from decimal import Decimal
from datetime import date
import enum


class PromotionScope(enum.Enum):
    PROJECT = "project"    # Applies to entire project
    VILLAGE = "village"    # Applies to specific village
    HOUSE = "house"        # Applies to specific house


class PromotionStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"


class PromotionPolicy(Base):
    __tablename__ = "promotion_policies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Validity period
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=False)
    
    # Eligibility criteria
    min_payin_amount = Column(Numeric(12, 2), nullable=True)
    
    # Credit calculation (one of these must be set)
    credit_amount = Column(Numeric(10, 2), nullable=True)    # Fixed amount
    credit_percent = Column(Numeric(5, 2), nullable=True)    # Percentage (0-100)
    
    # Limits
    max_credit_total = Column(Numeric(12, 2), nullable=True)
    
    # Scope
    scope = Column(
        PgEnum('project', 'village', 'house', name='promotion_scope', create_type=False),
        nullable=False,
        default='project'
    )
    scope_id = Column(Integer, nullable=True)  # References village or house ID if scoped
    
    # Status
    status = Column(
        PgEnum('active', 'expired', 'disabled', name='promotion_status', create_type=False),
        nullable=False,
        default='active'
    )
    
    # Audit
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")
    
    # Table constraints are defined in migration

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "min_payin_amount": float(self.min_payin_amount) if self.min_payin_amount else None,
            "credit_amount": float(self.credit_amount) if self.credit_amount else None,
            "credit_percent": float(self.credit_percent) if self.credit_percent else None,
            "max_credit_total": float(self.max_credit_total) if self.max_credit_total else None,
            "scope": self.scope if isinstance(self.scope, str) else self.scope,
            "scope_id": self.scope_id,
            "status": self.status if isinstance(self.status, str) else self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_active(self) -> bool:
        """Check if promotion is currently active"""
        if self.status != 'active':
            return False
        today = date.today()
        return self.valid_from <= today <= self.valid_to

    def calculate_suggested_credit(self, payin_amount: float) -> float:
        """
        Calculate suggested credit based on promotion rules.
        
        PURE FUNCTION - no side effects, no database writes.
        
        Returns suggested credit amount (not guaranteed, just suggestion).
        """
        # Ensure we work with floats
        payin_amount = float(payin_amount) if payin_amount else 0
        
        if self.credit_amount:
            # Fixed amount
            suggested = float(self.credit_amount)
        elif self.credit_percent:
            # Percentage of pay-in
            suggested = payin_amount * (float(self.credit_percent) / 100)
        else:
            return 0
        
        # Apply max limit if set
        if self.max_credit_total:
            suggested = min(suggested, float(self.max_credit_total))
        
        return round(suggested, 2)

    def check_eligibility(self, payin_amount: float, paid_at: date, house_id: int = None) -> dict:
        """
        Check if a pay-in is eligible for this promotion.
        
        PURE FUNCTION - returns evaluation result only, no side effects.
        
        Args:
            payin_amount: Amount of the pay-in
            paid_at: Date when pay-in was made
            house_id: House ID for scope checking
            
        Returns:
            dict with eligible, reason, and suggested_credit
        """
        # 1. Check status
        if self.status != 'active':
            return {
                "eligible": False,
                "reason": f"Promotion is {self.status}",
                "suggested_credit": 0
            }
        
        # 2. Check date range
        # Note: valid_to is INCLUSIVE (last day promotion is valid)
        # All dates are in server timezone (no timezone conversion)
        if not (self.valid_from <= paid_at <= self.valid_to):
            return {
                "eligible": False,
                "reason": f"Pay-in date {paid_at} outside promotion period ({self.valid_from} to {self.valid_to}, inclusive)",
                "suggested_credit": 0
            }
        
        # 3. Check minimum amount
        if self.min_payin_amount and payin_amount < float(self.min_payin_amount):
            return {
                "eligible": False,
                "reason": f"Pay-in amount ฿{payin_amount:,.2f} below minimum ฿{float(self.min_payin_amount):,.2f}",
                "suggested_credit": 0
            }
        
        # 4. Check scope
        if self.scope == 'house' and self.scope_id:
            if house_id != self.scope_id:
                return {
                    "eligible": False,
                    "reason": f"Promotion only valid for house ID {self.scope_id}",
                    "suggested_credit": 0
                }
        elif self.scope == 'village':
            # village_id does not exist in current House model
            # SAFETY: Return ineligible rather than guessing
            return {
                "eligible": False,
                "reason": "Village-scoped promotions not supported (no village_id in system)",
                "suggested_credit": 0
            }
        # 'project' scope applies to all houses
        
        # 5. Calculate suggested credit
        suggested = self.calculate_suggested_credit(payin_amount)
        
        return {
            "eligible": True,
            "reason": f"Eligible for {self.name} (valid until {self.valid_to})",
            "suggested_credit": suggested
        }
