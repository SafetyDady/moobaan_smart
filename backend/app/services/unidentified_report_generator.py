"""
Generate a mobile-friendly PDF report of unidentified bank credits.
Designed for admin to download and share in LINE group chat.
Uses ReportLab with Thai font support (Sarabun from Google Fonts).
"""

import io
import os
from datetime import datetime, timedelta, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BANGKOK_TZ = timezone(timedelta(hours=7), name="Asia/Bangkok")

THAI_MONTHS = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
]

# ── Colors ─────────────────────────────────────────────────────────────
HEADER_BG = colors.HexColor("#1e293b")
SUMMARY_BG = colors.HexColor("#e0f2fe")
SUMMARY_TEXT = colors.HexColor("#0c4a6e")
TABLE_HEADER_BG = colors.HexColor("#334155")
ROW_ODD = colors.HexColor("#f8fafc")
GRID_COLOR = colors.HexColor("#e2e8f0")
AMOUNT_GREEN = colors.HexColor("#059669")
TEXT_SECONDARY = colors.HexColor("#64748b")
CTA_BG = colors.HexColor("#fef3c7")
CTA_TEXT = colors.HexColor("#92400e")


def _setup_fonts() -> str:
    """Register Thai font and return font name."""
    font_paths = [
        os.path.join(os.path.dirname(__file__), "../../assets/fonts/Sarabun-Regular.ttf"),
        "/usr/share/fonts/truetype/thai/Sarabun-Regular.ttf",
    ]
    bold_paths = [
        os.path.join(os.path.dirname(__file__), "../../assets/fonts/Sarabun-Bold.ttf"),
        "/usr/share/fonts/truetype/thai/Sarabun-Bold.ttf",
    ]

    registered = False
    for fp in font_paths:
        fp = os.path.normpath(fp)
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("Sarabun", fp))
                registered = True
                break
            except Exception:
                continue

    for fp in bold_paths:
        fp = os.path.normpath(fp)
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("Sarabun-Bold", fp))
                break
            except Exception:
                continue

    return "Sarabun" if registered else "Helvetica"


def _fmt_baht(val: float) -> str:
    return f"฿{val:,.2f}"


def _fmt_date_thai(iso_str: str) -> tuple[str, str]:
    """Returns (date_str, time_str) in Bangkok timezone."""
    if not iso_str:
        return ("-", "-")
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_bkk = dt.astimezone(BANGKOK_TZ)
        day = dt_bkk.day
        month = THAI_MONTHS[dt_bkk.month]
        year_be = (dt_bkk.year + 543) % 100
        return (f"{day} {month} {year_be}", f"{dt_bkk.hour:02d}:{dt_bkk.minute:02d}")
    except Exception:
        return ("-", "-")


def _extract_sender(txn: dict) -> str:
    """
    Extract sender/details from raw_row.
    KBANK CSV stores sender info in the Details column (typically index 12).
    """
    raw_row = txn.get("raw_row")
    if raw_row and isinstance(raw_row, list):
        for idx in [12, 11, 13]:
            if idx < len(raw_row) and raw_row[idx] and str(raw_row[idx]).strip():
                return str(raw_row[idx]).strip()
        # Fallback: last non-empty non-numeric cell
        for cell in reversed(raw_row):
            if cell and str(cell).strip():
                val = str(cell).strip()
                cleaned = val.replace(",", "").replace(".", "").replace("-", "")
                if not cleaned.isdigit():
                    return val
    return txn.get("description") or "-"


