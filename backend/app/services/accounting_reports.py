"""Read-only cash statements from currently valid, dated financial records.

This is a restated view, not a frozen/locked period snapshot. Receipt allocation
does not affect cash. Bounds are Bangkok calendar days, amounts stay Decimal
until the response boundary, and query errors must reach the caller.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.timezone import BANGKOK_TZ
from app.db.models import House, Invoice, IncomeTransaction, CreditNote, PayinReport, PayinStatus
from app.db.models.income_transaction import LedgerStatus

ZERO = Decimal('0')


def month_dates(year: int, month: int):
    if not 2000 <= year <= 3000 or not 1 <= month <= 12:
        raise ValueError('Invalid year or month')
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def local_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError('Financial timestamp must include a timezone')
    return value.astimezone(BANGKOK_TZ)


@dataclass
class CashWindow:
    house: House
    opening: Decimal
    invoice_total: Decimal
    payment_total: Decimal
    credit_total: Decimal
    closing: Decimal
    events: list


def cash_window(db: Session, house_id: int, start: date, end: date) -> CashWindow:
    if start > end or end == date.max:
        raise ValueError('Invalid statement date range')
    house = db.get(House, house_id)
    if not house:
        raise ValueError(f'House {house_id} not found')
    start_at = datetime.combine(start, datetime.min.time(), tzinfo=BANGKOK_TZ)
    end_day = end + timedelta(days=1)
    end_at = datetime.combine(end_day, datetime.min.time(), tzinfo=BANGKOK_TZ)
    events = []
    for inv in db.query(Invoice).filter(Invoice.house_id == house_id, Invoice.issue_date < end_day).all():
        cycle = 'Manual' if inv.is_manual else f'{inv.cycle_year}-{inv.cycle_month:02d}'
        events.append(dict(at=datetime.combine(inv.issue_date, datetime.min.time(), tzinfo=BANGKOK_TZ),
            kind='invoice', id=inv.id, amount=Decimal(inv.total_amount), order=0,
            description=f'Invoice {cycle}', description_th=f'ใบแจ้งหนี้ {cycle}',
            reference=f'INV-{inv.id}', source_table='invoices'))
    for receipt in db.query(IncomeTransaction).filter(
        IncomeTransaction.house_id == house_id, IncomeTransaction.status == LedgerStatus.POSTED,
        IncomeTransaction.received_at < end_at,
    ).all():
        ref = f'PayIn #{receipt.payin_id}' if receipt.payin_id else f'Ledger #{receipt.id}'
        events.append(dict(at=local_time(receipt.received_at), kind='payment', id=receipt.id,
            amount=Decimal(receipt.amount), order=1, description=f'Payment ({ref})',
            description_th=f'รับเงิน ({ref})', reference=f'PAY-{receipt.id}', source_table='income_transactions'))
    for credit in db.query(CreditNote).join(Invoice, Invoice.id == CreditNote.invoice_id).filter(
        Invoice.house_id == house_id, CreditNote.status == 'applied', CreditNote.created_at < end_at,
    ).all():
        events.append(dict(at=local_time(credit.created_at), kind='credit_note', id=credit.id,
            amount=Decimal(credit.credit_amount), order=2, description=f'Credit Note: {credit.reason[:50]}',
            description_th=credit.reason, reference=f'CR-{credit.id}', source_table='credit_notes'))
    events.sort(key=lambda e: (e['at'], e['order'], e['id']))
    opening = ZERO
    period = []
    totals = dict(invoice=ZERO, payment=ZERO, credit_note=ZERO)
    for event in events:
        signed = event['amount'] if event['kind'] == 'invoice' else -event['amount']
        if event['at'] < start_at:
            opening += signed
        else:
            period.append(event)
            totals[event['kind']] += event['amount']
    running = opening
    for event in period:
        running += event['amount'] if event['kind'] == 'invoice' else -event['amount']
        event['balance'] = running
    closing = opening + totals['invoice'] - totals['payment'] - totals['credit_note']
    if closing != running:
        raise ValueError('Statement balance does not reconcile')
    return CashWindow(house, opening, totals['invoice'], totals['payment'], totals['credit_note'], closing, period)


def month_snapshot(db: Session, house_id: int, year: int, month: int):
    start, end = month_dates(year, month)
    w = cash_window(db, house_id, start, end)
    return dict(house_id=house_id, house_code=w.house.house_code, owner_name=w.house.owner_name,
        year=year, month=month, period=f'{year:04d}-{month:02d}', period_end=end.isoformat(),
        opening_balance=float(w.opening), invoice_total=float(w.invoice_total),
        payment_total=float(w.payment_total), credit_total=float(w.credit_total), closing_balance=float(w.closing))


def range_statement(db: Session, house_id: int, start: date, end: date):
    w = cash_window(db, house_id, start, end)
    rows = [dict(date=start, description='Opening Balance', debit=None, credit=None,
        balance=float(w.opening), transaction_type='opening', transaction_id=None)]
    for event in w.events:
        rows.append(dict(date=event['at'].date(), description=event['description'],
            debit=float(event['amount']) if event['kind'] == 'invoice' else None,
            credit=float(event['amount']) if event['kind'] != 'invoice' else None,
            balance=float(event['balance']), transaction_type=event['kind'], transaction_id=event['id']))
    return dict(house_id=house_id, house_code=w.house.house_code, owner_name=w.house.owner_name,
        start_date=start, end_date=end, opening_balance=float(w.opening), closing_balance=float(w.closing),
        rows=rows, pending_payins=pending_context(db, house_id), summary=dict(invoice_total=float(w.invoice_total), payment_total=float(w.payment_total),
            credit_total=float(w.credit_total), closing_balance=float(w.closing)))


def monthly_statement(db: Session, house_id: int, year: int, month: int, thai_month: str, english_month: str):
    start, end = month_dates(year, month)
    w = cash_window(db, house_id, start, end)
    values = dict(opening_balance=float(w.opening), invoice_total=float(w.invoice_total),
        payment_total=float(w.payment_total), credit_total=float(w.credit_total), closing_balance=float(w.closing))
    snapshot = dict(house_id=house_id, house_code=w.house.house_code, owner_name=w.house.owner_name,
        year=year, month=month, period=f'{year:04d}-{month:02d}', period_end=end.isoformat(), **values)
    names = {'invoice': ('ใบแจ้งหนี้', 'Invoice'), 'payment': ('รับเงิน', 'Payment'), 'credit_note': ('ลดหนี้', 'Credit Note')}
    transactions = [dict(date=e['at'].date(), type=e['kind'], type_th=names[e['kind']][0],
        type_en=names[e['kind']][1], reference=e['reference'], description=e['description'],
        description_th=e['description_th'], amount=float(e['amount']), is_debit=e['kind'] == 'invoice',
        source_id=e['id'], source_table=e['source_table'], running_balance=float(e['balance'])) for e in w.events]
    return dict(header=dict(house_code=w.house.house_code, owner_name=w.house.owner_name,
        house_status=w.house.house_status.value, period=f'{year:04d}-{month:02d}',
        period_th=f'{thai_month} {year + 543}', period_en=f'{english_month} {year}',
        statement_date=datetime.now(BANGKOK_TZ).date().isoformat(), closing_balance=float(w.closing)),
        summary=dict(
            opening_balance=dict(th='ยอดยกมา', en='Opening Balance', amount=float(w.opening)),
            invoices=dict(th='ใบแจ้งหนี้เดือนนี้', en='Invoices This Month', amount=float(w.invoice_total)),
            payments=dict(th='รับเงินยืนยัน', en='Confirmed Receipts', amount=-float(w.payment_total)),
            credit_notes=dict(th='ลดหนี้/ปรับปรุงหนี้', en='Credit Notes / Debt Adjustment', amount=-float(w.credit_total)),
            closing_balance=dict(th='ยอดคงเหลือปลายเดือน', en='Closing Balance', amount=float(w.closing))),
        transactions=transactions, snapshot=snapshot, pending_payins=pending_context(db, house_id))


def dated_outstanding(invoice, end: date) -> Decimal:
    """Restated end-of-day settlement debt, not a frozen historical ledger.

    Invoice date, receipt date and credit creation date are separate events.
    Later allocation of an earlier receipt restates the earlier period.
    """
    if invoice.issue_date > end:
        return ZERO
    end_at = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=BANGKOK_TZ)
    paid = sum((Decimal(p.amount) for p in invoice.payments
        if p.status.value == 'ACTIVE' and p.income_transaction
        and p.income_transaction.status == LedgerStatus.POSTED
        and local_time(p.income_transaction.received_at) < end_at), ZERO)
    credited = sum((Decimal(c.credit_amount) for c in invoice.credit_notes
        if c.status == 'applied' and local_time(c.created_at) < end_at), ZERO)
    return max(ZERO, Decimal(invoice.total_amount) - paid - credited)


def pending_context(db: Session, house_id: int):
    """Current submitted evidence, independent of a historical statement period."""
    count, amount = db.query(func.count(PayinReport.id),
        func.coalesce(func.sum(PayinReport.amount), 0)).filter(
        PayinReport.house_id == house_id,
        PayinReport.status.in_([PayinStatus.SUBMITTED, PayinStatus.PENDING]),
    ).one()
    return dict(scope='current', count=count, amount=float(amount),
        excluded_from_confirmed_receipts=True)
