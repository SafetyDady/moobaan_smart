"""
Generate a mobile-friendly PNG image report of unidentified bank credits.
Designed for admin to download and share in LINE group chat.
"""

import io
import os
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw, ImageFont

# Bangkok timezone (UTC+7)
BANGKOK_TZ = timezone(timedelta(hours=7), name="Asia/Bangkok")

# ── Layout constants (pixels) ──────────────────────────────────────────
IMG_WIDTH = 800
PADDING = 30
HEADER_HEIGHT = 140
SUMMARY_HEIGHT = 60
TABLE_HEADER_HEIGHT = 44
ROW_HEIGHT = 68
FOOTER_HEIGHT = 90

# ── Colors ─────────────────────────────────────────────────────────────
BG_WHITE = "#FFFFFF"
HEADER_BG = "#1E293B"
HEADER_TEXT = "#FFFFFF"
SUMMARY_BG = "#E0F2FE"
SUMMARY_TEXT = "#0C4A6E"
TABLE_HEADER_BG = "#334155"
TABLE_HEADER_TEXT = "#FFFFFF"
ROW_EVEN = "#FFFFFF"
ROW_ODD = "#F8FAFC"
GRID_COLOR = "#E2E8F0"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"
AMOUNT_GREEN = "#059669"
FOOTER_TEXT = "#6B7280"
DIVIDER_COLOR = "#CBD5E1"

# ── Thai month names ───────────────────────────────────────────────────
THAI_MONTHS = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
]


def _load_fonts() -> dict:
    """Load Thai fonts with fallback paths."""
    font_paths = [
        # Bundled font (Docker/Railway)
        os.path.join(os.path.dirname(__file__), "../../assets/fonts/Sarabun-Regular.ttf"),
        # Windows system fonts
        "C:/Windows/Fonts/leelawad.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        # Linux system fonts
        "/usr/share/fonts/truetype/thai/Sarabun-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
    ]
    bold_paths = [
        os.path.join(os.path.dirname(__file__), "../../assets/fonts/Sarabun-Bold.ttf"),
        "C:/Windows/Fonts/leelawdb.ttf",
        "C:/Windows/Fonts/tahomabd.ttf",
        "/usr/share/fonts/truetype/thai/Sarabun-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
    ]

    def _find_font(paths, size):
        for fp in paths:
            fp = os.path.normpath(fp)
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    return {
        "title": _find_font(bold_paths, 26),
        "subtitle": _find_font(font_paths, 18),
        "date_info": _find_font(font_paths, 15),
        "summary": _find_font(bold_paths, 20),
        "table_header": _find_font(bold_paths, 16),
        "row_text": _find_font(font_paths, 16),
        "row_bold": _find_font(bold_paths, 16),
        "row_small": _find_font(font_paths, 14),
        "footer": _find_font(font_paths, 14),
        "footer_small": _find_font(font_paths, 12),
    }


def _fmt_baht(val: float) -> str:
    """Format amount as Thai Baht."""
    return f"฿{val:,.2f}"


def _fmt_date_thai(iso_str: str) -> tuple[str, str]:
    """
    Parse ISO datetime, convert to Bangkok time.
    Returns (date_str, time_str).
    """
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
        date_str = f"{day} {month} {year_be}"
        time_str = f"{dt_bkk.hour:02d}:{dt_bkk.minute:02d}"
        return (date_str, time_str)
    except Exception:
        return ("-", "-")


def _truncate_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    """Truncate text with ellipsis if it exceeds max_width."""
    if not text:
        return "-"
    bbox = draw.textbbox((0, 0), text, font=font)
    if (bbox[2] - bbox[0]) <= max_width:
        return text
    # Truncate character by character
    for i in range(len(text), 0, -1):
        truncated = text[:i] + "..."
        bbox = draw.textbbox((0, 0), truncated, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return truncated
    return "..."


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy, fill, radius=8):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)