def generate_unidentified_receipts_pdf(
    transactions: list[dict],
    village_name: str = "หมู่บ้าน",
) -> io.BytesIO:
    """
    Generate a PDF report of unidentified bank credits.

    Args:
        transactions: List of dicts with keys:
            - effective_at, amount, description, channel, bank_name, raw_row
        village_name: Village name for header

    Returns:
        BytesIO buffer containing PDF data
    """
    font_name = _setup_fonts()
    bold_name = "Sarabun-Bold" if font_name == "Sarabun" else "Helvetica-Bold"

    now_bkk = datetime.now(BANGKOK_TZ)
    day = now_bkk.day
    month = THAI_MONTHS[now_bkk.month]
    year_be = (now_bkk.year + 543) % 100
    report_date = f"ออกรายงานเมื่อ {day} {month} {year_be} เวลา {now_bkk.hour:02d}:{now_bkk.minute:02d} น."

    txn_count = len(transactions)
    total_amount = sum(t.get("amount", 0) for t in transactions)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    elements = []

    # ── Styles ─────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontName=bold_name, fontSize=20, textColor=colors.white,
        spaceAfter=2 * mm,
    )
    style_subtitle = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontName=font_name, fontSize=13, textColor=colors.HexColor("#94a3b8"),
        spaceAfter=2 * mm,
    )
    style_date = ParagraphStyle(
        "ReportDate", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=TEXT_SECONDARY,
    )
    style_summary = ParagraphStyle(
        "SummaryText", parent=styles["Normal"],
        fontName=bold_name, fontSize=13, textColor=SUMMARY_TEXT,
    )
    style_cell = ParagraphStyle(
        "CellText", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=colors.HexColor("#1e293b"),
        leading=14,
    )
    style_cell_small = ParagraphStyle(
        "CellSmall", parent=styles["Normal"],
        fontName=font_name, fontSize=9, textColor=TEXT_SECONDARY,
        leading=12,
    )
    style_cell_amount = ParagraphStyle(
        "CellAmount", parent=styles["Normal"],
        fontName=bold_name, fontSize=11, textColor=AMOUNT_GREEN,
        alignment=2,  # RIGHT
    )
    style_footer = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontName=font_name, fontSize=10, textColor=CTA_TEXT,
        alignment=1,  # CENTER
        leading=16,
    )
    style_gen = ParagraphStyle(
        "Generated", parent=styles["Normal"],
        fontName=font_name, fontSize=8, textColor=TEXT_SECONDARY,
        alignment=1,
    )

    # ── Header (dark background table) ─────────────────────────────────
    header_data = [[
        Paragraph(f"{village_name}", style_title),
    ], [
        Paragraph("รายการเงินเข้าที่ยังไม่ระบุตัวตน", style_subtitle),
    ], [
        Paragraph(report_date, style_date),
    ]]
    page_width = A4[0] - 30 * mm
    header_table = Table(header_data, colWidths=[page_width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HEADER_BG),
        ("TOPPADDING", (0, 0), (0, 0), 12),
        ("BOTTOMPADDING", (0, -1), (0, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 2), (0, 2), 0),
        ("ROUNDEDCORNERS", [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 3 * mm))

    # ── Summary bar ────────────────────────────────────────────────────
    summary_data = [[
        Paragraph(f"{txn_count} รายการ", style_summary),
        Paragraph(f"รวม {_fmt_baht(total_amount)}", ParagraphStyle(
            "SummaryRight", parent=style_summary, alignment=2,
        )),
    ]]
    summary_table = Table(summary_data, colWidths=[page_width * 0.5, page_width * 0.5])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SUMMARY_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Transaction table ──────────────────────────────────────────────
    # Columns: # | วันที่/เวลา + ผู้โอน | จำนวนเงิน
    col_widths = [32, page_width - 32 - 85, 85]

    # Table header
    th_style = ParagraphStyle(
        "TH", parent=styles["Normal"],
        fontName=bold_name, fontSize=10, textColor=colors.white,
    )
    th_style_right = ParagraphStyle(
        "THRight", parent=th_style, alignment=2,
    )
    table_data = [[
        Paragraph("#", th_style),
        Paragraph("วันที่ / ผู้โอน", th_style),
        Paragraph("จำนวนเงิน", th_style_right),
    ]]

    # Table rows
    if txn_count == 0:
        table_data.append([
            "",
            Paragraph("ไม่มีรายการที่ยังไม่ระบุ", style_cell_small),
            "",
        ])
    else:
        for idx, txn in enumerate(transactions):
            date_str, time_str = _fmt_date_thai(txn.get("effective_at"))
            sender = _extract_sender(txn)
            channel = txn.get("channel") or ""
            bank = txn.get("bank_name") or ""
            channel_line = f"{channel}{' · ' + bank if bank else ''}"

            detail_text = (
                f"<b>{date_str} &nbsp; {time_str} น.</b><br/>"
                f"{sender}<br/>"
                f"<font size='8' color='#94a3b8'>{channel_line}</font>"
            )

            table_data.append([
                Paragraph(str(idx + 1), ParagraphStyle(
                    "RowNum", parent=style_cell, textColor=TEXT_SECONDARY, alignment=1,
                )),
                Paragraph(detail_text, style_cell),
                Paragraph(_fmt_baht(txn.get("amount", 0)), style_cell_amount),
            ])

    txn_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Table styling
    style_cmds = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Body
        ("TOPPADDING", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("LINEBELOW", (0, 0), (-1, 0), 1, TABLE_HEADER_BG),
    ]

    # Alternating row backgrounds
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ODD))

    txn_table.setStyle(TableStyle(style_cmds))
    elements.append(txn_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Footer CTA ─────────────────────────────────────────────────────
    cta_data = [[
        Paragraph(
            "หากท่านเป็นเจ้าของรายการเหล่านี้<br/>"
            "กรุณารายงานการชำระเงินผ่านแอปพลิเคชัน",
            style_footer,
        )
    ]]
    cta_table = Table(cta_data, colWidths=[page_width])
    cta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CTA_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    elements.append(cta_table)
    elements.append(Spacer(1, 4 * mm))

    # Generated timestamp
    elements.append(Paragraph(
        f"Generated: {now_bkk.strftime('%d/%m/%Y %H:%M')}",
        style_gen,
    ))

    # ── Build PDF ──────────────────────────────────────────────────────
    doc.build(elements)
    buffer.seek(0)
    return buffer
