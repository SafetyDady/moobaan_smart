from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base
import uuid


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_code = Column(String(50), nullable=False)  # e.g., KBANK, SCB
    account_no_masked = Column(String(50), nullable=False)  # e.g., xxx-x-xxxxx-1234
    account_type = Column(String(20), nullable=False, default="CASHFLOW")  # CASHFLOW, SAVINGS
    currency = Column(String(3), nullable=False, default="THB")
    is_active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "bank_code": self.bank_code,
            "account_no_masked": self.account_no_masked,
            "account_type": self.account_type,
            "currency": self.currency,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