def generate_unidentified_receipts_image(
    transactions: list[dict],
    village_name: str = "หมู่บ้าน",
) -> io.BytesIO:
    """
    Generate a mobile-friendly PNG image report of unidentified bank credits.

    Args:
        transactions: List of dicts with keys:
            - effective_at: ISO datetime string
            - amount: float
            - description: str (sender/channel info from bank)
            - bank_name: str (optional)
        village_name: Village name for header

    Returns:
        BytesIO buffer containing PNG image data
    """
    fonts = _load_fonts()
    txn_count = len(transactions)
    total_amount = sum(t.get("amount", 0) for t in transactions)

    # Calculate image height
    table_height = TABLE_HEADER_HEIGHT + (ROW_HEIGHT * max(txn_count, 1))
    img_height = PADDING + HEADER_HEIGHT + SUMMARY_HEIGHT + table_height + FOOTER_HEIGHT + PADDING

    # Create image
    img = Image.new("RGB", (IMG_WIDTH, img_height), BG_WHITE)
    draw = ImageDraw.Draw(img)

    y = 0

    # ── Header section (dark background) ───────────────────────────────
    draw.rectangle([0, 0, IMG_WIDTH, HEADER_HEIGHT], fill=HEADER_BG)

    # Village name
    y_text = PADDING
    draw.text((PADDING, y_text), village_name, fill=HEADER_TEXT, font=fonts["title"])

    # Report title
    y_text += 36
    draw.text((PADDING, y_text), "รายการเงินเข้าที่ยังไม่ระบุตัวตน", fill="#94A3B8", font=fonts["subtitle"])

    # Report date
    y_text += 28
    now_bkk = datetime.now(BANGKOK_TZ)
    day = now_bkk.day
    month = THAI_MONTHS[now_bkk.month]
    year_be = (now_bkk.year + 543) % 100
    date_str = f"ออกรายงานเมื่อ {day} {month} {year_be}  เวลา {now_bkk.hour:02d}:{now_bkk.minute:02d} น."
    draw.text((PADDING, y_text), date_str, fill="#64748B", font=fonts["date_info"])

    y = HEADER_HEIGHT

    # ── Summary bar ────────────────────────────────────────────────────
    _draw_rounded_rect(draw, (PADDING, y + 10, IMG_WIDTH - PADDING, y + SUMMARY_HEIGHT - 2), fill=SUMMARY_BG, radius=10)

    summary_y = y + 20
    draw.text(
        (PADDING + 20, summary_y),
        f"จำนวน: {txn_count} รายการ",
        fill=SUMMARY_TEXT, font=fonts["summary"],
    )
    # Right-aligned total
    total_text = f"รวม: {_fmt_baht(total_amount)}"
    bbox = draw.textbbox((0, 0), total_text, font=fonts["summary"])
    total_w = bbox[2] - bbox[0]
    draw.text(
        (IMG_WIDTH - PADDING - 20 - total_w, summary_y),
        total_text,
        fill=SUMMARY_TEXT, font=fonts["summary"],
    )

    y += SUMMARY_HEIGHT + 8

    # ── Table ──────────────────────────────────────────────────────────
    # Column layout: # | วันที่/เวลา + ผู้โอน | จำนวนเงิน
    col_num_x = PADDING
    col_num_w = 50
    col_detail_x = col_num_x + col_num_w
    col_detail_w = 510
    col_amount_x = col_detail_x + col_detail_w
    col_amount_w = IMG_WIDTH - PADDING - col_amount_x

    # Table header
    draw.rectangle([PADDING, y, IMG_WIDTH - PADDING, y + TABLE_HEADER_HEIGHT], fill=TABLE_HEADER_BG)
    header_y = y + 12
    draw.text((col_num_x + 14, header_y), "#", fill=TABLE_HEADER_TEXT, font=fonts["table_header"])
    draw.text((col_detail_x + 12, header_y), "วันที่ / ผู้โอน", fill=TABLE_HEADER_TEXT, font=fonts["table_header"])
    draw.text((col_amount_x + 12, header_y), "จำนวนเงิน", fill=TABLE_HEADER_TEXT, font=fonts["table_header"])

    y += TABLE_HEADER_HEIGHT

    # Table rows
    if txn_count == 0:
        # Empty state
        draw.rectangle([PADDING, y, IMG_WIDTH - PADDING, y + ROW_HEIGHT], fill=ROW_EVEN)
        draw.text(
            (IMG_WIDTH // 2 - 80, y + 22),
            "ไม่มีรายการที่ยังไม่ระบุ",
            fill=TEXT_SECONDARY, font=fonts["row_text"],
        )
        y += ROW_HEIGHT
    else:
        for idx, txn in enumerate(transactions):
            row_bg = ROW_EVEN if idx % 2 == 0 else ROW_ODD
            draw.rectangle([PADDING, y, IMG_WIDTH - PADDING, y + ROW_HEIGHT], fill=row_bg)

            # Row number
            draw.text(
                (col_num_x + 18, y + 22),
                str(idx + 1),
                fill=TEXT_SECONDARY, font=fonts["row_text"],
            )

            # Date + Time
            date_str, time_str = _fmt_date_thai(txn.get("effective_at"))
            draw.text(
                (col_detail_x + 12, y + 8),
                f"{date_str}  {time_str} น.",
                fill=TEXT_PRIMARY, font=fonts["row_bold"],
            )

            # Description (sender name) - truncated
            desc = txn.get("description", "-") or "-"
            desc_truncated = _truncate_text(draw, desc, fonts["row_small"], col_detail_w - 24)
            draw.text(
                (col_detail_x + 12, y + 32),
                desc_truncated,
                fill=TEXT_SECONDARY, font=fonts["row_small"],
            )

            # Amount (right-aligned within column)
            amount_text = _fmt_baht(txn.get("amount", 0))
            bbox = draw.textbbox((0, 0), amount_text, font=fonts["row_bold"])
            amount_w = bbox[2] - bbox[0]
            draw.text(
                (IMG_WIDTH - PADDING - 16 - amount_w, y + 22),
                amount_text,
                fill=AMOUNT_GREEN, font=fonts["row_bold"],
            )

            # Grid line
            draw.line(
                [(PADDING, y + ROW_HEIGHT), (IMG_WIDTH - PADDING, y + ROW_HEIGHT)],
                fill=GRID_COLOR, width=1,
            )

            y += ROW_HEIGHT

    # Table border
    table_top = HEADER_HEIGHT + SUMMARY_HEIGHT + 8
    draw.rectangle(
        [PADDING, table_top, IMG_WIDTH - PADDING, y],
        outline=GRID_COLOR, width=1,
    )

    # ── Footer ─────────────────────────────────────────────────────────
    y += 16
    draw.line([(PADDING, y), (IMG_WIDTH - PADDING, y)], fill=DIVIDER_COLOR, width=1)
    y += 12

    footer_text = "กรุณารายงานการชำระเงินผ่านแอปพลิเคชัน หรือติดต่อฝ่ายการเงิน"
    bbox = draw.textbbox((0, 0), footer_text, font=fonts["footer"])
    fw = bbox[2] - bbox[0]
    draw.text(((IMG_WIDTH - fw) // 2, y), footer_text, fill=FOOTER_TEXT, font=fonts["footer"])

    y += 28
    gen_text = f"Generated: {now_bkk.strftime('%d/%m/%Y %H:%M')}"
    bbox = draw.textbbox((0, 0), gen_text, font=fonts["footer_small"])
    gw = bbox[2] - bbox[0]
    draw.text(((IMG_WIDTH - gw) // 2, y), gen_text, fill="#94A3B8", font=fonts["footer_small"])

    # ── Save to buffer ─────────────────────────────────────────────────
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer
