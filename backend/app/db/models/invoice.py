from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="draft")  # draft, sent, paid, overdue, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    house = relationship("House")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    invoice = relationship("Invoice")