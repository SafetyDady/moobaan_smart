"""Automatic receipt/invoice lifecycle regressions on isolated local PostgreSQL."""
import asyncio
import unittest
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from types import SimpleNamespace
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select, text
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_credit_settlement_postgres import SettlementPostgresTests as Harness
from app.db.models import (House, User, Invoice, InvoiceStatus, IncomeTransaction,
    InvoicePayment, PayinReport, PayinStatus, BankAccount, BankStatementBatch,
    BankTransaction, PostingStatus, CreditNote, PaymentStatus)
from app.services.accounting import AccountingService
from app.api.bank_reconciliation import confirm_and_post
from app.api.bank_reconciliation import reverse_posted_transaction, ReverseRequest
from app.api.payins import accept_payin_report, apply_payin_fifo
from app.api.invoices import create_manual_invoice, ManualInvoiceCreate
from app.api import invoices as invoice_api, accounting as accounting_api
from app.models import InvoiceCreate as LegacyInvoiceCreate, InvoiceType, InvoiceItemBase
from app.db.models.income_transaction import LedgerStatus


class AutomaticAllocationTests(unittest.TestCase):
    setUpClass = classmethod(Harness.setUpClass.__func__)
    cleanup_schema = classmethod(Harness.cleanup_schema.__func__)

    def setUp(self):
        with self.Session() as db:
            user = User(full_name='Automatic regression', role='super_admin')
            house = House(house_code=uuid.uuid4().hex[:20], owner_name='Automatic regression')
            account = BankAccount(bank_code='TEST', account_no_masked='test')
            db.add_all([user, house, account]); db.flush()
            batch = BankStatementBatch(bank_account_id=account.id, year=2026, month=5,
                original_filename='test.csv', uploaded_by=user.id, status='CONFIRMED')
            db.add(batch); db.commit()
            self.house_id, self.user_id, self.account_id, self.batch_id = house.id, user.id, account.id, batch.id

    def receipt(self, amount='600', *, posted=True, day=11, house_id=None):
        with self.Session() as db:
            at = datetime(2026, 5, day, 0, 5, tzinfo=timezone.utc)
            payin = PayinReport(house_id=house_id or self.house_id, amount=Decimal(amount),
                transfer_date=at, transfer_hour=7, transfer_minute=5,
                status=PayinStatus.ACCEPTED if posted else PayinStatus.SUBMITTED)
            db.add(payin); db.flush()
            bank = BankTransaction(bank_statement_batch_id=self.batch_id, bank_account_id=self.account_id,
                effective_at=at, description='test receipt', credit=Decimal(amount), debit=0,
                raw_row={}, fingerprint=uuid.uuid4().hex, matched_payin_id=payin.id,
                posting_status=PostingStatus.POSTED if posted else PostingStatus.MATCHED)
            db.add(bank); db.flush(); payin.matched_statement_txn_id=bank.id
            ledger=None
            if posted:
                ledger=IncomeTransaction(house_id=payin.house_id, payin_id=payin.id, amount=payin.amount,
                    received_at=at, reference_bank_transaction_id=bank.id)
                db.add(ledger); db.flush()
            db.commit()
            return ledger.id if ledger else None, str(bank.id), payin.id

    def invoice(self, amount='600', *, month=5, due=None, manual=False):
        with self.Session() as db:
            inv=Invoice(house_id=self.house_id, cycle_year=0 if manual else 2026,
                cycle_month=0 if manual else month, issue_date=date(2026,5,1),
                due_date=due or date(2026,month,28), total_amount=Decimal(amount),
                status=InvoiceStatus.ISSUED,is_manual=manual)
            db.add(inv);db.commit();return inv.id

    def post(self, bank_id, db=None):
        if db is not None:
            return asyncio.run(confirm_and_post(bank_id, data=None, db=db, current_user=db.get(User,self.user_id)))
        with self.Session() as session:return self.post(bank_id, session)

    def pairs(self):
        with self.Session() as db:
            return [(p.income_transaction_id,p.invoice_id,p.amount) for p in db.query(InvoicePayment)
                .join(Invoice).filter(Invoice.house_id==self.house_id,InvoicePayment.status==PaymentStatus.ACTIVE)
                .order_by(InvoicePayment.id).all()]

    def test_received_before_monthly_invoice_is_automatically_applied(self):
        ledger,_,_=self.receipt()
        with self.Session() as db:AccountingService.auto_generate_invoices(db,2026,5)
        with self.Session() as db:
            inv=db.query(Invoice).filter_by(house_id=self.house_id,cycle_year=2026,cycle_month=5).one()
            self.assertEqual(inv.get_total_paid_decimal(),Decimal('600'))
            self.assertEqual(self.pairs(),[(ledger,inv.id,Decimal('600'))])

    def test_new_receipt_consumes_older_unused_money_first(self):
        old,_,_=self.receipt()
        inv=self.invoice()
        _,bank,_=self.receipt(posted=False,day=20)
        self.post(bank)
        self.assertEqual(self.pairs(),[(old,inv,Decimal('600'))])

    def test_confirm_before_bill_then_generate_and_retry(self):
        _,bank,_=self.receipt(posted=False)
        result=self.post(bank)
        self.assertEqual(result['allocations'],[])
        self.assertEqual(self.post(bank)['status'],'already_posted')
        with self.Session() as db:
            AccountingService.auto_generate_invoices(db,2026,5)
            AccountingService.auto_generate_invoices(db,2026,5)
        self.assertEqual(len(self.pairs()),1)
        self.assertEqual(self.pairs()[0][2],Decimal('600'))

    def test_invoice_before_receipt_auto_settles(self):
        inv=self.invoice()
        _,bank,_=self.receipt(posted=False)
        posted=self.post(bank)
        self.assertEqual(self.pairs(),[(posted['income_transaction_id'],inv,Decimal('600'))])

    def test_prepayment_spans_generated_months_exactly_once(self):
        ledger,_,_=self.receipt('1500.24')
        with self.Session() as db:
            for month in [5,6,7,7]:AccountingService.auto_generate_invoices(db,2026,month)
            invoices=db.query(Invoice).filter_by(house_id=self.house_id).order_by(Invoice.cycle_month).all()
            self.assertEqual([i.get_total_paid_decimal() for i in invoices],
                [Decimal('600'),Decimal('600'),Decimal('300.24')])
            self.assertEqual(db.get(IncomeTransaction,ledger).get_unallocated_amount(),0)
        self.assertEqual(len(self.pairs()),3)

    def test_manual_bill_uses_due_date_not_zero_cycle_priority(self):
        monthly=self.invoice('600',due=date.today())
        ledger,_,_=self.receipt('700.25')
        with self.Session() as db:
            result=asyncio.run(create_manual_invoice(ManualInvoiceCreate(house_id=self.house_id,
                amount=20000,description='Special invoice',due_date=date.today()+timedelta(days=10)),
                db=db,current_user=db.get(User,self.user_id)))
        self.assertEqual(self.pairs(),[(ledger,monthly,Decimal('600')),
                                      (ledger,result['id'],Decimal('100.25'))])

    def test_credits_partial_payment_and_stale_status(self):
        inv=self.invoice('600')
        ledger,_,_=self.receipt('500.01')
        with self.Session() as db:
            db.add(CreditNote(invoice_id=inv,credit_amount=Decimal('200.02'),reason='test',
                              status='applied',created_by_user_id=self.user_id))
            db.get(Invoice,inv).status=InvoiceStatus.PAID  # Deliberately stale cache/state.
            db.commit()
            AccountingService.auto_apply_payments_fifo(db,ledger)
            bill=db.get(Invoice,inv)
            self.assertEqual(bill.get_total_paid_decimal(),Decimal('399.98'))
            self.assertEqual(bill.get_remaining_balance_decimal(),0)
            self.assertEqual(db.get(IncomeTransaction,ledger).get_unallocated_amount(),100.03)

    def test_pending_reversed_and_foreign_house_money_excluded(self):
        inv=self.invoice()
        pending,_,payin=self.receipt('600')
        reversed_id,_,_=self.receipt('600',day=12)
        with self.Session() as db:
            db.get(PayinReport,payin).status=PayinStatus.PENDING
            db.get(IncomeTransaction,reversed_id).status=LedgerStatus.REVERSED
            other=House(house_code=uuid.uuid4().hex[:20],owner_name='Other')
            db.add(other);db.commit();other_id=other.id
        foreign,_,_=self.receipt('1000',house_id=other_id)
        valid,_,_=self.receipt('200.01',day=20)
        with self.Session() as db:
            AccountingService.auto_apply_payments_fifo(db,valid)
            self.assertEqual(db.get(IncomeTransaction,foreign).get_unallocated_amount(),1000)
        self.assertEqual(self.pairs(),[(valid,inv,Decimal('200.01'))])

    def test_normal_automation_does_not_rewrite_existing_allocations(self):
        may=self.invoice(month=5);june=self.invoice(month=6)
        old,_,_=self.receipt(day=11);later,_,_=self.receipt(day=20)
        with self.Session() as db:
            previous=InvoicePayment(invoice_id=may,income_transaction_id=later,amount=Decimal('600'))
            db.add(previous);db.commit();pid=previous.id;at=previous.applied_at
            AccountingService.auto_apply_payments_fifo(db,old)
            db.refresh(previous)
            self.assertEqual((previous.id,previous.income_transaction_id,previous.invoice_id,
                              previous.applied_at,previous.status),(pid,later,may,at,PaymentStatus.ACTIVE))
        self.assertEqual(self.pairs(),[(later,may,Decimal('600')),(old,june,Decimal('600'))])

    def test_both_legacy_accept_routes_allocate_in_same_transaction(self):
        self.invoice('1200')
        _,_,payin1=self.receipt(posted=False)
        _,_,payin2=self.receipt(posted=False,day=20)
        with self.Session() as db:
            asyncio.run(accept_payin_report(payin1,db=db,current_user=db.get(User,self.user_id)))
            AccountingService.accept_payin(db,payin2,self.user_id)
        self.assertEqual(sum(p[2] for p in self.pairs()),Decimal('1200'))

    def test_legacy_fifo_uses_house_funds_and_actual_balance(self):
        inv=self.invoice()
        old,_,_=self.receipt()
        _,_,new_payin=self.receipt(day=20)
        with self.Session() as db:
            db.get(Invoice,inv).status=InvoiceStatus.PAID;db.commit()
            result=asyncio.run(apply_payin_fifo(new_payin,db=db,current_user=db.get(User,self.user_id)))
        self.assertEqual(result['allocation_scope'],'household')
        self.assertEqual(self.pairs(),[(old,inv,Decimal('600'))])

    def test_both_legacy_invoice_creators_consume_unused_money(self):
        ledger,_,_=self.receipt('1200')
        with self.Session() as db:
            result=asyncio.run(invoice_api.create_invoice(LegacyInvoiceCreate(house_id=self.house_id,
                invoice_type=InvoiceType.AUTO_MONTHLY,cycle='2026-05',due_date=date(2026,5,28),
                items=[InvoiceItemBase(description='test',amount=600)]),db=db))
            self.assertEqual(result.status,'PAID')
            self.assertEqual(result.paid,600)
            result2=asyncio.run(accounting_api.create_invoice(accounting_api.InvoiceCreate(
                house_id=self.house_id,cycle_year=2026,cycle_month=6,issue_date=date(2026,6,1),
                due_date=date(2026,6,28),total_amount=Decimal('600')),
                db=db,current_user=db.get(User,self.user_id)))
            self.assertEqual(result2['invoice']['status'],'PAID')
        self.assertEqual(sum(p[2] for p in self.pairs()),Decimal('1200'))

    def test_legacy_invoice_writes_require_authentication(self):
        app=FastAPI();app.include_router(invoice_api.router)
        with TestClient(app) as client:
            for method,path in [('POST','/api/invoices'),('PUT','/api/invoices/1'),('DELETE','/api/invoices/1')]:
                self.assertEqual(client.request(method,path,json={}).status_code,401)

    def test_resident_cannot_choose_or_create_invoices_through_write_apis(self):
        from app.core.deps import get_current_user
        from app.api import bank_reconciliation, payins
        app=FastAPI()
        for router in [invoice_api.router,accounting_api.router,bank_reconciliation.router,payins.router]:app.include_router(router)
        app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(id=999,role='resident')
        with TestClient(app) as client:
            for method,path in [('POST','/api/invoices'),('PUT','/api/invoices/1'),('DELETE','/api/invoices/1'),
                ('POST','/api/invoices/generate-monthly'),('POST','/api/invoices/manual'),
                ('POST','/api/invoices/1/apply-payment'),('POST','/api/payin-reports/1/apply-fifo'),
                ('POST','/api/bank-statements/transactions/00000000-0000-0000-0000-000000000000/confirm-and-post')]:
                with self.subTest(path=path):self.assertEqual(client.request(method,path,json={}).status_code,403)

    def test_failure_after_automatic_insert_rolls_back_receipt_and_allocations(self):
        self.invoice()
        _,bank,payin=self.receipt(posted=False)
        from app.services.automatic_allocation import apply_prepared_funds as real
        def fail_after_insert(db,scope):
            real(db,scope)
            raise RuntimeError('simulated failure after allocation flush')
        with patch('app.api.bank_reconciliation.apply_prepared_funds',side_effect=fail_after_insert):
            with self.assertRaises(HTTPException):self.post(bank)
        self.assertEqual(self.pairs(),[])
        with self.Session() as db:
            self.assertEqual(db.get(BankTransaction,uuid.UUID(bank)).posting_status,PostingStatus.MATCHED)
            self.assertEqual(db.get(PayinReport,payin).status,PayinStatus.SUBMITTED)
            self.assertEqual(db.query(IncomeTransaction).filter_by(payin_id=payin).count(),0)

    def test_full_credit_and_due_date_ties_are_deterministic(self):
        full=self.invoice(month=5)
        first=self.invoice(month=6,due=date(2026,6,28))
        second=self.invoice(month=7,due=date(2026,6,28))
        ledger,_,_=self.receipt('600.01')
        with self.Session() as db:
            db.add(CreditNote(invoice_id=full,credit_amount=Decimal('600'),reason='test',
                status='applied',created_by_user_id=self.user_id));db.commit()
            AccountingService.auto_apply_payments_fifo(db,ledger)
        self.assertEqual(self.pairs(),[(ledger,first,Decimal('600')),(ledger,second,Decimal('.01'))])

    def test_reusing_prepared_scope_does_not_spend_same_money_twice(self):
        from app.services.automatic_allocation import prepare_allocation, apply_prepared_funds
        self.invoice('600',month=5);self.invoice('600',month=6)
        self.receipt('700')
        with self.Session() as db:
            scope=prepare_allocation(db,[self.house_id])
            self.assertEqual(len(apply_prepared_funds(db,scope)),2)
            self.assertEqual(apply_prepared_funds(db,scope),[])
            db.commit()
        self.assertEqual(sum(p[2] for p in self.pairs()),Decimal('700'))

    def race(self, first_action, second_action, reject_second=False):
        staged,release=Event(),Event()
        def first():
            with self.Session() as db:
                real=db.commit
                def gated():
                    staged.set()
                    if not release.wait(15):raise RuntimeError('Release timeout')
                    real()
                db.commit=gated
                first_action(db)
        def second():
            with self.Session() as db:
                # Load house bills before the first transaction commits.
                for inv in db.query(Invoice).filter_by(house_id=self.house_id):inv.get_total_paid()
                cached_banks=db.query(BankTransaction).filter_by(bank_statement_batch_id=self.batch_id).all()
                if not staged.wait(10):raise RuntimeError('First action timeout')
                try:second_action(db);return 'ok'
                except (HTTPException,ValueError):
                    db.rollback();return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1=pool.submit(first);f2=pool.submit(second)
            try:
                self.assertTrue(staged.wait(10))
                deadline=time.monotonic()+7;blocked=False
                while time.monotonic()<deadline:
                    with self.admin.connect() as c:
                        blocked=c.execute(text('SELECT EXISTS (SELECT 1 FROM pg_stat_activity '
                            'WHERE application_name=:name AND cardinality(pg_blocking_pids(pid))>0)'),{'name':self.schema}).scalar()
                    if blocked:break
                    time.sleep(.03)
                self.assertTrue(blocked,'Second transaction must really block in PostgreSQL')
            finally:release.set()
            f1.result(timeout=10)
            self.assertEqual(f2.result(timeout=10),'rejected' if reject_second else 'ok')

    def test_race_confirmation_then_monthly_generation(self):
        _,bank,_=self.receipt(posted=False)
        self.race(lambda db:self.post(bank,db),lambda db:AccountingService.auto_generate_invoices(db,2026,5))
        self.assertEqual(len(self.pairs()),1)
        self.assertEqual(self.pairs()[0][2],Decimal('600'))

    def test_race_generation_then_confirmation(self):
        _,bank,_=self.receipt(posted=False)
        self.race(lambda db:AccountingService.auto_generate_invoices(db,2026,5),lambda db:self.post(bank,db))
        self.assertEqual(len(self.pairs()),1)

    def test_race_two_generations_do_not_duplicate_bills_or_allocations(self):
        self.receipt()
        self.race(lambda db:AccountingService.auto_generate_invoices(db,2026,5),
                  lambda db:AccountingService.auto_generate_invoices(db,2026,5))
        with self.Session() as db:
            self.assertEqual(db.query(Invoice).filter_by(house_id=self.house_id,cycle_year=2026,cycle_month=5).count(),1)
        self.assertEqual(len(self.pairs()),1)

    def test_race_two_confirmations_share_house_balance(self):
        inv=self.invoice()
        _,a,_=self.receipt(posted=False)
        _,b,_=self.receipt(posted=False,day=20)
        self.race(lambda db:self.post(a,db),lambda db:self.post(b,db))
        self.assertEqual(sum(p[2] for p in self.pairs()),Decimal('600'))

    def test_race_same_confirmation_is_idempotent(self):
        self.invoice()
        _,bank,_=self.receipt(posted=False)
        self.race(lambda db:self.post(bank,db),lambda db:self.post(bank,db))
        self.assertEqual(len(self.pairs()),1)

    def test_race_automatic_then_explicit_payment_rechecks_ledger(self):
        inv=self.invoice()
        ledger,_,_=self.receipt()
        self.race(lambda db:AccountingService.auto_apply_payments_fifo(db,ledger),
            lambda db:AccountingService.apply_payment_to_invoice(db,ledger,inv,Decimal('600')),True)
        self.assertEqual(len(self.pairs()),1)

    def test_race_reversal_then_generation_excludes_reversed_money(self):
        ledger,bank,_=self.receipt()
        self.race(lambda db:asyncio.run(reverse_posted_transaction(bank,ReverseRequest(reason='test'),
            current_user=db.get(User,self.user_id),db=db)),
            lambda db:AccountingService.auto_generate_invoices(db,2026,5))
        self.assertEqual(self.pairs(),[])


del Harness  # Do not rediscover the imported harness's own tests in this module.
if __name__=='__main__':unittest.main(verbosity=2)
