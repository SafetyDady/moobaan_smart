from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date, Text, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class InvoiceStatus(enum.Enum):
    ISSUED = "ISSUED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Invoice(Base):
    __tablename__ = "invoices"
    
    __table_args__ = (
        UniqueConstraint('house_id', 'cycle_year', 'cycle_month', name='unique_house_cycle'),
    )

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    cycle_year = Column(Integer, nullable=False)  # e.g., 2024
    cycle_month = Column(Integer, nullable=False)  # 1-12
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)  # e.g., 600.00
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.ISSUED)
    notes = Column(Text, nullable=True)  # For accounting notes, discount explanations, etc.
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    house = relationship("House")
    creator = relationship("User")
    payments = relationship("InvoicePayment", back_populates="invoice")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "house_code": self.house.house_code if self.house else None,
            "owner_name": self.house.owner_name if self.house else None,
            "cycle_year": self.cycle_year,
            "cycle_month": self.cycle_month,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "status": self.status.value if self.status else None,
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_total_paid(self):
        """Calculate total amount paid for this invoice"""
        if not self.payments:
            return 0
        return sum(float(payment.amount) for payment in self.payments)

    def get_outstanding_amount(self):
        """Calculate remaining amount to be paid"""
        return float(self.total_amount) - self.get_total_paid()

    def update_status(self):
        """Update invoice status based on payments"""
        total_paid = self.get_total_paid()
        total_amount = float(self.total_amount)
        
        if total_paid <= 0:
            self.status = InvoiceStatus.ISSUED
        elif total_paid >= total_amount:
            self.status = InvoiceStatus.PAID
        else:
            self.status = InvoiceStatus.PARTIALLY_PAID