"""
Phase 5.2: Report Export API (PDF/Excel)

Purpose:
- Export admin data tables as PDF or Excel files
- Supports: invoices, payins, houses, members, expenses
- READ ONLY — no data mutation

Endpoints:
- GET /api/reports/export/{report_type}?format=pdf|xlsx
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, desc, extract
from typing import Optional
from datetime import datetime
import io
import logging

from app.db.session import get_db
from app.core.deps import require_admin_or_accounting
from app.core.timezone import BANGKOK_TZ
from app.db.models import (
    User, Invoice, InvoiceStatus, PayinReport, PayinStatus,
    House, HouseStatus, Expense, ExpenseStatus, InvoicePayment
)
from app.db.models.house_member import HouseMember

# Canonical settlement status (Invoice.get_settlement_status) → Thai label,
# so the export reads the same as the invoice table on screen.
SETTLEMENT_STATUS_TH = {
    "ISSUED": "รอดำเนินการ",
    "PARTIALLY_PAID": "ชำระบางส่วน",
    "PAID": "ชำระแล้ว",
    "CREDITED": "เครดิตแล้ว",
}

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports/export", tags=["Report Export"])


# ─── Helper: Format Thai Baht ──────────────────────────────────────────

def fmt_baht(val):
    """Format number as Thai Baht string"""
    if val is None:
        return "฿0"
    return f"฿{val:,.2f}"


def _to_bangkok(dt):
    """Timestamps are stored in UTC; business dates are Asia/Bangkok.

    Plain ``date`` objects have no tzinfo and are already calendar dates,
    so they pass through untouched.
    """
    if getattr(dt, "tzinfo", None) is not None:
        return dt.astimezone(BANGKOK_TZ)
    return dt


def fmt_date(dt):
    """Format datetime to Thai-friendly string (Asia/Bangkok)"""
    if not dt:
        return "-"
    if isinstance(dt, str):
        return dt
    return _to_bangkok(dt).strftime("%d/%m/%Y")


def fmt_datetime(dt):
    """Format datetime with time (Asia/Bangkok)"""
    if not dt:
        return "-"
    if isinstance(dt, str):
        return dt
    return _to_bangkok(dt).strftime("%d/%m/%Y %H:%M")


# ─── Data Fetchers ──────────────────────────────────────────────────────

def fetch_invoices(
    db: Session,
    period: Optional[str] = None,
    status: Optional[str] = None,
    house_id: Optional[int] = None,
    is_manual: Optional[bool] = None,
):
    """Fetch invoice data for export.

    Mirrors the invoice table on screen: same money figures, the same canonical
    settlement status, and the same filters the user is looking at. Money cells
    stay numeric so the spreadsheet can total them.
    """
    query = db.query(Invoice).options(
        selectinload(Invoice.payments).selectinload(InvoicePayment.income_transaction),
        selectinload(Invoice.credit_notes),
        selectinload(Invoice.house),
    )
    if period:
        # period format: "YYYY-MM" → filter by cycle_year and cycle_month
        try:
            year, month = period.split("-")
            query = query.filter(
                Invoice.cycle_year == int(year),
                Invoice.cycle_month == int(month),
            )
        except (ValueError, AttributeError):
            pass  # Invalid period format, skip filter

    if house_id:
        query = query.filter(Invoice.house_id == house_id)
    if is_manual is not None:
        query = query.filter(Invoice.is_manual == is_manual)

    query = query.order_by(desc(Invoice.created_at))
    invoices = query.all()

    # Settlement status is computed, not stored, so filter it in Python —
    # the same rule the list API applies.
    status_filter = None
    if status:
        status_filter = {"PENDING": "ISSUED", "CANCELLED": "CREDITED"}.get(
            status.upper(), status.upper()
        )

    headers = [
        "เลขที่", "บ้าน", "งวด", "ยอดรวม", "ชำระแล้ว", "เครดิต/ลดหนี้",
        "ค้างชำระ", "สถานะ", "วันที่ออกบิล", "วันครบกำหนด", "วันที่ชำระล่าสุด",
    ]
    rows = []
    for inv in invoices:
        settlement = inv.get_settlement_status()
        if status_filter and settlement != status_filter:
            continue
        house_code = inv.house.house_code if inv.house else "-"
        if inv.is_manual:
            inv_period = "พิเศษ"
        elif inv.cycle_year and inv.cycle_month:
            inv_period = f"{inv.cycle_year}-{inv.cycle_month:02d}"
        else:
            inv_period = "-"
        rows.append([
            str(inv.id),
            house_code,
            inv_period,
            float(inv.total_amount),
            inv.get_total_paid(),
            inv.get_total_credited(),
            inv.get_remaining_balance(),
            SETTLEMENT_STATUS_TH.get(settlement, settlement),
            fmt_date(inv.issue_date),
            fmt_date(inv.due_date),
            fmt_datetime(inv.get_last_payment_at()),
        ])
    return headers, rows, f"invoices_{period or 'all'}"


def fetch_payins(db: Session, status_filter: Optional[str] = None):
    """Fetch payin data for export"""
    query = db.query(PayinReport)
    if status_filter:
        try:
            status_enum = PayinStatus(status_filter)
            query = query.filter(PayinReport.status == status_enum)
        except ValueError:
            pass
    query = query.order_by(desc(PayinReport.created_at))
    payins = query.all()

    headers = ["เลขที่", "บ้าน", "จำนวนเงิน", "วันที่โอน", "สถานะ", "วันที่แจ้ง"]
    rows = []
    for p in payins:
        house_code = p.house.house_code if p.house else "-"
        rows.append([
            str(p.id),
            house_code,
            fmt_baht(p.amount),
            fmt_date(p.transfer_date),
            p.status.value if p.status else "-",
            fmt_datetime(p.created_at),
        ])
    return headers, rows, f"payins_{status_filter or 'all'}"


def fetch_houses(db: Session):
    """Fetch house data for export"""
    houses = db.query(House).order_by(House.house_code).all()

    headers = ["รหัสบ้าน", "ที่อยู่", "สถานะ", "ค่าส่วนกลาง/เดือน"]
    rows = []
    for h in houses:
        rows.append([
            h.house_code or "-",
            h.address or "-",
            h.status.value if h.status else "-",
            fmt_baht(h.monthly_fee) if hasattr(h, 'monthly_fee') and h.monthly_fee else "-",
        ])
    return headers, rows, "houses"


def fetch_members(db: Session):
    """Fetch member data for export"""
    members = db.query(HouseMember).order_by(HouseMember.id).all()

    headers = ["ชื่อ-นามสกุล", "บ้าน", "โทรศัพท์", "อีเมล", "บทบาท"]
    rows = []
    for m in members:
        house_code = m.house.house_code if m.house else "-"
        rows.append([
            m.full_name or "-",
            house_code,
            m.phone or "-",
            m.email or "-",
            m.role or "-",
        ])
    return headers, rows, "members"


def fetch_expenses(db: Session, period: Optional[str] = None):
    """Fetch expense data for export"""
    query = db.query(Expense)
    if period:
        # period format: "YYYY-MM" — filter by expense_date year/month
        try:
            year, month = period.split("-")
            query = query.filter(
                extract('year', Expense.expense_date) == int(year),
                extract('month', Expense.expense_date) == int(month),
            )
        except (ValueError, AttributeError):
            pass  # Invalid period format, skip filter
    query = query.order_by(desc(Expense.created_at))
    expenses = query.all()

    headers = ["เลขที่", "รายการ", "หมวดหมู่", "จำนวนเงิน", "สถานะ", "วันที่"]
    rows = []
    for e in expenses:
        rows.append([
            str(e.id),
            e.description or "-",
            e.category or "-",
            fmt_baht(e.amount),
            e.status.value if e.status else "-",
            fmt_date(e.expense_date if e.expense_date else e.created_at),
        ])
    return headers, rows, f"expenses_{period or 'all'}"


def drop_columns(headers: list, rows: list, drop: Optional[list], money_columns: Optional[list]):
    """Remove columns by index and re-map money column indices to the new layout.

    Used to give the PDF a narrower set than the spreadsheet.
    """
    drop_set = set(drop or [])
    if not drop_set:
        return headers, rows, money_columns
    keep = [i for i in range(len(headers)) if i not in drop_set]
    new_headers = [headers[i] for i in keep]
    new_rows = [[row[i] for i in keep] for row in rows]
    new_money = [keep.index(i) for i in (money_columns or []) if i in keep]
    return new_headers, new_rows, new_money


# ─── PDF Generator ──────────────────────────────────────────────────────

def generate_pdf(title: str, headers: list, rows: list, money_columns: Optional[list] = None) -> io.BytesIO:
    """Generate PDF report using reportlab.

    Money cells arrive as numbers (so Excel can total them); the PDF renders
    them as Baht text.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Try to register Thai font
    thai_font_registered = False
    font_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "Sarabun-Regular.ttf"),
        "/usr/share/fonts/truetype/thai/Sarabun-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('ThaiFont', fp))
                thai_font_registered = True
                break
            except Exception:
                continue

    font_name = 'ThaiFont' if thai_font_registered else 'Helvetica'

    # Title
    title_style = styles['Title']
    if thai_font_registered:
        title_style.fontName = font_name
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 5*mm))

    # Subtitle with date
    subtitle_style = styles['Normal']
    if thai_font_registered:
        subtitle_style.fontName = font_name
    now_str = datetime.now(BANGKOK_TZ).strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Generated: {now_str} | Total: {len(rows)} records", subtitle_style))
    elements.append(Spacer(1, 5*mm))

    # Table data
    money_cols = set(money_columns or [])
    display_rows = [
        [fmt_baht(value) if idx in money_cols else ("-" if value is None else str(value))
         for idx, value in enumerate(row)]
        for row in rows
    ]
    table_data = [headers] + display_rows

    # Calculate column widths
    available_width = landscape(A4)[0] - 30*mm
    col_count = len(headers)
    col_width = available_width / col_count

    table = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Body
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        # Alternating rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # Set Thai font for all cells if available
    if thai_font_registered:
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
        ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ─── Excel Generator ────────────────────────────────────────────────────

