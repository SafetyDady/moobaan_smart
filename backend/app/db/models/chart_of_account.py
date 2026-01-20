"""
Phase F.2: Chart of Accounts (COA Lite) Model

IMPORTANT: This is a STRUCTURAL layer only
- NO General Ledger
- NO Debit/Credit posting
- NO Balance tracking
- NO Auto journal entries

Purpose:
- Classification for reporting
- Export to Excel/accountants
- Management accounting structure
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class AccountType(enum.Enum):
    """Account type classification"""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class ChartOfAccount(Base):
    """
    Chart of Accounts model for Phase F.2: COA Lite
    
    This is a classification structure only - NOT a GL account.
    No balance tracking, no posting, no debit/credit.
    
    Account Code Convention:
    - 1xxx: Asset
    - 2xxx: Liability
    - 4xxx: Revenue
    - 5xxx: Expense
    """
    __tablename__ = "chart_of_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_code = Column(String(20), nullable=False, unique=True, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False, index=True)
    active = Column(Boolean, nullable=False, default=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "account_type": self.account_type.value if self.account_type else None,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
