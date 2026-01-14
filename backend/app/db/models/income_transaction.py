from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class IncomeTransaction(Base):
    __tablename__ = "income_transactions"

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    payin_id = Column(Integer, ForeignKey("payin_reports.id", ondelete="CASCADE"), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    house = relationship("House")
    payin = relationship("PayinReport")
    invoice_payments = relationship("InvoicePayment", back_populates="income_transaction")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "house_code": self.house.house_code if self.house else None,
            "payin_id": self.payin_id,
            "amount": float(self.amount) if self.amount else 0,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_total_applied(self):
        """Calculate total amount applied to invoices"""
        if not self.invoice_payments:
            return 0
        return sum(float(payment.amount) for payment in self.invoice_payments)

    def get_unallocated_amount(self):
        """Calculate amount not yet applied to any invoice"""
        return float(self.amount) - self.get_total_applied()