def generate_excel(title: str, headers: list, rows: list, money_columns: Optional[list] = None) -> io.BytesIO:
    """Generate Excel report using openpyxl.

    Money columns are written as real numbers with a currency format so the
    spreadsheet can sum and filter them.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]  # Excel sheet name max 31 chars

    # Header style
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0'),
    )

    # Title row
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = Font(bold=True, size=14)
    title_cell.alignment = Alignment(horizontal="center")

    # Date row
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
    date_cell = ws.cell(row=2, column=1, value=f"Generated: {datetime.now(BANGKOK_TZ).strftime('%d/%m/%Y %H:%M')} | Total: {len(rows)} records")
    date_cell.font = Font(size=10, color="666666")
    date_cell.alignment = Alignment(horizontal="center")

    # Headers (row 4)
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # Data rows
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    money_cols = set(money_columns or [])
    for row_idx, row_data in enumerate(rows, 5):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            if (col_idx - 1) in money_cols:
                cell.number_format = '#,##0.00'
                cell.alignment = Alignment(vertical="center", horizontal="right")
            else:
                cell.alignment = Alignment(vertical="center")
            if (row_idx - 5) % 2 == 1:
                cell.fill = alt_fill

    # Auto-width columns
    for col_idx in range(1, len(headers) + 1):
        max_length = len(str(headers[col_idx - 1]))
        for row in rows:
            if col_idx - 1 < len(row):
                max_length = max(max_length, len(str(row[col_idx - 1])))
        ws.column_dimensions[ws.cell(row=4, column=col_idx).column_letter].width = min(max_length + 4, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ─── Export Endpoint ────────────────────────────────────────────────────

REPORT_TYPES = {
    # money_columns: written as numbers in Excel, rendered as Baht in PDF.
    # pdf_drop_columns: trimmed from the PDF only — 11 columns do not fit A4,
    # so the PDF keeps the on-screen set and Excel keeps the full detail.
    "invoices": {
        "title": "รายงานใบแจ้งหนี้",
        "fetcher": fetch_invoices,
        "money_columns": [3, 4, 5, 6],
        "pdf_drop_columns": [0, 5, 8],  # เลขที่, เครดิต/ลดหนี้, วันที่ออกบิล
    },
    "payins": {"title": "รายงานการชำระเงิน", "fetcher": fetch_payins},
    "houses": {"title": "รายงานบ้านทั้งหมด", "fetcher": fetch_houses},
    "members": {"title": "รายงานสมาชิก", "fetcher": fetch_members},
    "expenses": {"title": "รายงานค่าใช้จ่าย", "fetcher": fetch_expenses},
}


@router.get("/{report_type}")
async def export_report(
    report_type: str,
    format: str = Query("xlsx", pattern="^(pdf|xlsx)$", description="Export format: pdf or xlsx"),
    period: Optional[str] = Query(None, description="Filter by period (YYYY-MM)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    house_id: Optional[int] = Query(None, description="Filter by house (invoices)"),
    is_manual: Optional[bool] = Query(None, description="Manual vs auto-monthly invoices"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting),
):
    """
    Export report data as PDF or Excel file.
    
    Supported report_type: invoices, payins, houses, members, expenses
    """
    if report_type not in REPORT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Supported: {', '.join(REPORT_TYPES.keys())}"
        )

    config = REPORT_TYPES[report_type]
    title = config["title"]

    # Fetch data based on report type
    try:
        if report_type == "invoices":
            headers, rows, filename = config["fetcher"](
                db, period=period, status=status, house_id=house_id, is_manual=is_manual,
            )
        elif report_type == "payins":
            headers, rows, filename = config["fetcher"](db, status_filter=status)
        elif report_type == "expenses":
            headers, rows, filename = config["fetcher"](db, period=period)
        else:
            headers, rows, filename = config["fetcher"](db)
    except Exception as e:
        logger.error(f"Export data fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report data")

    # Generate file
    money_columns = config.get("money_columns")
    try:
        if format == "pdf":
            headers, rows, money_columns = drop_columns(
                headers, rows, config.get("pdf_drop_columns"), money_columns,
            )
            buffer = generate_pdf(title, headers, rows, money_columns=money_columns)
            media_type = "application/pdf"
            ext = "pdf"
        else:
            buffer = generate_excel(title, headers, rows, money_columns=money_columns)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
    except Exception as e:
        logger.error(f"Export generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report file")

    timestamp = datetime.now(BANGKOK_TZ).strftime("%Y%m%d_%H%M%S")
    download_filename = f"{filename}_{timestamp}.{ext}"

    logger.info(f"📊 Report exported: {download_filename} by user {current_user.id}")

    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"'
        }
    )
