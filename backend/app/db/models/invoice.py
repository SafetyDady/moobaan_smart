from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date, Text, Enum, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum
from decimal import Decimal


class InvoiceStatus(enum.Enum):
    ISSUED = "ISSUED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Invoice(Base):
    __tablename__ = "invoices"
    
    # Note: unique constraint for (house_id, cycle_year, cycle_month) is now a partial index
    # that only applies when is_manual = false (see migration d1_manual_invoice)

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    cycle_year = Column(Integer, nullable=False)  # e.g., 2024 (0 for manual invoices)
    cycle_month = Column(Integer, nullable=False)  # 1-12 (0 for manual invoices)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)  # e.g., 600.00
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.ISSUED)
    notes = Column(Text, nullable=True)  # For accounting notes, discount explanations, etc.
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Manual invoice fields (Phase D.1)
    is_manual = Column(Boolean, nullable=False, default=False)
    manual_reason = Column(Text, nullable=True)  # Reason/description for manual invoice
    
    # Phase F.2: Link to Chart of Accounts (REVENUE type only)
    revenue_account_id = Column(Integer, ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    house = relationship("House")
    creator = relationship("User")
    payments = relationship("InvoicePayment", back_populates="invoice")
    credit_notes = relationship("CreditNote", back_populates="invoice")
    revenue_account = relationship("ChartOfAccount")  # Phase F.2

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
            "is_manual": self.is_manual,
            "manual_reason": self.manual_reason,
            "revenue_account_id": self.revenue_account_id,
            "revenue_account_code": self.revenue_account.account_code if self.revenue_account else None,
            "revenue_account_name": self.revenue_account.account_name if self.revenue_account else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_total_credited(self):
        return float(self.get_total_credited_decimal())

    def get_total_credited_decimal(self):
        return sum((Decimal(str(cn.credit_amount))
                    for cn in (self.credit_notes or []) if cn.status == 'applied'), Decimal('0'))

    def get_total_paid_decimal(self):
        return sum((Decimal(str(payment.amount)) for payment in (self.payments or [])
                    if not hasattr(payment, 'status') or payment.status is None
                    or payment.status.value == 'ACTIVE'), Decimal('0'))

    def get_net_amount_decimal(self):
        return max(Decimal('0'), Decimal(str(self.total_amount)) - self.get_total_credited_decimal())

    def get_remaining_balance_decimal(self):
        """Single source of truth for credit caps and settlement balances."""
        return max(Decimal('0'), self.get_net_amount_decimal() - self.get_total_paid_decimal())

    def get_net_amount(self):
        """Calculate net payable amount after credits (Phase D.2)
        
        Formula: net_amount = total_amount - total_credited
        This NEVER modifies the original invoice amount.
        """
        return float(self.get_net_amount_decimal())

    def get_remaining_balance(self):
        """Calculate remaining balance after credits AND payments (Phase D.2)
        
        Formula: remaining = net_amount - total_paid
        """
        return float(self.get_remaining_balance_decimal())

    def is_fully_credited(self):
        """Check if invoice is fully credited (cancelled by credit note)"""
        total = Decimal(str(self.total_amount))
        return total > 0 and self.get_total_credited_decimal() >= total

    def get_total_paid(self):
        """Calculate total amount paid for this invoice (only ACTIVE payments)"""
        return float(self.get_total_paid_decimal())

    def get_outstanding_amount(self):
        """Calculate remaining amount to be paid (considering credits)"""
        return self.get_remaining_balance()

    def get_last_payment_at(self):
        """Return the actual receipt time of the most recent ACTIVE payment (None if unpaid).

        Uses the linked income_transaction.received_at (the real money-received time,
        sourced from the bank statement / pay-in) rather than InvoicePayment.applied_at
        (which is only when an accountant linked the payment to the invoice). For an
        invoice paid in several instalments this returns the latest instalment's
        received_at — hence "last payment". Full per-payment history stays in the
        invoice detail view.
        """
        times = [
            payment.income_transaction.received_at
            for payment in (self.payments or [])
            if (not hasattr(payment, 'status') or payment.status is None or payment.status.value == 'ACTIVE')
            and payment.income_transaction is not None
            and payment.income_transaction.received_at is not None
        ]
        if not times:
            return None
        return max(times)

    def get_settlement_status(self):
        """Public status derived from current amounts, without mutating stored state.

        Partial credits alone do not constitute payment. CREDITED is an API
        value; PostgreSQL continues to store CANCELLED for fully credited bills.
        """
        if self.is_fully_credited():
            return 'CREDITED'
        if self.get_remaining_balance_decimal() <= 0:
            return 'PAID'
        if self.get_total_paid_decimal() > 0:
            return 'PARTIALLY_PAID'
        return 'ISSUED'

    def update_status(self):
        """Persist the canonical status only during an explicit settlement write."""
        status = self.get_settlement_status()
        self.status = InvoiceStatus.CANCELLED if status == 'CREDITED' else InvoiceStatus(status)
