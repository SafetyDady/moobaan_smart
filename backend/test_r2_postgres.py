"""R2 regressions on an isolated local PG schema, never the restored evidence DB."""
import asyncio
import uuid
import unittest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text
import test_credit_settlement_postgres as fixtures
from app.api import accounting
from app.api.invoices import get_allocatable_ledgers
from app.api.reports import get_invoice_aging_report, get_cashflow_vs_ar_report
from app.api.dashboard import get_village_summary
from app.core import auth
from app.core.deps import get_db
from app.db.models import (Invoice, InvoiceStatus, IncomeTransaction, InvoicePayment,
    PaymentStatus, CreditNote, BankTransaction, PostingStatus, PayinReport, PayinStatus,
    User, House, HouseMember)
from app.db.models.income_transaction import LedgerStatus
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus
from app.services.accounting import AccountingService as Service
from app.services.accounting_reports import pending_context


class R2Tests(unittest.TestCase):
    setUpClass = classmethod(fixtures.SettlementPostgresTests.setUpClass.__func__)
    cleanup_schema = classmethod(fixtures.SettlementPostgresTests.cleanup_schema.__func__)
    setUp = fixtures.SettlementPostgresTests.setUp
    bank_fixture = fixtures.SettlementPostgresTests.bank_fixture
    payment = fixtures.SettlementPostgresTests.payment
    credit = fixtures.SettlementPostgresTests.credit
    balance = fixtures.SettlementPostgresTests.balance
    race = fixtures.SettlementPostgresTests.race

    def case_b(self):
        self.bank_fixture()
        with self.Session() as db:
            ledger = db.get(IncomeTransaction, self.ledger_id)
            bank = db.get(BankTransaction, uuid.UUID(self.bank_id))
            bank.matched_payin_id = None
            bank.posting_status = PostingStatus.POSTED
            bank.batch.status = 'CONFIRMED'
            bank.credit = ledger.amount
            bank.effective_at = ledger.received_at
            ledger.payin_id = None
            ledger.reference_bank_transaction_id = bank.id
            db.commit()

    def test_statement_only_picker_apply_and_source_unchanged(self):
        self.case_b()
        with self.Session() as db:
            ledger = db.get(IncomeTransaction, self.ledger_id)
            before = ledger.to_dict()
            bank_before = ledger.bank_transaction.to_dict()
            listed = asyncio.run(get_allocatable_ledgers(house_id=ledger.house_id, db=db))
            self.assertEqual(listed['ledgers'][0]['id'], self.ledger_id)
            self.payment(db, '600')
            self.assertEqual(self.balance()[:3], (600, 0, 0))
            self.assertEqual(ledger.to_dict(), before)
            self.assertEqual(ledger.bank_transaction.to_dict(), bank_before)
            self.assertEqual(asyncio.run(get_allocatable_ledgers(house_id=ledger.house_id, db=db))['ledgers'][0]['remaining'], 400)

    def test_unproven_or_mismatched_statement_rejected_in_picker_and_writer(self):
        self.case_b()
        with self.Session() as db:
            for change in ('missing', 'reversed', 'bank_reversed', 'amount', 'time', 'batch', 'matched'):
                with self.subTest(change=change):
                    ledger = db.get(IncomeTransaction, self.ledger_id)
                    bank = ledger.bank_transaction
                    if change == 'missing': ledger.reference_bank_transaction_id = None
                    elif change == 'reversed': ledger.status = LedgerStatus.REVERSED
                    elif change == 'bank_reversed': bank.posting_status = PostingStatus.REVERSED
                    elif change == 'amount': bank.credit = Decimal('999')
                    elif change == 'time': bank.effective_at += timedelta(seconds=1)
                    elif change == 'batch': bank.batch.status = 'PARSED'
                    elif change == 'matched': bank.matched_payin_id = self.payin_id
                    db.flush(); db.expire_all()
                    self.assertEqual(asyncio.run(get_allocatable_ledgers(house_id=ledger.house_id, db=db))['count'], 0)
                    with self.assertRaises(HTTPException): self.payment(db, '100')
                    db.rollback()
            self.assertEqual(db.query(InvoicePayment).filter_by(invoice_id=self.inv_id).count(), 0)

    def test_case_b_caps_cross_house_and_pending_payin(self):
        self.case_b()
        with self.Session() as db:
            for change in ('cross_house', 'invoice_cap', 'ledger_cap', 'pending'):
                with self.subTest(change=change):
                    ledger = db.get(IncomeTransaction, self.ledger_id)
                    if change == 'cross_house':
                        other = House(house_code=uuid.uuid4().hex[:20], owner_name='R2 other'); db.add(other); db.flush()
                        db.get(Invoice, self.inv_id).house_id = other.id
                    if change == 'ledger_cap': db.get(Invoice, self.inv_id).total_amount = Decimal('2000')
                    if change == 'pending':
                        ledger.payin_id = self.payin_id
                        db.get(PayinReport, self.payin_id).status = PayinStatus.PENDING
                    db.flush(); db.expire_all()
                    amount = '1100' if change == 'ledger_cap' else ('601' if change == 'invoice_cap' else '100')
                    with self.assertRaises(HTTPException): self.payment(db, amount)
                    db.rollback()

    def test_race_case_b_credit_then_payment(self):
        self.case_b()
        self.assertEqual(self.race(lambda db: self.credit(db, '400'),
            lambda db: self.payment(db, '400')), (0, 400, 200))

    def test_race_case_b_two_allocations(self):
        self.case_b()
        self.assertEqual(self.race(lambda db: self.payment(db, '400'),
            lambda db: self.payment(db, '400')), (400, 0, 200))

    def test_race_case_b_reversal_prevents_waiting_application(self):
        from app.api.bank_reconciliation import reverse_posted_transaction, ReverseRequest
        self.case_b()
        def reverse(db):
            asyncio.run(reverse_posted_transaction(self.bank_id, ReverseRequest(reason='R2 race'),
                current_user=db.get(User, self.user_id), db=db))
        self.assertEqual(self.race(reverse, lambda db: self.payment(db, '400')), (0, 0, 600))

    def test_aging_credit_stale_status_and_bangkok_last_microsecond(self):
        with self.Session() as db:
            inv = db.get(Invoice, self.inv_id)
            inv.issue_date = date(2026, 5, 1); inv.due_date = date(2026, 5, 1)
            inv.status = InvoiceStatus.PAID  # Deliberately stale: must still be considered.
            ledger = db.get(IncomeTransaction, self.ledger_id)
            ledger.received_at = datetime(2026, 5, 31, 16, 59, 59, 999999, tzinfo=timezone.utc)
            db.add_all([
                InvoicePayment(invoice_id=inv.id, income_transaction_id=ledger.id, amount=Decimal('100'), status=PaymentStatus.ACTIVE),
                InvoicePayment(invoice_id=inv.id, income_transaction_id=ledger.id, amount=Decimal('50'), status=PaymentStatus.REVERSED),
                CreditNote(invoice_id=inv.id, credit_amount=Decimal('200'), reason='R2', status='applied', created_at=ledger.received_at),
            ])
            db.commit()
            def aging():
                return next(r for r in Service.generate_aging_report(db, 2026, 5) if r['house_id'] == inv.house_id)
            for tz in ('UTC', 'Asia/Bangkok', 'America/New_York'):
                db.execute(text(f"SET LOCAL TIME ZONE '{tz}'")); db.expire_all()
                self.assertEqual(aging()['total_outstanding'], 300)
            ledger.received_at = datetime(2026, 5, 31, 17, tzinfo=timezone.utc)
            db.commit(); self.assertEqual(aging()['total_outstanding'], 400)
            current = asyncio.run(get_invoice_aging_report(house_id=inv.house_id, as_of_date='2026-05-31', db=db, current_user=db.get(User, self.user_id)))
            self.assertEqual(current.total_outstanding, 300)  # Current debt, historical bucket date only.
            db.add(CreditNote(invoice_id=inv.id, credit_amount=Decimal('300'), reason='Later', status='applied', created_at=datetime(2026,6,2,tzinfo=timezone.utc)))
            db.commit(); self.assertEqual(aging()['total_outstanding'], 400)

    def test_fifo_uses_debt_not_stale_paid_status(self):
        with self.Session() as db:
            db.get(Invoice, self.inv_id).status = InvoiceStatus.PAID
            db.commit()
            payments = Service.auto_apply_payments_fifo(db, self.ledger_id)
            self.assertEqual(sum(p.amount for p in payments), 600)
            self.assertEqual(self.balance()[:3], (600, 0, 0))

    def test_cashflow_uses_posted_receipts_without_slip_not_payin_amount(self):
        self.case_b()
        with self.Session() as db:
            ledger = db.get(IncomeTransaction, self.ledger_id)
            ledger.received_at = datetime(2026,5,31,17,30,tzinfo=timezone.utc)
            ledger.bank_transaction.effective_at = ledger.received_at
            db.get(PayinReport,self.payin_id).amount = Decimal('7777')  # Must never substitute slip money.
            db.commit()
            def report(month):
                return asyncio.run(get_cashflow_vs_ar_report(from_date=f'2026-{month:02d}-01',
                    to_date=f'2026-{month:02d}-30', group_by='month', house_id=ledger.house_id,
                    db=db,current_user=db.get(User,self.user_id)))
            self.assertEqual(report(6).summary.total_cash, 1000)
            self.assertEqual(report(5).summary.total_cash, 0)
            ledger.status = LedgerStatus.REVERSED; db.commit()
            self.assertEqual(report(6).summary.total_cash, 0)

    @patch('app.core.auth.SECRET_KEY', 'r2-local-auth-test-key-never-production')
    def test_legacy_invoices_rechecks_selected_and_active_membership(self):
        with self.Session() as db:
            user=db.get(User,self.user_id); user.role='resident'
            hid=db.get(Invoice,self.inv_id).house_id
            membership=ResidentMembership(user_id=user.id,house_id=hid)
            db.add_all([membership, HouseMember(user_id=user.id,house_id=hid)])
            db.commit()
            app=FastAPI(); app.include_router(accounting.router)
            app.dependency_overrides[get_db]=lambda:db
            with TestClient(app,base_url='https://testserver') as client:
                def login(house):
                    client.cookies.set('access_token',auth.create_access_token(dict(sub=str(user.id),role='resident',house_id=house,session_version=user.session_version)))
                url=f'/accounting/invoices/house/{hid}'
                login(hid); self.assertEqual(client.get(url).status_code,200)
                login(None); self.assertEqual(client.get(url).status_code,403)
                login(hid+1000); self.assertEqual(client.get(url).status_code,403)
                login(hid); membership.status=ResidentMembershipStatus.INACTIVE; db.commit()
                self.assertEqual(client.get(url).status_code,403)  # Legacy row intentionally still exists.

    def test_pending_context_separate_from_confirmed_money(self):
        with self.Session() as db:
            hid=db.get(Invoice,self.inv_id).house_id
            for state in (PayinStatus.PENDING, PayinStatus.SUBMITTED, PayinStatus.DRAFT):
                db.add(PayinReport(house_id=hid,amount=Decimal('100.25'),status=state,
                    transfer_date=datetime(2026,9,1,tzinfo=timezone.utc),transfer_hour=0,transfer_minute=0))
            db.commit()
            before=Service.generate_house_statement(db,hid,2026,5)
            self.assertEqual(before['pending_payins'],dict(scope='current',count=2,amount=200.5,excluded_from_confirmed_receipts=True))
            self.assertEqual(before['summary']['payments']['amount'],0)
            self.assertEqual(before['transactions'],[])

    def test_report_defaults_and_recent_activity_use_bangkok_and_posted_only(self):
        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                instant = datetime(2099, 5, 31, 17, 30, tzinfo=timezone.utc)
                return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)
        with self.Session() as db:
            ledger=db.get(IncomeTransaction,self.ledger_id)
            ledger.received_at=datetime(2099,5,31,17,30,tzinfo=timezone.utc)
            ledger.amount=Decimal('123.45')
            db.add(IncomeTransaction(house_id=ledger.house_id,amount=Decimal('456.78'),
                received_at=datetime(2099,6,2,tzinfo=timezone.utc),status=LedgerStatus.REVERSED))
            db.commit()
            with patch('app.api.reports.datetime',FrozenDateTime):
                aging=asyncio.run(get_invoice_aging_report(house_id=ledger.house_id,as_of_date=None,db=db,current_user=db.get(User,self.user_id)))
                self.assertEqual(aging.as_of,'2099-06-01')
                cash=asyncio.run(get_cashflow_vs_ar_report(from_date=None,to_date=None,group_by='month',house_id=ledger.house_id,db=db,current_user=db.get(User,self.user_id)))
                self.assertEqual((cash.from_date,cash.to_date),('2099-01-01','2099-06-01'))
                self.assertEqual(cash.summary.total_cash,123.45)
            village=asyncio.run(get_village_summary(db=db,current_user=db.get(User,self.user_id)))
            activities=village['recent_activities']
            income=next(a for a in activities if a['type']=='income' and a['amount']==123.45)
            self.assertEqual(income['timestamp'],'01/06/2099 00:30')
            self.assertFalse(any(a['type']=='income' and a['amount']==456.78 for a in activities))


if __name__ == '__main__': unittest.main()
