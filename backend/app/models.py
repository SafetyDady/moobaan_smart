from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# Authentication models
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    house_id: Optional[int] = None


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    phone: Optional[str] = None
    role: str = "resident"


# Existing enums
class UserRole(str, Enum):
    RESIDENT = "resident"
    ACCOUNTING = "accounting"
    SUPER_ADMIN = "super_admin"


class HouseStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MemberRole(str, Enum):
    OWNER = "owner"
    FAMILY = "family"


class PayInStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class InvoiceType(str, Enum):
    AUTO_MONTHLY = "auto_monthly"
    MANUAL = "manual"


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class ExpenseStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PAID = "paid"


# Dashboard Models
class DashboardSummary(BaseModel):
    current_balance: float = 0.0
    total_income: float = 0.0
    total_expenses: float = 0.0
    total_houses: int = 0
    active_houses: int = 0
    total_residents: int = 0
    pending_invoices: int = 0
    total_outstanding: float = 0.0
    pending_payins: int = 0
    overdue_invoices: int = 0
    recent_payments: int = 0
    monthly_revenue: float = 0.0


# House Models
class HouseBase(BaseModel):
    house_number: str
    address: Optional[str] = None
    status: HouseStatus = HouseStatus.ACTIVE


class HouseCreate(HouseBase):
    pass


class House(HouseBase):
    id: int
    member_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# Member Models
class MemberBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: MemberRole = MemberRole.FAMILY


class MemberCreate(MemberBase):
    house_id: int


class Member(MemberBase):
    id: int
    house_id: int
    house_number: str
    created_at: datetime

    class Config:
        from_attributes = True


# Invoice Models
class InvoiceItemBase(BaseModel):
    description: str
    amount: float


class InvoiceItem(InvoiceItemBase):
    id: int


class InvoiceBase(BaseModel):
    house_id: int
    invoice_type: InvoiceType
    cycle: Optional[str] = None  # e.g., "2024-01"
    due_date: date
    items: List[InvoiceItemBase]


class InvoiceCreate(InvoiceBase):
    pass


class Invoice(BaseModel):
    id: int
    house_id: int
    house_number: str
    invoice_type: InvoiceType
    cycle: Optional[str] = None
    total: float
    status: InvoiceStatus
    due_date: date
    items: List[InvoiceItem]
    created_at: datetime

    class Config:
        from_attributes = True


# Pay-in Report Models
class PayInReportBase(BaseModel):
    house_id: int
    amount: float
    transfer_date: str  # Accept date string (YYYY-MM-DD)
    transfer_hour: int  # 0-23
    transfer_minute: int  # 0-59
    slip_image_url: str  # Required - must attach slip


class PayInReportCreate(PayInReportBase):
    pass


class PayInReportUpdate(BaseModel):
    amount: Optional[float] = None
    transfer_date: Optional[str] = None
    transfer_hour: Optional[int] = None
    transfer_minute: Optional[int] = None
    slip_image_url: Optional[str] = None


class PayInReport(PayInReportBase):
    id: int
    house_number: str
    status: PayInStatus
    reject_reason: Optional[str] = None
    matched_statement_row_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RejectPayInRequest(BaseModel):
    reason: str


# Expense Models
class ExpenseBase(BaseModel):
    date: date
    category: str
    amount: float
    description: Optional[str] = None
    receipt_url: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    date: Optional[date] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    receipt_url: Optional[str] = None
    status: Optional[ExpenseStatus] = None


class Expense(ExpenseBase):
    id: int
    status: ExpenseStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Bank Statement Models
class BankStatementRow(BaseModel):
    id: int
    statement_id: int
    date: date
    time: str
    amount: float
    reference: str
    matched: bool
    matched_payin_id: Optional[int] = None


class BankStatement(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    total_rows: int
    matched_rows: int


class BankStatementUploadResponse(BaseModel):
    statement_id: int
    filename: str
    total_rows: int
    message: str


# Month-End Snapshot Models
class MonthEndSnapshot(BaseModel):
    """
    Month-end financial snapshot for a single house.
    All values are computed on-demand from ledger (not persisted).
    """
    house_id: int
    house_code: Optional[str] = None
    owner_name: Optional[str] = None
    year: int
    month: int
    opening_balance: float  # Balance at start of month (before any transactions in target month)
    invoice_total: float    # Sum of invoices issued in target month
    payment_total: float    # Sum of payments received in target month
    credit_total: float     # Sum of credit notes issued in target month
    closing_balance: float  # opening + invoice - payment - credit


class AggregatedSnapshot(BaseModel):
    """
    Aggregated month-end snapshot for all houses.
    Admin-only view of overall financial position.
    """
    year: int
    month: int
    total_houses: int
    opening_balance: float
    invoice_total: float
    payment_total: float
    credit_total: float
    closing_balance: float
    houses: List[MonthEndSnapshot]  # Detail for each house


# Financial Statement Models (Phase 2.4 - Read-Only Presentation)
class StatementRow(BaseModel):
    """
    Single row in financial statement.
    Running balance is display-only (not persisted).
    """
    date: date
    description: str
    debit: Optional[float] = None   # Invoices only
    credit: Optional[float] = None  # Payments + Credit Notes
    balance: float  # Running balance (display-only, not stored)
    transaction_type: str  # "opening", "invoice", "payment", "credit_note"
    transaction_id: Optional[int] = None  # Reference to source transaction


class StatementSummary(BaseModel):
    """
    Footer summary for financial statement.
    All values computed from ledger + snapshot.
    """
    invoice_total: float    # Sum of invoices in period
    payment_total: float    # Sum of payments in period
    credit_total: float     # Sum of credit notes in period
    closing_balance: float  # From snapshot only (NOT calculated here)


class FinancialStatement(BaseModel):
    """
    Complete financial statement for a house over a date range.
    
    IMPORTANT: This is a READ-ONLY presentation combining:
    - Opening balance from Phase 2.3 snapshot
    - Ledger transactions in period
    - Closing balance from Phase 2.3 snapshot
    
    No data is stored - all values derived on-demand.
    """
    house_id: int
    house_code: Optional[str] = None
    owner_name: Optional[str] = None
    start_date: date
    end_date: date
    opening_balance: float  # From snapshot (NOT calculated)
    closing_balance: float  # From snapshot (NOT calculated)
    rows: List[StatementRow]  # Transactions sorted by date ASC
    summary: StatementSummary
