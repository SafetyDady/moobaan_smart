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
    SUBMITTED = "submitted"
    REJECTED = "rejected"
    MATCHED = "matched"
    ACCEPTED = "accepted"


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
    current_balance: float
    total_income: float
    total_expenses: float
    active_houses: int
    pending_payins: int
    overdue_invoices: int


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
    transfer_date: date
    transfer_hour: int
    transfer_minute: int
    slip_image_url: Optional[str] = None


class PayInReportCreate(PayInReportBase):
    pass


class PayInReportUpdate(BaseModel):
    amount: Optional[float] = None
    transfer_date: Optional[date] = None
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
