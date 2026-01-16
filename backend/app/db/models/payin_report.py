from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class PayinStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class PayinReport(Base):
    __tablename__ = "payin_reports"

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    transfer_date = Column(DateTime(timezone=True), nullable=False)
    transfer_hour = Column(Integer, nullable=False)  # 0-23
    transfer_minute = Column(Integer, nullable=False)  # 0-59
    slip_url = Column(String(500), nullable=True)
    status = Column(Enum(PayinStatus), nullable=False, default=PayinStatus.PENDING)
    rejection_reason = Column(Text, nullable=True)
    accepted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # SUPER_ADMIN who accepted
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Reconciliation: 1:1 match with bank_transaction
    matched_statement_txn_id = Column(UUID(as_uuid=True), ForeignKey("bank_transactions.id", ondelete="SET NULL"), nullable=True, unique=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    house = relationship("House")
    submitted_by = relationship("User", foreign_keys=[submitted_by_user_id])
    accepted_by_user = relationship("User", foreign_keys=[accepted_by])
    income_transaction = relationship("IncomeTransaction", uselist=False, back_populates="payin")
    # 1:1 with BankTransaction - ONLY declare on PayinReport side (has the FK)
    matched_statement_txn = relationship("BankTransaction", foreign_keys=[matched_statement_txn_id], uselist=False)

    def to_dict(self):
        """Convert model to dictionary matching frontend expectations"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "house_code": self.house.house_code if self.house else None,
            "submitted_by_user_id": self.submitted_by_user_id,
            "submitted_by_name": self.submitted_by.full_name if self.submitted_by else None,
            "amount": float(self.amount) if self.amount else 0,
            "transfer_date": self.transfer_date.isoformat() if self.transfer_date else None,
            "transfer_hour": self.transfer_hour,
            "transfer_minute": self.transfer_minute,
            "slip_url": self.slip_url,
            "matched_statement_txn_id": str(self.matched_statement_txn_id) if self.matched_statement_txn_id else None,
            "is_matched": self.matched_statement_txn_id is not None,
            "status": self.status.value if self.status else None,
            "rejection_reason": self.rejection_reason,
            "accepted_by": self.accepted_by,
            "accepted_by_name": self.accepted_by_user.full_name if self.accepted_by_user else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_locked(self):
        """Check if payin is locked (accepted or rejected)"""
        return self.status in [PayinStatus.ACCEPTED, PayinStatus.REJECTED]

    def can_be_accepted(self):
        """Check if payin can be accepted"""
        return self.status == PayinStatus.PENDING