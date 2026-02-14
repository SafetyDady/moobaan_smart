from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
import enum


class LedgerStatus(enum.Enum):
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class IncomeTransaction(Base):
    __tablename__ = "income_transactions"

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    
    # Phase P1: payin_id is now NULLABLE (Case B: statement without pay-in)
    payin_id = Column(Integer, ForeignKey("payin_reports.id", ondelete="CASCADE"), unique=True, nullable=True)
    
    # Phase P1: bank_transaction_id is the source of truth (UNIQUE — 1 statement → 1 ledger)
    reference_bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("bank_transactions.id", ondelete="RESTRICT"), nullable=True, unique=True)
    
    amount = Column(Numeric(10, 2), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Phase P1: Reverse support (compensating state, no hard delete)
    status = Column(
        SAEnum(LedgerStatus, name='ledger_status_enum', create_constraint=False, native_enum=True),
        nullable=False,
        server_default='POSTED'
    )
    reversed_at = Column(DateTime(timezone=True), nullable=True)
    reversed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reverse_reason = Column(Text, nullable=True)

    # Relationships
    house = relationship("House")
    payin = relationship("PayinReport", back_populates="income_transaction")
    bank_transaction = relationship("BankTransaction", foreign_keys=[reference_bank_transaction_id])
    invoice_payments = relationship("InvoicePayment", back_populates="income_transaction")
    reversed_by_user = relationship("User", foreign_keys=[reversed_by])

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "house_code": self.house.house_code if self.house else None,
            "payin_id": self.payin_id,
            "reference_bank_transaction_id": str(self.reference_bank_transaction_id) if self.reference_bank_transaction_id else None,
            "amount": float(self.amount) if self.amount else 0,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status.value if self.status else "POSTED",
            "reversed_at": self.reversed_at.isoformat() if self.reversed_at else None,
            "reverse_reason": self.reverse_reason,
        }

    def get_total_applied(self):
        """Calculate total amount applied to invoices (only ACTIVE payments)"""
        if not self.invoice_payments:
            return 0
        return sum(float(payment.amount) for payment in self.invoice_payments 
                   if not hasattr(payment, 'status') or payment.status is None or payment.status.value == 'ACTIVE')

    def get_unallocated_amount(self):
        """Calculate amount not yet applied to any invoice"""
        return float(self.amount) - self.get_total_applied()