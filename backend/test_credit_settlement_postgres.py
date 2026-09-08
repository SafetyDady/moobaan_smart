"""Real PostgreSQL regression tests; never uses the application's DATABASE_URL.

Set CREDIT_TEST_DATABASE_URL to a localhost database named moobaan_credit_test.
Run: python -B -m unittest test_credit_settlement_postgres -v
Each run creates and removes only its own randomly named schema.
"""
import asyncio
import os
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
from threading import Event

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import ENUM

from app.db.session import Base
from app.db.models import (House, User, Invoice, InvoiceStatus, CreditNote,
    IncomeTransaction, InvoicePayment, PaymentStatus, PayinReport, PayinStatus,
    BankAccount, BankStatementBatch, BankTransaction, PostingStatus)
from app.api.credit_notes import CreditNoteCreate, create_credit_note
from app.api.invoices import ApplyPaymentRequest, apply_payment_to_invoice
from app.api.payins import apply_payin_fifo
from app.services.accounting import AccountingService
from app.api.bank_reconciliation import (confirm_and_post, ConfirmPostRequest,
    reverse_posted_transaction, ReverseRequest)


class SettlementPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = os.environ.get('CREDIT_TEST_DATABASE_URL')
        if not raw:
            raise RuntimeError('Set CREDIT_TEST_DATABASE_URL explicitly; PostgreSQL tests must not silently skip')
        url = make_url(raw)
        if (url.get_backend_name() != 'postgresql' or url.host not in ('localhost', '127.0.0.1')
                or url.database != 'moobaan_credit_test'):
            raise RuntimeError('Only a local PostgreSQL database named moobaan_credit_test is allowed')
        cls.schema = 'credit_test_' + uuid.uuid4().hex
        cls.admin = create_engine(url)
        with cls.admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA {cls.schema}'))
        cls.engine = create_engine(url, connect_args={
            'options': f'-c search_path={cls.schema} -c statement_timeout=15000',
            'application_name': cls.schema,
        })
        cls.addClassCleanup(cls.cleanup_schema)
        with cls.engine.begin() as conn:
            # Production migrations create these enums independently of tables.
            for table in Base.metadata.tables.values():
                for column in table.columns:
                    if isinstance(column.type, ENUM) and not column.type.create_type:
                        column.type.create(conn, checkfirst=True)
            Base.metadata.create_all(conn)
        cls.Session = sessionmaker(bind=cls.engine, autoflush=False)

    @classmethod
    def cleanup_schema(cls):
        cls.engine.dispose()
        with cls.admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA {cls.schema} CASCADE'))
        cls.admin.dispose()

    def setUp(self):
        with self.Session() as db:
            user = User(full_name='Regression test', role='super_admin')
            house = House(house_code=uuid.uuid4().hex[:20], owner_name='Regression test')
            db.add_all([user, house]); db.flush()
            inv = Invoice(house_id=house.id, cycle_year=2026, cycle_month=9,
                issue_date=date.today(), due_date=date.today(), total_amount=Decimal('600'),
                status=InvoiceStatus.ISSUED, is_manual=True)
            payin = PayinReport(house_id=house.id, amount=Decimal('1000'),
                transfer_date=datetime.now(timezone.utc), transfer_hour=12, transfer_minute=0,
                status=PayinStatus.ACCEPTED)
            db.add_all([inv, payin]); db.flush()
            ledger = IncomeTransaction(house_id=house.id, payin_id=payin.id,
                amount=Decimal('1000'), received_at=datetime.now(timezone.utc))
            db.add(ledger); db.commit()
            self.inv_id, self.user_id, self.ledger_id, self.payin_id = inv.id, user.id, ledger.id, payin.id

    def credit(self, db, amount, full=False):
        return asyncio.run(create_credit_note(
            CreditNoteCreate(invoice_id=self.inv_id, credit_amount=amount,
                             is_full_credit=full, reason='test'),
            db=db, current_user=db.get(User, self.user_id)))

    def payment(self, db, amount, service=False):
        if service:
            return AccountingService.apply_payment_to_invoice(db, self.ledger_id, self.inv_id, Decimal(amount))
        return asyncio.run(apply_payment_to_invoice(self.inv_id,
            ApplyPaymentRequest(income_transaction_id=self.ledger_id, amount=amount),
            db=db, current_user=db.get(User, self.user_id)))

    def balance(self):
        with self.Session() as db:
            inv = db.get(Invoice, self.inv_id)
            return inv.get_total_paid(), inv.get_total_credited(), inv.get_remaining_balance(), inv.status

    def bank_fixture(self):
        with self.Session() as db:
            house_id = db.get(Invoice, self.inv_id).house_id
            account = BankAccount(bank_code='TEST', account_no_masked='test')
            payin = PayinReport(house_id=house_id, amount=Decimal('400'),
                transfer_date=datetime.now(timezone.utc), transfer_hour=12, transfer_minute=0,
                status=PayinStatus.SUBMITTED)
            db.add_all([account, payin]); db.flush()
            batch = BankStatementBatch(bank_account_id=account.id, year=2026, month=9,
                original_filename='test.csv', uploaded_by=self.user_id)
            db.add(batch); db.flush()
            txn = BankTransaction(bank_statement_batch_id=batch.id, bank_account_id=account.id,
                effective_at=datetime.now(timezone.utc), description='test', credit=Decimal('400'),
                raw_row={}, fingerprint=uuid.uuid4().hex, matched_payin_id=payin.id,
                posting_status=PostingStatus.MATCHED)
            db.add(txn); db.commit()
            self.bank_id = str(txn.id)

    def bank_post(self, db, explicit=False):
        return asyncio.run(confirm_and_post(self.bank_id,
            data=ConfirmPostRequest(invoice_id=self.inv_id) if explicit else None,
            current_user=db.get(User, self.user_id), db=db))

    def test_bank_explicit_and_reverse_preserve_credit(self):
        self.bank_fixture()
        with self.Session() as db:
            self.credit(db, '400')
            self.bank_post(db, explicit=True)
            self.assertEqual(self.balance()[:3], (200, 400, 0))
            asyncio.run(reverse_posted_transaction(self.bank_id, ReverseRequest(reason='test'),
                current_user=db.get(User, self.user_id), db=db))
        self.assertEqual(self.balance(), (0, 400, 200, InvoiceStatus.ISSUED))

    def test_full_credit_clears_only_outstanding(self):
        with self.Session() as db:
            self.payment(db, '400')
            result = self.credit(db, '200', full=True)
            self.assertEqual(result.credit_amount, 200)
        self.assertEqual(self.balance(), (400, 200, 0, InvoiceStatus.PAID))

    def test_credit_above_outstanding_and_paid_invoice_rejected(self):
        with self.Session() as db:
            self.payment(db, '400')
            with self.assertRaises(HTTPException) as caught:
                self.credit(db, '201')
            self.assertEqual(caught.exception.status_code, 400)
            db.rollback()
            self.payment(db, '200')
            with self.assertRaises(HTTPException):
                self.credit(db, '1', full=True)
        self.assertEqual(self.balance()[:3], (600, 0, 0))

    def test_special_invoice_and_accumulated_credit(self):
        with self.Session() as db:
            db.get(Invoice, self.inv_id).total_amount = Decimal('20000'); db.commit()
            self.credit(db, '5000')
            self.assertEqual(self.balance()[:3], (0, 5000, 15000))
            self.credit(db, '15000', full=True)
        self.assertEqual(self.balance(), (0, 20000, 0, InvoiceStatus.CANCELLED))

    def test_reversed_payment_does_not_reduce_creditable_balance(self):
        with self.Session() as db:
            db.add(InvoicePayment(invoice_id=self.inv_id, income_transaction_id=self.ledger_id,
                amount=Decimal('400'), status=PaymentStatus.REVERSED)); db.commit()
            self.credit(db, '600', full=True)
        self.assertEqual(self.balance()[:3], (0, 600, 0))

    def test_decimal_cents_close_exactly(self):
        with self.Session() as db:
            db.get(Invoice, self.inv_id).total_amount = Decimal('0.30'); db.commit()
            self.payment(db, '0.10')
            self.credit(db, '0.20', full=True)
        self.assertEqual(self.balance(), (0.1, 0.2, 0, InvoiceStatus.PAID))

    def test_service_accepts_exact_decimal_balance(self):
        with self.Session() as db:
            db.get(Invoice, self.inv_id).total_amount = Decimal('0.30'); db.commit()
            self.payment(db, '0.30', service=True)
        self.assertEqual(self.balance(), (0.3, 0, 0, InvoiceStatus.PAID))

    def test_service_fifo_multiple_invoices_one_ledger(self):
        with self.Session() as db:
            first = db.get(Invoice, self.inv_id)
            second = Invoice(house_id=first.house_id, cycle_year=2026, cycle_month=10,
                issue_date=date.today(), due_date=date.today(), total_amount=Decimal('600'),
                status=InvoiceStatus.ISSUED, is_manual=True)
            db.add(second); db.commit(); second_id = second.id
            result = AccountingService.auto_apply_payments_fifo(db, self.ledger_id)
            self.assertEqual(len(result), 2)
            self.assertEqual(db.get(Invoice, second_id).get_remaining_balance(), 200)
            self.assertEqual(db.get(IncomeTransaction, self.ledger_id).get_unallocated_amount(), 0)
        self.assertEqual(self.balance()[:3], (600, 0, 0))

    def test_invalid_precision_and_nonfinite_amounts_rejected(self):
        for amount in ('NaN', 'Infinity', '-1', '0', '0.001'):
            with self.subTest(amount=amount), self.assertRaises(ValidationError):
                CreditNoteCreate(invoice_id=self.inv_id, credit_amount=amount, reason='test')

    def test_fifo_paths_respect_credits(self):
        for service in (False, True):
            if service:
                self.setUp()
            with self.Session() as db:
                self.credit(db, '400')
                if service:
                    AccountingService.auto_apply_payments_fifo(db, self.ledger_id)
                else:
                    asyncio.run(apply_payin_fifo(self.payin_id, db=db,
                        current_user=db.get(User, self.user_id)))
            self.assertEqual(self.balance()[:3], (200, 400, 0))

    def race(self, first_action, second_action, second_ok=False):
        staged, release, preloaded = Event(), Event(), Event()
        def first():
            with self.Session() as db:
                original = db.commit
                def gated_commit():
                    staged.set()
                    if not release.wait(12):
                        raise RuntimeError('Test release timeout')
                    original()
                db.commit = gated_commit
                if not preloaded.wait(5):
                    raise RuntimeError('Preload timeout')
                first_action(db)
        def second():
            with self.Session() as db:
                # Deliberately cache the balance BEFORE the other commit.
                inv = db.get(Invoice, self.inv_id)
                inv.get_remaining_balance()
                preloaded.set()
                if not staged.wait(5):
                    raise RuntimeError('First writer timeout')
                try:
                    second_action(db)
                    return 'ok'
                except (HTTPException, ValueError):
                    db.rollback()
                    return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1, f2 = pool.submit(first), pool.submit(second)
            try:
                self.assertTrue(staged.wait(5))
                blocked = False
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    with self.admin.connect() as conn:
                        blocked = conn.execute(text('SELECT EXISTS (SELECT 1 FROM pg_stat_activity '
                            'WHERE application_name=:name AND cardinality(pg_blocking_pids(pid))>0)'),
                            {'name': self.schema}).scalar()
                    if blocked:
                        break
                    time.sleep(0.05)
                self.assertTrue(blocked, 'Second real PostgreSQL transaction must wait on a lock')
            finally:
                release.set()
            f1.result(timeout=8)
            self.assertEqual(f2.result(timeout=8), 'ok' if second_ok else 'rejected')
        paid, credit, outstanding, _ = self.balance()
        self.assertLessEqual(paid + credit, 600)
        return paid, credit, outstanding

    def test_race_two_credits_refreshes_cached_balance(self):
        self.assertEqual(self.race(lambda db: self.credit(db, '400'),
            lambda db: self.credit(db, '400')), (0, 400, 200))

    def test_race_payment_then_credit(self):
        self.assertEqual(self.race(lambda db: self.payment(db, '400'),
            lambda db: self.credit(db, '400')), (400, 0, 200))

    def test_race_credit_then_payment_api(self):
        self.assertEqual(self.race(lambda db: self.credit(db, '400'),
            lambda db: self.payment(db, '400')), (0, 400, 200))

    def test_race_credit_then_payment_service(self):
        self.assertEqual(self.race(lambda db: self.credit(db, '400'),
            lambda db: self.payment(db, '400', service=True)), (0, 400, 200))

    def test_race_two_full_credits(self):
        self.assertEqual(self.race(lambda db: self.credit(db, '600', full=True),
            lambda db: self.credit(db, '600', full=True)), (0, 600, 0))

    def test_race_two_payments_same_ledger(self):
        self.assertEqual(self.race(lambda db: self.payment(db, '400'),
            lambda db: self.payment(db, '400')), (400, 0, 200))

    def test_race_credit_then_bank_fifo(self):
        self.bank_fixture()
        self.assertEqual(self.race(lambda db: self.credit(db, '400'),
            lambda db: self.bank_post(db), second_ok=True), (200, 400, 0))

    def test_race_bank_then_credit(self):
        self.bank_fixture()
        self.assertEqual(self.race(lambda db: self.bank_post(db),
            lambda db: self.credit(db, '400')), (400, 0, 200))

    def test_race_credit_then_payin_fifo(self):
        self.assertEqual(self.race(lambda db: self.credit(db, '400'),
            lambda db: asyncio.run(apply_payin_fifo(self.payin_id, db=db,
                current_user=db.get(User, self.user_id))), second_ok=True), (200, 400, 0))

    def test_race_credit_then_service_fifo(self):
        self.assertEqual(self.race(lambda db: self.credit(db, '400'),
            lambda db: AccountingService.auto_apply_payments_fifo(db, self.ledger_id),
            second_ok=True), (200, 400, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
