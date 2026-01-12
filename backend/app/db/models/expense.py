from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from sqlalchemy.sql import func
from app.db.session import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=False)  # maintenance, utilities, administration, etc.
    expense_date = Column(DateTime(timezone=True), nullable=False)
    receipt_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary matching frontend expectations"""
        return {
            "id": self.id,
            "description": self.description,
            "amount": float(self.amount) if self.amount else 0,
            "category": self.category,
            "expense_date": self.expense_date.isoformat() if self.expense_date else None,
            "receipt_url": self.receipt_url,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }