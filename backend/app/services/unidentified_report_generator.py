"""
Generate a mobile-friendly HTML report of unidentified bank credits.
Designed for admin to view in browser and screenshot to share in LINE group.
"""

from datetime import datetime, timedelta, timezone
from html import escape

BANGKOK_TZ = timezone(timedelta(hours=7), name="Asia/Bangkok")

THAI_MONTHS = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
]


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
    Extract sender/details from raw_row or description.
    KBANK CSV stores sender info in the Details column (typically last non-empty cell).
    """
    raw_row = txn.get("raw_row")
    if raw_row and isinstance(raw_row, list):
        # Try common details column indices (KBANK: index 12)
        for idx in [12, 11, 13]:
            if idx < len(raw_row) and raw_row[idx] and str(raw_row[idx]).strip():
                return str(raw_row[idx]).strip()
        # Fallback: last non-empty cell in the row
        for cell in reversed(raw_row):
            if cell and str(cell).strip() and str(cell).strip() not in ('-', ''):
                val = str(cell).strip()
                # Skip numeric-only values (amounts/balances)
                cleaned = val.replace(',', '').replace('.', '').replace('-', '')
                if not cleaned.isdigit():
                    return val
    return txn.get("description") or "-"


def generate_unidentified_receipts_html(
    transactions: list[dict],
    village_name: str = "หมู่บ้าน",
) -> str:
    """
    Generate a self-contained HTML report of unidentified bank credits.
    Mobile-friendly, designed for screenshot sharing in LINE group.
    """
    now_bkk = datetime.now(BANGKOK_TZ)
    day = now_bkk.day
    month = THAI_MONTHS[now_bkk.month]
    year_be = (now_bkk.year + 543) % 100
    report_date = f"{day} {month} {year_be} เวลา {now_bkk.hour:02d}:{now_bkk.minute:02d} น."

    txn_count = len(transactions)
    total_amount = sum(t.get("amount", 0) for t in transactions)

    # Build transaction rows
    rows_html = ""
    for idx, txn in enumerate(transactions):
        date_str, time_str = _fmt_date_thai(txn.get("effective_at"))
        amount = txn.get("amount", 0)
        sender = escape(_extract_sender(txn))
        channel = escape(txn.get("channel") or "")
        bank = escape(txn.get("bank_name") or "")

        rows_html += f"""
        <div class="row {'odd' if idx % 2 else ''}">
          <div class="row-num">{idx + 1}</div>
          <div class="row-detail">
            <div class="row-date">{escape(date_str)} &nbsp; {escape(time_str)} น.</div>
            <div class="row-sender">{sender}</div>
            <div class="row-channel">{escape(channel)}{(' · ' + bank) if bank else ''}</div>
          </div>
          <div class="row-amount">{_fmt_baht(amount)}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>รายการเงินเข้าที่ยังไม่ระบุ - {escape(village_name)}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Sarabun', 'Prompt', 'Kanit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f1f5f9;
    color: #1e293b;
    min-height: 100vh;
  }}
  .container {{
    max-width: 480px;
    margin: 0 auto;
    background: #fff;
    min-height: 100vh;
    box-shadow: 0 0 20px rgba(0,0,0,0.08);
  }}
  .header {{
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    color: #fff;
    padding: 24px 20px;
  }}
  .header h1 {{
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .header .subtitle {{
    font-size: 15px;
    color: #94a3b8;
    margin-bottom: 8px;
  }}
  .header .date {{
    font-size: 13px;
    color: #64748b;
  }}
  .summary {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #e0f2fe;
    margin: 12px 12px 0;
    padding: 14px 18px;
    border-radius: 12px;
  }}
  .summary-label {{
    font-size: 15px;
    color: #0c4a6e;
    font-weight: 600;
  }}
  .summary-total {{
    font-size: 18px;
    color: #0c4a6e;
    font-weight: 700;
  }}
  .table-header {{
    display: flex;
    align-items: center;
    background: #334155;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 12px;
    margin: 12px 12px 0;
    border-radius: 8px 8px 0 0;
  }}
  .table-header .th-num {{ width: 36px; text-align: center; }}
  .table-header .th-detail {{ flex: 1; padding-left: 8px; }}
  .table-header .th-amount {{ width: 110px; text-align: right; }}
  .rows {{
    margin: 0 12px;
    border-left: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
  }}
  .row {{
    display: flex;
    align-items: flex-start;
    padding: 12px;
    border-bottom: 1px solid #e2e8f0;
  }}
  .row.odd {{
    background: #f8fafc;
  }}
  .row-num {{
    width: 36px;
    text-align: center;
    font-size: 14px;
    color: #94a3b8;
    padding-top: 2px;
    font-weight: 600;
  }}
  .row-detail {{
    flex: 1;
    padding-left: 8px;
    min-width: 0;
  }}
  .row-date {{
    font-size: 14px;
    font-weight: 600;
    color: #1e293b;
  }}
  .row-sender {{
    font-size: 14px;
    color: #475569;
    margin-top: 2px;
    word-break: break-word;
  }}
  .row-channel {{
    font-size: 12px;
    color: #94a3b8;
    margin-top: 2px;
  }}
  .row-amount {{
    width: 110px;
    text-align: right;
    font-size: 15px;
    font-weight: 700;
    color: #059669;
    padding-top: 2px;
    white-space: nowrap;
  }}
  .rows-end {{
    margin: 0 12px;
    height: 8px;
    border-left: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    border-radius: 0 0 8px 8px;
  }}
  .footer {{
    text-align: center;
    padding: 20px;
    color: #6b7280;
    font-size: 14px;
    line-height: 1.6;
  }}
  .footer .cta {{
    background: #fef3c7;
    color: #92400e;
    padding: 12px 16px;
    border-radius: 10px;
    margin: 0 12px 12px;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.5;
  }}
  .footer .gen {{
    font-size: 12px;
    color: #94a3b8;
  }}
  .empty {{
    text-align: center;
    padding: 40px 20px;
    color: #94a3b8;
    font-size: 15px;
  }}
  @media print {{
    body {{ background: #fff; }}
    .container {{ box-shadow: none; max-width: 100%; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{escape(village_name)}</h1>
    <div class="subtitle">รายการเงินเข้าที่ยังไม่ระบุตัวตน</div>
    <div class="date">ออกรายงานเมื่อ {escape(report_date)}</div>
  </div>

  <div class="summary">
    <div class="summary-label">{txn_count} รายการ</div>
    <div class="summary-total">รวม {_fmt_baht(total_amount)}</div>
  </div>

  {"" if txn_count == 0 else f'''
  <div class="table-header">
    <div class="th-num">#</div>
    <div class="th-detail">วันที่ / ผู้โอน</div>
    <div class="th-amount">จำนวนเงิน</div>
  </div>
  <div class="rows">
    {rows_html}
  </div>
  <div class="rows-end"></div>
  '''}

  {"<div class='empty'>ไม่มีรายการที่ยังไม่ระบุ</div>" if txn_count == 0 else ""}

  <div class="footer">
    <div class="cta">
      หากท่านเป็นเจ้าของรายการเหล่านี้<br>
      กรุณารายงานการชำระเงินผ่านแอปพลิเคชัน<br>
      หรือติดต่อฝ่ายการเงินของหมู่บ้าน
    </div>
    <div class="gen">Generated: {now_bkk.strftime('%d/%m/%Y %H:%M')}</div>
  </div>
</div>
</body>
</html>"""
    return html
