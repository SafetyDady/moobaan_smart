"""
Expense ↔ Bank Allocation model

Many-to-many junction between expenses and bank_transactions.
Allows partial matching: one expense can be covered by multiple bank debits,
and one bank debit can cover multiple expenses (split payment).

Business Rules:
- SUM(matched_amount) for an expense must not exceed expense.amount
- SUM(matched_amount) for a bank txn must not exceed bank_transaction.debit
- Only DEBIT transactions (cash-out) can be allocated to expenses
- matched_amount must be > 0
"""
from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid


class ExpenseBankAllocation(Base):
    __tablename__ = "expense_bank_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("bank_transactions.id", ondelete="CASCADE"), nullable=False)
    matched_amount = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('expense_id', 'bank_transaction_id', name='uq_expense_bank_allocation'),
        CheckConstraint('matched_amount > 0', name='ck_allocation_amount_positive'),
        Index('ix_allocation_expense_id', 'expense_id'),
        Index('ix_allocation_bank_txn_id', 'bank_transaction_id'),
    )

    # Relationships
    expense = relationship("Expense", backref="bank_allocations")
    bank_transaction = relationship("BankTransaction", backref="expense_allocations")

    def to_dict(self):
        return {
            "id": str(self.id),
            "expense_id": self.expense_id,
            "bank_transaction_id": str(self.bank_transaction_id),
            "matched_amount": float(self.matched_amount) if self.matched_amount else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
