"""
Phase 5.1: In-App Notification Model

Purpose:
- Store notifications for users (admin + resident)
- Track read/unread status
- Support different notification types (invoice, payment, system)

IMPORTANT:
- Additive only — no changes to existing tables
- Soft-delete via is_deleted flag (no hard delete)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class NotificationType(str, enum.Enum):
    """Notification type categories"""
    INVOICE_CREATED = "INVOICE_CREATED"           # New invoice for resident
    INVOICE_OVERDUE = "INVOICE_OVERDUE"            # Invoice past due date
    PAYIN_SUBMITTED = "PAYIN_SUBMITTED"            # Resident submitted payin (for admin)
    PAYIN_ACCEPTED = "PAYIN_ACCEPTED"              # Admin accepted payin (for resident)
    PAYIN_REJECTED = "PAYIN_REJECTED"              # Admin rejected payin (for resident)
    EXPENSE_CREATED = "EXPENSE_CREATED"            # New expense recorded
    SYSTEM = "SYSTEM"                              # System-level notification


class Notification(Base):
    """In-app notification for users"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Target user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Notification content
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Optional reference to related entity
    reference_type = Column(String(50), nullable=True)   # "invoice", "payin", "expense"
    reference_id = Column(Integer, nullable=True)         # ID of the related entity

    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value if self.type else None,
            "title": self.title,
            "message": self.message,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
