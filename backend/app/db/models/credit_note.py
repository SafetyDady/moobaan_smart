"""
Credit Note Model (Phase D.2)

Rules:
- Credit notes are IMMUTABLE (no update/delete after creation)
- credit_amount must be positive
- credit_amount cannot exceed invoice remaining balance
- is_full_credit = true means cancel entire invoice
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from app.db.session import Base
import enum


class CreditNoteStatus(enum.Enum):
    ISSUED = "issued"
    APPLIED = "applied"


class CreditNote(Base):
    __tablename__ = "credit_notes"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False)
    credit_amount = Column(Numeric(10, 2), nullable=False)  # Always positive
    reason = Column(Text, nullable=False)
    is_full_credit = Column(Boolean, nullable=False, default=False)
    status = Column(
        PgEnum('issued', 'applied', name='credit_note_status', create_type=False),
        nullable=False, 
        default='applied'
    )
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="credit_notes")
    created_by = relationship("User")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "credit_amount": float(self.credit_amount) if self.credit_amount else 0,
            "reason": self.reason,
            "is_full_credit": self.is_full_credit,
            "status": self.status if self.status else None,  # status is now a string
            "created_by_user_id": self.created_by_user_id,
            "created_by_name": self.created_by.full_name if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }