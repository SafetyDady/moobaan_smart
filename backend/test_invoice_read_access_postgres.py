"""HTTP access checks for the active invoice UI routes on isolated PostgreSQL."""
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import invoices
from app.core.auth import create_access_token
from app.core.deps import get_db
from app.db.models import Invoice, User, HouseMember
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus
import test_credit_settlement_postgres as fixtures


class InvoiceReadAccessTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.SettlementPostgresTests.setUpClass.__func__)
    cleanup_schema = classmethod(fixtures.SettlementPostgresTests.cleanup_schema.__func__)
    setUp = fixtures.SettlementPostgresTests.setUp

    def routes(self):
        return ['/api/invoices', '/api/invoices/allocatable-ledgers',
                f'/api/invoices/{self.inv_id}', f'/api/invoices/{self.inv_id}/detail',
                f'/api/invoices/{self.inv_id}/payments']

    def client(self, db):
        app = FastAPI(); app.include_router(invoices.router)
        app.dependency_overrides[get_db] = lambda: db
        return TestClient(app)

    def token(self, user, house):
        return {'Authorization': 'Bearer ' + create_access_token(dict(
            sub=str(user.id), role=user.role, house_id=house, session_version=user.session_version))}

    def resident(self, db):
        user = db.get(User, self.user_id); user.role = 'resident'
        hid = db.get(Invoice, self.inv_id).house_id
        membership = ResidentMembership(user_id=user.id, house_id=hid)
        db.add_all([membership, HouseMember(user_id=user.id, house_id=hid)])
        db.commit()
        return user, hid, membership

    def test_anonymous_denied_on_all_five_invoice_reads(self):
        with self.Session() as db, self.client(db) as client:
            for path in self.routes():
                with self.subTest(path=path): self.assertEqual(client.get(path).status_code, 401)

    def test_admin_and_accounting_retain_all_house_access(self):
        with self.Session() as db, self.client(db) as client:
            user = db.get(User, self.user_id)
            for role in ('super_admin', 'accounting'):
                user.role = role; db.commit()
                for path in self.routes():
                    with self.subTest(role=role,path=path):
                        self.assertEqual(client.get(path, headers=self.token(user,None)).status_code, 200)

    def test_resident_own_house_and_omitted_filter_are_scoped(self):
        with self.Session() as db, self.client(db) as client:
            user,hid,_ = self.resident(db); headers = self.token(user,hid)
            for path in [self.routes()[0], *self.routes()[2:]]:
                r=client.get(path,headers=headers)
                self.assertEqual(r.status_code,200)
                if path == '/api/invoices':
                    self.assertTrue(r.json()); self.assertEqual({i['house_id'] for i in r.json()},{hid})
            self.assertEqual(client.get(f'/api/invoices?house_id={hid}',headers=headers).status_code,200)
            self.assertEqual(client.get('/api/invoices/allocatable-ledgers',headers=headers).status_code,403)

    def test_resident_selected_house_mismatch_and_missing_context_denied(self):
        with self.Session() as db, self.client(db) as client:
            user,hid,_ = self.resident(db)
            for house in (None,hid+1000):
                for path in [self.routes()[0]+f'?house_id={hid}',*self.routes()[2:]]:
                    with self.subTest(house=house,path=path):
                        self.assertEqual(client.get(path,headers=self.token(user,house)).status_code,403)
            self.assertEqual(client.get('/api/invoices',headers=self.token(user,None)).status_code,403)
            self.assertEqual(client.get(f'/api/invoices?house_id={hid+1000}',headers=self.token(user,hid)).status_code,403)

    def test_inactive_membership_denied_even_with_legacy_membership_and_token(self):
        with self.Session() as db, self.client(db) as client:
            user,hid,membership = self.resident(db); headers = self.token(user,hid)
            membership.status = ResidentMembershipStatus.INACTIVE; db.commit()
            for path in [self.routes()[0], *self.routes()[2:]]:
                with self.subTest(path=path):self.assertEqual(client.get(path,headers=headers).status_code,403)


if __name__ == '__main__': unittest.main(verbosity=2)
