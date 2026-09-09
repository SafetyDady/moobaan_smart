"""Legacy read-report regression tests on an isolated local PostgreSQL schema.

Uses the same guarded local test database as settlement tests; no production URL.
Run: python -B -m unittest test_accounting_reads_postgres -v
"""
import unittest
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

import test_credit_settlement_postgres as fixtures
from app.api import accounting
from app.core.deps import get_db, get_current_user, get_house_id_from_token
from app.core import auth
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus
from app.db.models import (House, HouseMember, User, Invoice, InvoicePayment,
    IncomeTransaction, PayinReport, PayinStatus, PaymentStatus, CreditNote)
from app.db.models.house import HouseStatus
from app.db.models.income_transaction import LedgerStatus
from app.services.accounting import AccountingService as Service


class AccountingReadTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.SettlementPostgresTests.setUpClass.__func__)
    cleanup_schema = classmethod(fixtures.SettlementPostgresTests.cleanup_schema.__func__)
    setUp = fixtures.SettlementPostgresTests.setUp

    def seed_cash(self, db):
        inv = db.get(Invoice, self.inv_id)
        inv.issue_date = date(2026, 5, 10)
        inv.total_amount = Decimal('600.15')
        # A manual invoice's issue date, not its cycle metadata, dates the debt.
        ledger = db.get(IncomeTransaction, self.ledger_id)
        ledger.amount = Decimal('1000.30')
        ledger.received_at = datetime(2026, 5, 11, 16, 59, 59, 999999, tzinfo=timezone.utc)
        later = Invoice(house_id=inv.house_id, is_manual=True, total_amount=Decimal('20000'),
            cycle_year=2026, cycle_month=6,
            issue_date=date(2026, 6, 8), due_date=date(2026, 6, 30), manual_reason='Special')
        db.add(later); db.flush()
        db.add_all([
            InvoicePayment(invoice_id=inv.id, income_transaction_id=ledger.id,
                amount=Decimal('100.10'), status=PaymentStatus.ACTIVE),
            InvoicePayment(invoice_id=inv.id, income_transaction_id=ledger.id,
                amount=Decimal('200.05'), status=PaymentStatus.ACTIVE),
            InvoicePayment(invoice_id=inv.id, income_transaction_id=ledger.id,
                amount=Decimal('50'), status=PaymentStatus.REVERSED),
            CreditNote(invoice_id=inv.id, credit_amount=Decimal('99.99'), reason='Applied',
                status='applied', created_at=datetime(2026, 5, 20, tzinfo=timezone.utc)),
            CreditNote(invoice_id=inv.id, credit_amount=Decimal('999'), reason='Not applied',
                status='issued', created_at=datetime(2026, 5, 20, tzinfo=timezone.utc)),
            CreditNote(invoice_id=later.id, credit_amount=Decimal('5000'), reason='Special credit',
                status='applied', created_at=datetime(2026, 6, 9, tzinfo=timezone.utc)),
        ])
        for amount, at, posted in [
            ('22.22', datetime(2026, 5, 31, 17, tzinfo=timezone.utc), True),
            ('77', datetime(2026, 5, 12, tzinfo=timezone.utc), False),
        ]:
            payin = PayinReport(house_id=inv.house_id, amount=Decimal(amount), transfer_date=at,
                transfer_hour=0, transfer_minute=0, status=PayinStatus.ACCEPTED)
            db.add(payin); db.flush()
            db.add(IncomeTransaction(house_id=inv.house_id, payin_id=payin.id,
                amount=Decimal(amount), received_at=at,
                status=LedgerStatus.POSTED if posted else LedgerStatus.REVERSED))
        db.add(PayinReport(house_id=inv.house_id, amount=Decimal('999'),
            transfer_date=datetime(2026, 5, 12, tzinfo=timezone.utc), transfer_hour=0,
            transfer_minute=0, status=PayinStatus.PENDING))
        db.commit(); db.expire_all()
        db.execute(text("SET LOCAL TIME ZONE 'UTC'"))
        return inv.house_id

    def test_snapshot_counts_receipts_once_and_excludes_pending_reversed_unapplied(self):
        with self.Session() as db:
            hid = self.seed_cash(db)
            may = Service.calculate_month_end_snapshot(db, hid, 2026, 5)
            self.assertEqual([may[k] for k in ('opening_balance', 'invoice_total',
                'payment_total', 'credit_total', 'closing_balance')], [0, 600.15, 1000.30, 99.99, -500.14])
            june = Service.calculate_month_end_snapshot(db, hid, 2026, 6)
            self.assertEqual([june[k] for k in ('opening_balance', 'invoice_total',
                'payment_total', 'credit_total', 'closing_balance')], [-500.14, 20000, 22.22, 5000, 14477.64])
            empty = Service.calculate_month_end_snapshot(db, hid, 2026, 1)
            self.assertEqual(empty['opening_balance'], 0)
            self.assertEqual(empty['closing_balance'], 0)

    def test_exact_day_bounds_and_bangkok_midnight(self):
        with self.Session() as db:
            hid = self.seed_cash(db)
            day = Service.generate_statement(db, hid, date(2026, 5, 11), date(2026, 5, 11))
            self.assertEqual(day['opening_balance'], 600.15)
            self.assertEqual(day['closing_balance'], -400.15)
            self.assertEqual(day['rows'][-1]['date'], date(2026, 5, 11))
            self.assertEqual(day['summary']['payment_total'], 1000.30)
            # 17:00 UTC belongs to the following Bangkok date/month.
            boundary = Service.generate_statement(db, hid, date(2026, 6, 1), date(2026, 6, 1))
            self.assertEqual(boundary['opening_balance'], -500.14)
            self.assertEqual(boundary['summary']['payment_total'], 22.22)
            self.assertEqual(boundary['closing_balance'], -522.36)
            self.assertEqual(boundary['rows'][-1]['balance'], boundary['closing_balance'])
            last_may = Service.generate_statement(db, hid, date(2026, 5, 31), date(2026, 5, 31))
            self.assertEqual(len(last_may['rows']), 1)
            self.assertEqual(last_may['closing_balance'], -500.14)

    def test_monthly_rows_summary_snapshot_and_invoice_balance_have_explicit_meanings(self):
        with self.Session() as db:
            hid = self.seed_cash(db)
            for month, end in [(5, 31), (6, 30)]:
                monthly = Service.generate_house_statement(db, hid, 2026, month)
                ranged = Service.generate_statement(db, hid, date(2026, month, 1), date(2026, month, end))
                self.assertEqual(monthly['snapshot']['closing_balance'], ranged['closing_balance'])
                running = Decimal(str(monthly['summary']['opening_balance']['amount']))
                for row in monthly['transactions']:
                    running += Decimal(str(row['amount'])) * (1 if row['is_debit'] else -1)
                    self.assertEqual(running, Decimal(str(row['running_balance'])))
                self.assertEqual(running, Decimal(str(monthly['header']['closing_balance'])))
                payments = [r for r in monthly['transactions'] if r['type'] == 'payment']
                self.assertEqual(len(payments), 1)
                self.assertEqual(payments[0]['source_table'], 'income_transactions')
            balance = Service.calculate_house_balance(db, hid)
            self.assertEqual(balance['total_paid'], Decimal('300.15'))  # Allocated money only.
            self.assertEqual(balance['total_credited'], Decimal('5099.99'))
            self.assertEqual(balance['outstanding_balance'], Decimal('15200.01'))
            summary = Service.get_house_financial_summary(db, hid)
            self.assertEqual(summary['balance'], balance)
            self.assertEqual(len(summary['recent_payments']), 2)
            self.assertEqual(len(summary['credit_notes']), 2)
            first = next(i for i in summary['recent_invoices'] if i['id'] == self.inv_id)
            self.assertEqual(first['status'], 'PARTIALLY_PAID')

    def test_invalid_ranges_missing_house_and_query_errors_never_become_zero_reports(self):
        with self.Session() as db:
            hid = db.get(Invoice, self.inv_id).house_id
            for year, month in [(2026, 0), (2026, 13), (1999, 1)]:
                with self.assertRaises(ValueError):
                    Service.generate_house_statement(db, hid, year, month)
            with self.assertRaises(ValueError):
                Service.generate_statement(db, hid, date(2026, 6, 2), date(2026, 6, 1))
            with self.assertRaises(ValueError):
                Service.calculate_house_balance(db, -1)
            with self.assertRaises(ValueError):
                Service.generate_statement(db, -1, date(2026, 1, 1), date(2026, 1, 31))
        failed_db = Mock()
        failed_db.get.side_effect = RuntimeError('database unavailable')
        with self.assertRaisesRegex(RuntimeError, 'database unavailable'):
            Service.generate_statement(failed_db, hid, date(2026, 1, 1), date(2026, 1, 31))

    def test_http_reports_enforce_existing_house_guard_and_preserve_forbidden(self):
        with self.Session() as db:
            hid = self.seed_cash(db)
            user = db.get(User, self.user_id)
            user.role = 'resident'
            db.add(ResidentMembership(house_id=hid, user_id=user.id))
            db.commit()
            app = FastAPI(); app.include_router(accounting.router)
            app.dependency_overrides[get_db] = lambda: db
            app.dependency_overrides[get_current_user] = lambda: user
            app.dependency_overrides[get_house_id_from_token] = lambda: hid
            paths = [f'/balance/house/{hid}', f'/financial-summary/house/{hid}',
                f'/snapshot/house/{hid}?year=2026&month=5', f'/snapshot/{hid}?year=2026&month=5',
                f'/statement/house/{hid}?year=2026&month=5',
                f'/statement/{hid}?start_date=2026-05-11&end_date=2026-05-11']
            with TestClient(app) as client:
                for path in paths:
                    response = client.get('/accounting' + path)
                    self.assertEqual(response.status_code, 200, (path, response.text))
                summary = client.get('/accounting' + paths[1]).json()['financial_summary']
                self.assertEqual(summary['credit_notes']['total_amount'], 5099.99)
                # Same authenticated resident cannot request another house.
                other = House(house_code='OTHER-ACCESS', owner_name='Other')
                db.add(other); db.commit()
                for path in paths:
                    response = client.get('/accounting' + path.replace(str(hid), str(other.id), 1))
                    self.assertEqual(response.status_code, 403, (path, response.text))
                house = db.get(House, hid); house.house_status = HouseStatus.SUSPENDED; db.commit()
                for path in paths:
                    self.assertEqual(client.get('/accounting' + path).status_code, 403)
                user.role = 'super_admin'; db.commit()
                for path in paths:
                    self.assertEqual(client.get('/accounting' + path).status_code, 200)

    @patch('app.core.auth.SECRET_KEY', 'local-report-test-only-signing-key-never-production')
    def test_real_signed_session_select_switch_revoke_and_membership(self):
        from app.api.auth import router as auth_router
        with self.Session() as db:
            hid = self.seed_cash(db)
            user = db.get(User, self.user_id); user.role = 'resident'
            other = House(house_code='SWITCH-HOUSE', owner_name='Second house')
            db.add(other); db.flush()
            membership = ResidentMembership(house_id=hid, user_id=user.id)
            db.add_all([membership, ResidentMembership(house_id=other.id, user_id=user.id)])
            db.commit()
            app = FastAPI(); app.include_router(accounting.router); app.include_router(auth_router)
            app.dependency_overrides[get_db] = lambda: db  # Real auth dependencies execute.
            with TestClient(app, base_url='https://testserver') as client:
                url = f'/accounting/statement/house/{hid}?year=2026&month=5'
                self.assertEqual(client.get(url).status_code, 401)
                token = auth.create_access_token({'sub':str(user.id), 'role':'resident',
                    'session_version':user.session_version})
                client.cookies.set('access_token', token, domain='testserver.local', path='/')
                self.assertEqual(client.get(url).status_code, 403)  # No selected house.
                response = client.post('/api/auth/select-house', json={'house_id':hid})
                self.assertEqual(response.status_code, 200, response.text)
                selected_token = client.cookies.get('access_token')
                response = client.get(url)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()['statement']['snapshot']['payment_total'], 1000.30)
                # Even membership of both houses does not bypass the selected context.
                other_url = f'/accounting/statement/house/{other.id}?year=2026&month=5'
                self.assertEqual(client.get(other_url).status_code, 403)
                self.assertEqual(client.post('/api/auth/select-house',json={'house_id':other.id}).status_code,200)
                self.assertEqual(client.get(other_url).status_code, 200)
                self.assertEqual(client.get(url).status_code, 403)
                client.cookies.set('access_token', selected_token, domain='testserver.local', path='/')
                membership.status = ResidentMembershipStatus.INACTIVE; db.commit()
                self.assertEqual(client.get(url).status_code, 403)  # Existing token immediately loses access.
                membership.status = ResidentMembershipStatus.ACTIVE; db.commit()
                self.assertEqual(client.get(url).status_code, 200)
                user.session_version += 1; db.commit()
                self.assertEqual(client.get(url).status_code, 401)
                expired = auth.create_access_token({'sub':str(user.id), 'role':'resident','house_id':hid,
                    'session_version':user.session_version}, expires_delta=timedelta(seconds=-1))
                client.cookies.set('access_token', expired, domain='testserver.local', path='/')
                self.assertEqual(client.get(url).status_code, 401)

    @patch('app.core.auth.SECRET_KEY', 'local-report-test-only-signing-key-never-production')
    def test_production_app_mounts_report_urls_and_preserves_legacy(self):
        from app.main import app
        with self.Session() as db:
            hid = self.seed_cash(db)
            user = db.get(User, self.user_id)
            previous = app.dependency_overrides.copy()
            app.dependency_overrides[get_db] = lambda: db
            try:
                with TestClient(app, base_url='https://testserver') as client:
                    paths = [f'/balance/house/{hid}', f'/financial-summary/house/{hid}',
                        f'/snapshot/house/{hid}?year=2026&month=5', f'/snapshot/{hid}?year=2026&month=5',
                        f'/statement/house/{hid}?year=2026&month=5',
                        f'/statement/{hid}?start_date=2026-05-01&end_date=2026-05-31']
                    self.assertEqual(client.get('/health').status_code,200)
                    self.assertEqual(client.get('/api/accounting'+paths[0]).status_code,401)
                    client.cookies.set('access_token',auth.create_access_token({'sub':str(user.id),
                        'role':user.role,'session_version':user.session_version}))
                    for path in paths:
                        canonical=client.get('/api/accounting'+path)
                        legacy=client.get('/accounting'+path)
                        self.assertEqual(canonical.status_code,200,(path,canonical.text))
                        self.assertEqual(legacy.status_code,200,(path,legacy.text))
                        a,b=canonical.json(),legacy.json()
                        a.pop('meta',None);b.pop('meta',None)
                        self.assertEqual(a,b)
                    for fmt in ('pdf','xlsx'):
                        response=client.get('/api/accounting'+paths[4]+'&format='+fmt)
                        self.assertEqual(response.status_code,200)
                    self.assertEqual(client.post('/api/accounting/payments/apply',json={}).status_code,404)
            finally:
                app.dependency_overrides.clear();app.dependency_overrides.update(previous)

    @patch('app.core.auth.SECRET_KEY', 'local-report-test-only-signing-key-never-production')
    def test_signed_cookie_downloads_match_json_and_admin(self):
        from openpyxl import load_workbook
        from reportlab.pdfbase import pdfmetrics
        with self.Session() as db:
            hid = self.seed_cash(db)
            user = db.get(User, self.user_id); user.role = 'resident'
            db.add(ResidentMembership(house_id=hid,user_id=user.id)); db.commit()
            app = FastAPI(); app.include_router(accounting.router)
            app.dependency_overrides[get_db] = lambda: db
            with TestClient(app, base_url='https://testserver') as client:
                def login():
                    client.cookies.set('access_token', auth.create_access_token({'sub':str(user.id),
                        'role':user.role,'house_id':hid,'session_version':user.session_version}))
                login()
                url = f'/accounting/statement/house/{hid}?year=2026&month=5'
                resident = client.get(url).json()['statement']
                xlsx = client.get(url+'&format=xlsx')
                self.assertEqual(xlsx.status_code,200,xlsx.text[:100] if xlsx.status_code!=200 else '')
                workbook = load_workbook(BytesIO(xlsx.content), data_only=True)
                self.assertEqual(workbook['Statement']['A2'].value, 'หมู่บ้านแมกไม้ลีลาวดี')
                raw = list(workbook['RawData'].values)
                payments = [r for r in raw[1:] if r[1]=='Payment']
                self.assertEqual(len(payments),1)
                self.assertEqual(payments[0][3],1000.30)
                self.assertEqual(raw[-1][4],resident['snapshot']['closing_balance'])
                pdf = client.get(url+'&format=pdf')
                self.assertEqual(pdf.status_code,200)
                self.assertTrue(pdf.content.startswith(b'%PDF-'))
                self.assertIn('StatementSarabun',pdfmetrics.getRegisteredFontNames())
                self.assertIn(f'statement_house{hid}_2026_05.pdf',pdf.headers['content-disposition'])
                self.assertEqual(client.get(url+'&format=bad').status_code,400)
                user.role = 'super_admin'; db.commit(); login()
                admin = client.get(url).json()['statement']
                self.assertEqual(admin,resident)


if __name__ == '__main__':
    unittest.main()
