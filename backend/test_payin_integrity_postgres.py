"""Local PostgreSQL only: endpoint regressions and real blocking races.

Uses the existing harness: explicit localhost moobaan_credit_test URL required,
random isolated schema per run. Never connects to the application's DB URL.
"""
import asyncio
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Event
from unittest.mock import patch
from types import SimpleNamespace

from fastapi import HTTPException, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

import test_automatic_allocation_postgres as fixtures
from app.db.models import PayinReport, PayinStatus, BankTransaction, PostingStatus, User, IncomeTransaction
from app.db.models.income_transaction import LedgerStatus
from app.models import PayInReportUpdate, RejectPayInRequest
from app.api import payins, payin_state, bank_reconciliation as reconciliation
from app.db.session import get_db
from app.core.deps import require_admin_or_accounting, require_user, get_house_id_from_token
from app.services.payin_integrity import lock_payin_evidence, apply_evidence_edit


class PayinIntegrityTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.AutomaticAllocationTests.setUpClass.__func__)
    cleanup_schema = classmethod(fixtures.AutomaticAllocationTests.cleanup_schema.__func__)
    receipt = fixtures.AutomaticAllocationTests.receipt
    invoice = fixtures.AutomaticAllocationTests.invoice

    def setUp(self):
        fixtures.AutomaticAllocationTests.setUp(self)
        _, bank, self.payin_id = self.receipt(posted=False)
        import uuid
        self.bank_id = uuid.UUID(bank)
        self.inv_id = self.invoice()
        with self.Session() as db:
            p = db.get(PayinReport, self.payin_id)
            p.slip_url = 'test/original.png'
            p.status = PayinStatus.PENDING
            db.commit()

    def invoke(self, operation, db=None):
        if db is None:
            with self.Session() as session:
                return self.invoke(operation, session)
        return operation(db)

    def edit(self, db, **fields):
        return asyncio.run(payins.update_payin_report(None, self.payin_id,
            PayInReportUpdate(**fields), db=db, current_user=db.get(User, self.user_id),
            token_house_id=None))

    def accept(self, db):
        return asyncio.run(payins.accept_payin_report(self.payin_id,
            db=db, current_user=db.get(User, self.user_id)))

    def post(self, db):
        return asyncio.run(reconciliation.confirm_and_post(str(self.bank_id), data=None,
            db=db, current_user=db.get(User, self.user_id)))

    def reject(self, db, state=False):
        fn = payin_state.reject_payin_needs_fix if state else payins.reject_payin_report
        request = payin_state.RejectPayinRequest(reason='wrong slip') if state else RejectPayInRequest(reason='wrong slip')
        return asyncio.run(fn(self.payin_id, request, db=db, current_user=db.get(User, self.user_id)))

    def match(self, db):
        return asyncio.run(reconciliation.match_transaction_with_payin(str(self.bank_id),
            reconciliation.MatchRequest(payin_id=self.payin_id), db=db, current_user=db.get(User, self.user_id)))

    def unmatch(self, db):
        return asyncio.run(reconciliation.unmatch_transaction(str(self.bank_id),
            db=db, current_user=db.get(User, self.user_id)))

    def accounting_accept(self, db):
        from app.api.accounting import accept_payin, PayinAccept
        return asyncio.run(accept_payin(PayinAccept(payin_id=self.payin_id),
            db=db,current_user=db.get(User,self.user_id)))

    def state(self):
        with self.Session() as db:
            p, b = db.get(PayinReport, self.payin_id), db.get(BankTransaction, self.bank_id)
            ledgers = db.query(IncomeTransaction).filter_by(payin_id=p.id).all()
            return (p.status, p.matched_statement_txn_id, b.matched_payin_id,
                    b.posting_status, [(l.amount, l.received_at) for l in ledgers])

    def assert_released(self):
        status, link, back, posting, ledgers = self.state()
        self.assertIsNone(link); self.assertIsNone(back)
        self.assertEqual(posting, PostingStatus.UNMATCHED)
        self.assertEqual(ledgers, [])

    def test_amount_edit_unmatches(self):
        self.invoke(lambda db: self.edit(db, amount=999))
        self.assert_released()
        with self.assertRaises(HTTPException): self.invoke(self.accept)
        self.assert_released()

    def test_date_edit_unmatches(self):
        self.invoke(lambda db: self.edit(db, transfer_date='2026-05-12'))
        self.assert_released()

    def test_hour_only_updates_canonical_timestamp_and_unmatches(self):
        self.invoke(lambda db: self.edit(db, transfer_hour=8))
        self.assert_released()
        with self.Session() as db:
            self.assertEqual(db.get(PayinReport, self.payin_id).transfer_date.hour, 1)

    def test_minute_only_unmatches(self):
        self.invoke(lambda db: self.edit(db, transfer_minute=6))
        self.assert_released()

    def test_slip_edit_unmatches(self):
        self.invoke(lambda db: self.edit(db, slip_image_url='test/new.png'))
        self.assert_released()

    def test_equal_values_and_equivalent_timezone_keep_match(self):
        self.invoke(lambda db: self.edit(db, amount=600, transfer_date='2026-05-11T07:05:00+07:00',
            transfer_hour=7, transfer_minute=5, slip_image_url='test/original.png'))
        self.assertEqual(self.state()[1], self.bank_id)
        self.invoke(lambda db: self.edit(db, transfer_date='2026-05-11T00:05:00Z'))
        self.assertEqual(self.state()[1], self.bank_id)

    def test_date_only_equal_does_not_lose_time(self):
        self.invoke(lambda db: self.edit(db, transfer_date='2026-05-11'))
        self.assertEqual(self.state()[1], self.bank_id)

    def test_reject_both_paths_release(self):
        for state in (False, True):
            with self.subTest(state=state):
                with self.Session() as db:
                    p, b = db.get(PayinReport, self.payin_id), db.get(BankTransaction, self.bank_id)
                    p.status=PayinStatus.PENDING; p.matched_statement_txn_id=b.id
                    b.matched_payin_id=p.id; b.posting_status=PostingStatus.MATCHED; db.commit()
                self.invoke(lambda db: self.reject(db, state))
                self.assert_released()
                self.assertEqual(self.state()[0], PayinStatus.REJECTED_NEEDS_FIX)

    def test_drift_rejected_by_both_posting_paths_without_changes(self):
        for field in ('amount', 'time'):
            for operation in (self.accept, self.post, self.accounting_accept):
                with self.subTest(field=field, path=operation.__name__):
                    with self.Session() as db:
                        p=db.get(PayinReport,self.payin_id); b=db.get(BankTransaction,self.bank_id)
                        p.amount=Decimal('999') if field=='amount' else b.credit
                        p.transfer_date=b.effective_at + timedelta(seconds=61) if field=='time' else b.effective_at
                        db.commit()
                    before=self.state()
                    with self.assertRaises(HTTPException) as ctx: self.invoke(operation)
                    self.assertEqual(ctx.exception.status_code,400)
                    self.assertEqual(ctx.exception.detail['code'],'EVIDENCE_CHANGED')
                    self.assertEqual(self.state(),before)

    def test_receipt_amount_comes_from_bank_with_existing_one_cent_tolerance(self):
        with self.Session() as db:
            db.get(PayinReport,self.payin_id).amount=Decimal('600.01');db.commit()
        self.invoke(self.accept)
        self.assertEqual(self.state()[4][0][0],Decimal('600'))
        with self.Session() as db:
            from app.db.models import Invoice
            self.assertEqual(db.get(Invoice,self.inv_id).get_total_paid_decimal(),Decimal('600'))

    def test_post_normal_and_idempotent(self):
        self.invoke(self.post)
        self.assertEqual(self.invoke(self.post)['status'],'already_posted')
        self.assertEqual(len(self.state()[4]),1)

    def test_accounting_path_uses_statement_amount(self):
        with self.Session() as db:
            db.get(PayinReport,self.payin_id).amount=Decimal('600.01');db.commit()
        self.invoke(self.accounting_accept)
        self.assertEqual(self.state()[4][0][0],Decimal('600'))

    def test_failed_edit_commit_preserves_original_evidence_and_match(self):
        before=self.state()
        with self.Session() as db, patch.object(db,'commit',side_effect=RuntimeError('local injected failure')):
            with self.assertRaises(RuntimeError):self.edit(db,amount=999)
            db.rollback()
        self.assertEqual(self.state(),before)
        with self.Session() as db:self.assertEqual(db.get(PayinReport,self.payin_id).amount,Decimal('600'))

    def test_statement_original_fields_survive_edit_reject_and_post(self):
        def original():
            with self.Session() as db:
                bank=db.get(BankTransaction,self.bank_id)
                return (bank.credit,bank.debit,bank.effective_at,bank.description,bank.raw_row,bank.fingerprint)
        before=original()
        self.invoke(lambda db:self.edit(db,amount=999))
        self.assertEqual(original(),before)
        self.invoke(lambda db:self.edit(db,amount=600))
        self.invoke(self.match);self.invoke(self.reject)
        self.assertEqual(original(),before)
        self.invoke(lambda db:self.edit(db,amount=600))
        self.invoke(self.match);self.invoke(self.post)
        self.assertEqual(original(),before)

    def test_admin_create_then_attach_requires_new_match(self):
        self.invoke(self.unmatch)
        with self.Session() as db:
            result=asyncio.run(payin_state.admin_create_payin_from_bank(
                payin_state.AdminCreateFromBankRequest(bank_transaction_id=str(self.bank_id),house_id=self.house_id),
                db=db,current_user=db.get(User,self.user_id)))
            new_id=result['payin']['id']
        with self.Session() as db, patch.object(payin_state,'save_slip_file',return_value='test/admin.png'):
            asyncio.run(payin_state.attach_slip_to_payin(new_id,slip=object(),db=db,
                current_user=db.get(User,self.user_id)))
        with self.Session() as db:
            self.assertIsNone(db.get(PayinReport,new_id).matched_statement_txn_id)
            self.assertEqual(db.get(BankTransaction,self.bank_id).posting_status,PostingStatus.UNMATCHED)

    def test_delete_paths_release_pending_but_block_posted(self):
        self.invoke(lambda db: asyncio.run(payins.delete_submission(self.payin_id,
            RejectPayInRequest(reason='duplicate local test'),db=db,current_user=db.get(User,self.user_id))))
        with self.Session() as db:
            self.assertIsNone(db.get(PayinReport,self.payin_id))
            self.assertIsNone(db.get(BankTransaction,self.bank_id).matched_payin_id)
            self.assertEqual(db.get(BankTransaction,self.bank_id).posting_status,PostingStatus.UNMATCHED)
        _,bank,self.payin_id=self.receipt(posted=False,day=12)
        import uuid
        self.bank_id=uuid.UUID(bank)
        self.invoke(self.post)
        with self.assertRaises(HTTPException):
            self.invoke(lambda db:asyncio.run(payins.delete_payin_report(None,self.payin_id,
                db=db,current_user=db.get(User,self.user_id),token_house_id=None)))
        self.assertEqual(self.state()[0],PayinStatus.ACCEPTED)

    def test_rejected_payin_cannot_use_confirm_post(self):
        # Simulate a legacy rejected row whose old match was never released.
        with self.Session() as db:
            db.get(PayinReport,self.payin_id).status=PayinStatus.REJECTED_NEEDS_FIX;db.commit()
        before=self.state()
        with self.assertRaises(HTTPException):self.invoke(self.post)
        self.assertEqual(self.state(),before)

    def test_inconsistent_links_do_not_clear_other_payin(self):
        with self.Session() as db:
            db.get(BankTransaction,self.bank_id).matched_payin_id=None;db.commit()
        before=self.state()
        with self.assertRaises(HTTPException) as ctx:self.invoke(self.reject)
        self.assertEqual(ctx.exception.status_code,409)
        self.assertEqual(self.state(),before)

    def test_accepted_edit_reject_unmatch_are_blocked(self):
        self.invoke(self.accept); before=self.state()
        for op in (lambda db:self.edit(db,amount=999),self.reject,
                   lambda db:self.reject(db,True),self.unmatch):
            with self.subTest(op=op):
                with self.assertRaises(HTTPException):self.invoke(op)
                self.assertEqual(self.state(),before)

    def test_reversed_bank_is_not_released_or_reposted(self):
        with self.Session() as db:
            db.get(BankTransaction,self.bank_id).posting_status=PostingStatus.REVERSED;db.commit()
        before=self.state()
        for op in (self.unmatch,self.accept,self.post,self.reject):
            with self.subTest(op=op.__name__):
                with self.assertRaises(HTTPException):self.invoke(op)
                self.assertEqual(self.state(),before)

    def test_hidden_active_ledger_prevents_release(self):
        with self.Session() as db:
            p=db.get(PayinReport,self.payin_id)
            db.add(IncomeTransaction(house_id=self.house_id,payin_id=p.id,amount=p.amount,
                received_at=p.transfer_date,reference_bank_transaction_id=self.bank_id,status=LedgerStatus.POSTED))
            db.commit()
        before=self.state()
        with self.assertRaises(HTTPException):self.invoke(self.unmatch)
        self.assertEqual(self.state(),before)

    def test_unconfirmed_statement_cannot_post(self):
        with self.Session() as db:
            db.get(BankTransaction,self.bank_id).batch.status='PARSED';db.commit()
        for op in (self.accept,self.post):
            with self.assertRaises(HTTPException):self.invoke(op)
        self.assertEqual(self.state()[4],[])

    def test_save_draft_and_attach_slip_release(self):
        with self.Session() as db, patch.object(payin_state,'get_house_id_from_token',return_value=self.house_id):
            asyncio.run(payin_state.save_payin_draft(self.payin_id, request=None, amount=None,
                transfer_date=None, transfer_hour=None, transfer_minute=6, slip=None,
                db=db,current_user=db.get(User,self.user_id),credentials=None))
        self.assert_released()
        self.invoke(lambda db:self.edit(db,transfer_minute=5))
        self.invoke(self.match)
        with self.Session() as db, patch.object(payin_state,'save_slip_file',return_value='test/upload.png'):
            asyncio.run(payin_state.attach_slip_to_payin(self.payin_id,slip=object(),db=db,
                current_user=db.get(User,self.user_id)))
        self.assert_released()

    def test_other_house_resident_cannot_edit_or_see_statement(self):
        resident=SimpleNamespace(id=self.user_id,role='resident')
        with self.Session() as db:
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(payins.update_payin_report(None,self.payin_id,PayInReportUpdate(amount=999),
                    db=db,current_user=resident,token_house_id=self.house_id+1))
            self.assertEqual(ctx.exception.status_code,403)
        with self.Session() as db:
            own=asyncio.run(payins.get_payin_report(None,self.payin_id,db=db,
                current_user=resident,token_house_id=self.house_id))
            self.assertIsNone(own['matched_statement'])
        with self.Session() as db:
            admin=asyncio.run(payins.get_payin_report(None,self.payin_id,db=db,
                current_user=db.get(User,self.user_id),token_house_id=None))
            self.assertEqual(admin['matched_statement']['credit'],600)

    def test_invalid_edit_rolls_back_without_unmatching(self):
        for fields in ({'amount':float('nan')},{'amount':-1},{'amount':600.001},{'transfer_hour':25}):
            before=self.state()
            with self.assertRaises(HTTPException):self.invoke(lambda db:self.edit(db,**fields))
            self.assertEqual(self.state(),before)

    def race(self, first, second):
        ready, finish, second_started=Event(),Event(),Event()
        second_pid=[]
        def worker(op, hold=False):
            with self.Session() as db:
                if hold:
                    commit=db.commit
                    def held_commit():
                        db.flush();ready.set()
                        if not finish.wait(8):raise RuntimeError('race release timed out')
                        commit()
                    db.commit=held_commit
                else:
                    second_pid.append(db.execute(text('select pg_backend_pid()')).scalar())
                    second_started.set()
                try:op(db);return 'ok'
                except HTTPException as exc:db.rollback();return exc.status_code
        with ThreadPoolExecutor(2) as pool:
            one=pool.submit(worker,first,True)
            try:
                self.assertTrue(ready.wait(5),'first operation failed before commit')
                two=pool.submit(worker,second)
                self.assertTrue(second_started.wait(2))
                blocked=False
                with self.engine.connect() as conn:
                    deadline=time.monotonic()+4
                    while time.monotonic()<deadline:
                        blocked=conn.execute(text('select cardinality(pg_blocking_pids(:pid)) > 0'),
                            {'pid':second_pid[0]}).scalar()
                        if blocked:break
                        time.sleep(.02)
                self.assertTrue(blocked,'second real transaction must block, not merely run later')
            finally:finish.set()
            return one.result(timeout=5),two.result(timeout=5)

    def test_race_edit_then_accept(self):
        self.assertEqual(self.race(lambda db:self.edit(db,amount=999),self.accept),('ok',409))
        self.assert_released()

    def test_race_accept_then_edit(self):
        self.assertEqual(self.race(self.accept,lambda db:self.edit(db,amount=999)),('ok',400))
        self.assertEqual(self.state()[4][0][0],Decimal('600'))

    def test_race_reject_then_post(self):
        self.assertEqual(self.race(self.reject,self.post),('ok',409))
        self.assert_released()

    def test_race_post_then_reject(self):
        self.assertEqual(self.race(self.post,self.reject),('ok',400))
        self.assertEqual(self.state()[0],PayinStatus.ACCEPTED)

    def test_race_accept_then_post_exactly_one_ledger(self):
        self.assertEqual(self.race(self.accept,self.post),('ok','ok'))
        self.assertEqual(len(self.state()[4]),1)

    def test_race_post_then_accept_exactly_one_ledger(self):
        self.assertEqual(self.race(self.post,self.accept),('ok',400))
        self.assertEqual(len(self.state()[4]),1)

    def test_race_match_then_edit_detects_changed_link(self):
        self.invoke(self.unmatch)
        self.assertEqual(self.race(self.match,lambda db:self.edit(db,amount=999)),('ok',409))
        with self.Session() as db:self.assertEqual(db.get(PayinReport,self.payin_id).amount,Decimal('600'))

    def test_race_unmatched_edit_then_match(self):
        self.invoke(self.unmatch)
        self.assertEqual(self.race(lambda db:self.edit(db,amount=999),self.match),('ok',400))
        self.assert_released()

    def test_race_post_then_unmatch(self):
        self.assertEqual(self.race(self.post,self.unmatch),('ok',400))
        self.assertEqual(self.state()[3],PostingStatus.POSTED)

    def test_race_accounting_accept_then_edit(self):
        self.assertEqual(self.race(self.accounting_accept,lambda db:self.edit(db,amount=999)),('ok',400))
        self.assertEqual(self.state()[4][0][0],Decimal('600'))

    def test_race_edit_then_accounting_accept(self):
        self.assertEqual(self.race(lambda db:self.edit(db,amount=999),self.accounting_accept),('ok',409))
        self.assert_released()

    def test_race_accounting_accept_then_post(self):
        self.assertEqual(self.race(self.accounting_accept,self.post),('ok','ok'))
        self.assertEqual(len(self.state()[4]),1)

    def test_stale_review_blocks_match_after_slip_changed_before_match(self):
        from app.services.payin_integrity import evidence_revision
        self.invoke(self.unmatch)
        with self.Session() as db:revision=evidence_revision(db.get(PayinReport,self.payin_id))
        self.invoke(lambda db:self.edit(db,slip_image_url='test/replaced.png'))
        with self.Session() as db:
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(reconciliation.match_transaction_with_payin(str(self.bank_id),
                    reconciliation.MatchRequest(payin_id=self.payin_id,evidence_revision=revision),
                    db=db,current_user=db.get(User,self.user_id)))
            self.assertEqual(ctx.exception.status_code,409)
        self.assert_released()

    def test_stale_review_blocks_post_after_unmatch_and_rematch(self):
        from app.services.payin_integrity import evidence_revision
        with self.Session() as db:revision=evidence_revision(db.get(PayinReport,self.payin_id))
        self.invoke(lambda db:self.edit(db,slip_image_url='test/replaced.png'))
        self.invoke(self.match)
        with self.Session() as db:
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(reconciliation.confirm_and_post(str(self.bank_id),
                    reconciliation.ConfirmPostRequest(evidence_revision=revision),
                    db=db,current_user=db.get(User,self.user_id)))
            self.assertEqual(ctx.exception.status_code,409)
        self.assertEqual(self.state()[4],[])
        with self.Session() as db:
            fresh=evidence_revision(db.get(PayinReport,self.payin_id))
            asyncio.run(reconciliation.confirm_and_post(str(self.bank_id),
                reconciliation.ConfirmPostRequest(evidence_revision=fresh),
                db=db,current_user=db.get(User,self.user_id)))
        self.assertEqual(len(self.state()[4]),1)

    def test_http_drift_400_and_admin_evidence_response(self):
        app=FastAPI();app.include_router(payins.router)
        def session():
            with self.Session() as db:yield db
        app.dependency_overrides[get_db]=session
        actor=SimpleNamespace(id=self.user_id,role='super_admin')
        app.dependency_overrides[require_admin_or_accounting]=lambda:actor
        app.dependency_overrides[require_user]=lambda:actor
        app.dependency_overrides[get_house_id_from_token]=lambda:None
        with self.Session() as db:
            db.get(PayinReport,self.payin_id).amount=Decimal('999');db.commit()
        with TestClient(app) as client:
            result=client.post(f'/api/payin-reports/{self.payin_id}/accept')
            self.assertEqual(result.status_code,400)
            self.assertEqual(result.json()['detail']['code'],'EVIDENCE_CHANGED')
            result=client.get(f'/api/payin-reports/{self.payin_id}')
            self.assertEqual(result.json()['matched_statement']['credit'],600)
        self.assertEqual(self.state()[4],[])


if __name__ == '__main__':unittest.main()
