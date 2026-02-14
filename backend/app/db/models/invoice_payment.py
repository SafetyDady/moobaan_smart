from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class PaymentStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    REVERSED = "REVERSED"


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    income_transaction_id = Column(Integer, ForeignKey("income_transactions.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Phase P1: Reverse support
    status = Column(
        SAEnum(PaymentStatus, name='payment_status_enum', create_constraint=False, native_enum=True),
        nullable=False,
        server_default='ACTIVE'
    )

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    income_transaction = relationship("IncomeTransaction", back_populates="invoice_payments")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "income_transaction_id": self.income_transaction_id,
            "amount": float(self.amount) if self.amount else 0,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "status": self.status.value if self.status else "ACTIVE",
        }