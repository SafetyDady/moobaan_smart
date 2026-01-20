from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Date, ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class ExpenseStatus(enum.Enum):
    """Expense status enum for Phase F.1"""
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class ExpenseCategory(enum.Enum):
    """Predefined expense categories"""
    MAINTENANCE = "MAINTENANCE"
    SECURITY = "SECURITY"
    CLEANING = "CLEANING"
    UTILITIES = "UTILITIES"
    ADMIN = "ADMIN"
    OTHER = "OTHER"


class Expense(Base):
    """
    Expense model for Phase F.1: Expense Core (Cash Out)
    Updated in Phase F.2: Added account_id FK to Chart of Accounts
    
    Represents money paid or payable (cash-out) from the village fund.
    
    Rules:
    - amount > 0
    - paid_date cannot be earlier than expense_date
    - Cannot mark-paid if status is CANCELLED
    - Cannot cancel if already PAID
    - account_id must reference an EXPENSE type account (Phase F.2)
    """
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint('amount > 0', name='expense_amount_positive'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Optional: expense may relate to a specific house
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Phase F.2: Link to Chart of Accounts (EXPENSE type only)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    
    # Core expense fields
    category = Column(String(100), nullable=False, index=True)  # MAINTENANCE, SECURITY, CLEANING, UTILITIES, ADMIN, OTHER
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String(255), nullable=False)
    
    # Dates
    expense_date = Column(Date, nullable=False, index=True)  # When expense occurred / invoice date
    paid_date = Column(Date, nullable=True)  # When actually paid
    
    # Status
    status = Column(Enum(ExpenseStatus), nullable=False, default=ExpenseStatus.PENDING, index=True)
    
    # Additional info
    vendor_name = Column(String(255), nullable=True)
    payment_method = Column(String(50), nullable=True)  # CASH/TRANSFER/CHECK/OTHER
    receipt_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    house = relationship("House")
    created_by = relationship("User")
    account = relationship("ChartOfAccount")  # Phase F.2

    def to_dict(self):
        """Convert model to dictionary matching frontend expectations"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "house_code": self.house.house_code if self.house else None,
            "account_id": self.account_id,
            "account_code": self.account.account_code if self.account else None,
            "account_name": self.account.account_name if self.account else None,
            "category": self.category,
            "amount": float(self.amount) if self.amount else 0,
            "description": self.description,
            "expense_date": self.expense_date.isoformat() if self.expense_date else None,
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "status": self.status.value if self.status else None,
            "vendor_name": self.vendor_name,
            "payment_method": self.payment_method,
            "receipt_url": self.receipt_url,
            "notes": self.notes,
            "created_by_user_id": self.created_by_user_id,
            "created_by_name": self.created_by.full_name if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
