from datetime import datetime, date, timedelta
from app.models import (
    House, HouseStatus,
    Member, MemberRole,
    Invoice, InvoiceType, InvoiceStatus, InvoiceItem,
    PayInReport, PayInStatus,
    Expense, ExpenseStatus,
    BankStatement, BankStatementRow,
    DashboardSummary
)

# Mock Houses
MOCK_HOUSES = [
    House(
        id=1,
        house_number="A-101",
        address="123 Village Road",
        status=HouseStatus.ACTIVE,
        member_count=3,
        created_at=datetime.now() - timedelta(days=365)
    ),
    House(
        id=2,
        house_number="A-102",
        address="124 Village Road",
        status=HouseStatus.ACTIVE,
        member_count=2,
        created_at=datetime.now() - timedelta(days=350)
    ),
    House(
        id=3,
        house_number="B-201",
        address="201 Village Road",
        status=HouseStatus.ACTIVE,
        member_count=1,
        created_at=datetime.now() - timedelta(days=300)
    ),
    House(
        id=4,
        house_number="B-202",
        address="202 Village Road",
        status=HouseStatus.INACTIVE,
        member_count=0,
        created_at=datetime.now() - timedelta(days=280)
    ),
]

# Mock Members
MOCK_MEMBERS = [
    Member(
        id=1,
        house_id=1,
        house_number="A-101",
        name="สมชาย ใจดี",
        phone="081-234-5678",
        email="somchai@example.com",
        role=MemberRole.OWNER,
        created_at=datetime.now() - timedelta(days=365)
    ),
    Member(
        id=2,
        house_id=1,
        house_number="A-101",
        name="สมหญิง ใจดี",
        phone="082-345-6789",
        email="somying@example.com",
        role=MemberRole.FAMILY,
        created_at=datetime.now() - timedelta(days=365)
    ),
    Member(
        id=3,
        house_id=1,
        house_number="A-101",
        name="น้องชาย ใจดี",
        phone="083-456-7890",
        email=None,
        role=MemberRole.FAMILY,
        created_at=datetime.now() - timedelta(days=300)
    ),
    Member(
        id=4,
        house_id=2,
        house_number="A-102",
        name="วิชัย มั่งมี",
        phone="084-567-8901",
        email="wichai@example.com",
        role=MemberRole.OWNER,
        created_at=datetime.now() - timedelta(days=350)
    ),
    Member(
        id=5,
        house_id=2,
        house_number="A-102",
        name="วิชญา มั่งมี",
        phone="085-678-9012",
        email="wichaya@example.com",
        role=MemberRole.FAMILY,
        created_at=datetime.now() - timedelta(days=350)
    ),
    Member(
        id=6,
        house_id=3,
        house_number="B-201",
        name="ประยุทธ์ สุขสม",
        phone="086-789-0123",
        email="prayut@example.com",
        role=MemberRole.OWNER,
        created_at=datetime.now() - timedelta(days=300)
    ),
]

# Mock Invoices
MOCK_INVOICES = [
    Invoice(
        id=1,
        house_id=1,
        house_number="A-101",
        invoice_type=InvoiceType.AUTO_MONTHLY,
        cycle="2024-01",
        total=3000.0,
        status=InvoiceStatus.PAID,
        due_date=date(2024, 1, 31),
        items=[
            InvoiceItem(id=1, description="ค่าส่วนกลาง", amount=2000.0),
            InvoiceItem(id=2, description="ค่าน้ำ", amount=500.0),
            InvoiceItem(id=3, description="ค่าไฟ", amount=500.0),
        ],
        created_at=datetime(2024, 1, 1)
    ),
    Invoice(
        id=2,
        house_id=1,
        house_number="A-101",
        invoice_type=InvoiceType.AUTO_MONTHLY,
        cycle="2024-02",
        total=3000.0,
        status=InvoiceStatus.PENDING,
        due_date=date(2024, 2, 29),
        items=[
            InvoiceItem(id=4, description="ค่าส่วนกลาง", amount=2000.0),
            InvoiceItem(id=5, description="ค่าน้ำ", amount=500.0),
            InvoiceItem(id=6, description="ค่าไฟ", amount=500.0),
        ],
        created_at=datetime(2024, 2, 1)
    ),
    Invoice(
        id=3,
        house_id=2,
        house_number="A-102",
        invoice_type=InvoiceType.AUTO_MONTHLY,
        cycle="2024-01",
        total=3000.0,
        status=InvoiceStatus.OVERDUE,
        due_date=date(2024, 1, 31),
        items=[
            InvoiceItem(id=7, description="ค่าส่วนกลาง", amount=2000.0),
            InvoiceItem(id=8, description="ค่าน้ำ", amount=500.0),
            InvoiceItem(id=9, description="ค่าไฟ", amount=500.0),
        ],
        created_at=datetime(2024, 1, 1)
    ),
    Invoice(
        id=4,
        house_id=1,
        house_number="A-101",
        invoice_type=InvoiceType.MANUAL,
        cycle=None,
        total=5000.0,
        status=InvoiceStatus.PENDING,
        due_date=date.today() + timedelta(days=30),
        items=[
            InvoiceItem(id=10, description="ค่าซ่อมแซมรั้ว", amount=5000.0),
        ],
        created_at=datetime.now() - timedelta(days=5)
    ),
]

# Mock Pay-in Reports
MOCK_PAYIN_REPORTS = [
    PayInReport(
        id=1,
        house_id=1,
        house_number="A-101",
        amount=3000.0,
        transfer_date="2024-01-15",  # String format
        transfer_hour=14,
        transfer_minute=30,
        slip_image_url="https://example.com/slips/slip1.jpg",
        status=PayInStatus.ACCEPTED,
        reject_reason=None,
        matched_statement_row_id=1,
        created_at=datetime(2024, 1, 15, 14, 35),
        updated_at=datetime(2024, 1, 15, 15, 0)
    ),
    PayInReport(
        id=2,
        house_id=2,
        house_number="A-102",
        amount=3000.0,
        transfer_date="2024-01-20",  # String format
        transfer_hour=10,
        transfer_minute=15,
        slip_image_url="https://example.com/slips/slip2.jpg",
        status=PayInStatus.REJECTED,
        reject_reason="ภาพสลิปไม่ชัดเจน กรุณาอัพโหลดใหม่",
        matched_statement_row_id=None,
        created_at=datetime(2024, 1, 20, 10, 20),
        updated_at=datetime(2024, 1, 20, 11, 0)
    ),
    PayInReport(
        id=3,
        house_id=3,
        house_number="B-201",
        amount=3000.0,
        transfer_date=(date.today() - timedelta(days=1)).isoformat(),  # Convert to string
        transfer_hour=16,
        transfer_minute=45,
        slip_image_url="https://example.com/slips/slip3.jpg",
        status=PayInStatus.PENDING,
        reject_reason=None,
        matched_statement_row_id=None,
        created_at=datetime.now() - timedelta(days=1),
        updated_at=datetime.now() - timedelta(days=1)
    ),
    PayInReport(
        id=4,
        house_id=1,
        house_number="A-101",
        amount=3000.0,
        transfer_date=(date.today() - timedelta(days=2)).isoformat(),  # Convert to string
        transfer_hour=9,
        transfer_minute=0,
        slip_image_url="https://example.com/slips/slip4.jpg",
        status=PayInStatus.ACCEPTED,
        reject_reason=None,
        matched_statement_row_id=3,
        created_at=datetime.now() - timedelta(days=2),
        updated_at=datetime.now() - timedelta(days=1, hours=12)
    ),
]

# Mock Expenses
MOCK_EXPENSES = [
    Expense(
        id=1,
        date=date(2024, 1, 10),
        category="ซ่อมบำรุง",
        amount=15000.0,
        description="ซ่อมแซมประตูทางเข้าหมู่บ้าน",
        receipt_url="https://example.com/receipts/receipt1.pdf",
        status=ExpenseStatus.PAID,
        created_at=datetime(2024, 1, 10),
        updated_at=datetime(2024, 1, 15)
    ),
    Expense(
        id=2,
        date=date(2024, 1, 20),
        category="ค่าสาธารณูปโภค",
        amount=8000.0,
        description="ค่าไฟฟ้าส่วนกลาง",
        receipt_url="https://example.com/receipts/receipt2.pdf",
        status=ExpenseStatus.APPROVED,
        created_at=datetime(2024, 1, 20),
        updated_at=datetime(2024, 1, 22)
    ),
    Expense(
        id=3,
        date=date.today(),
        category="ทำความสะอาด",
        amount=5000.0,
        description="ค่าบริการทำความสะอาดสวนสาธารณะ",
        receipt_url=None,
        status=ExpenseStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now()
    ),
]

# Mock Bank Statements
MOCK_BANK_STATEMENTS = [
    BankStatement(
        id=1,
        filename="statement_2024_01.xlsx",
        upload_date=datetime(2024, 1, 31, 10, 0),
        total_rows=15,
        matched_rows=12
    ),
]

MOCK_BANK_STATEMENT_ROWS = [
    BankStatementRow(
        id=1,
        statement_id=1,
        date=date(2024, 1, 15),
        time="14:30",
        amount=3000.0,
        reference="TRF-001234",
        matched=True,
        matched_payin_id=1
    ),
    BankStatementRow(
        id=2,
        statement_id=1,
        date=date(2024, 1, 18),
        time="11:20",
        amount=2500.0,
        reference="TRF-001235",
        matched=False,
        matched_payin_id=None
    ),
    BankStatementRow(
        id=3,
        statement_id=1,
        date=date.today() - timedelta(days=2),
        time="09:00",
        amount=3000.0,
        reference="TRF-001236",
        matched=True,
        matched_payin_id=4
    ),
]

# Mock Dashboard Summary
MOCK_DASHBOARD_SUMMARY = DashboardSummary(
    current_balance=125000.0,
    total_income=180000.0,
    total_expenses=55000.0,
    active_houses=3,
    pending_payins=1,
    overdue_invoices=1
)
