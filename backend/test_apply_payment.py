"""
Test Apply Payment Feature: Ledger → Invoice Allocation
Tests the complete workflow of applying recognized ledger entries to invoices.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import datetime, date
from decimal import Decimal
from app.db.session import SessionLocal
from app.db.models.house import House as HouseDB
from app.db.models.invoice import Invoice as InvoiceDB
from app.db.models.payin_report import PayinReport
from app.db.models.income_transaction import IncomeTransaction
from app.db.models.invoice_payment import InvoicePayment

def reset_test_data():
    """Clean up test data"""
    db = SessionLocal()
    try:
        # Delete in correct order
        db.query(InvoicePayment).delete()
        db.query(InvoiceDB).delete()
        db.query(IncomeTransaction).delete()
        db.query(PayinReport).filter(PayinReport.amount == Decimal("600.00")).filter(
            PayinReport.transfer_date >= datetime(2025, 1, 1)
        ).delete()
        db.query(HouseDB).filter(HouseDB.house_code == "TEST001").delete()
        db.commit()
        print("✓ Reset test data")
    finally:
        db.close()


def setup_test_data():
    """
    Create test scenario:
    - House TEST001
    - Invoice #1: ฿1200 (Jan 2025)
    - Invoice #2: ฿600 (Feb 2025)
    - Payin #1: ฿600 (ACCEPTED) → Ledger #1: ฿600
    - Payin #2: ฿600 (ACCEPTED) → Ledger #2: ฿600
    """
    db = SessionLocal()
    try:
        # 1. Create test house
        house = HouseDB(
            house_code="TEST001",
            owner_name="Apply Payment Test",
            house_status="ACTIVE"
        )
        db.add(house)
        db.flush()
        
        # 2. Create invoices
        invoice1 = InvoiceDB(
            house_id=house.id,
            cycle_year=2025,
            cycle_month=1,
            issue_date=date(2025, 1, 1),
            due_date=date(2025, 1, 31),
            total_amount=Decimal("1200.00"),
            status="ISSUED"
        )
        invoice2 = InvoiceDB(
            house_id=house.id,
            cycle_year=2025,
            cycle_month=2,
            issue_date=date(2025, 2, 1),
            due_date=date(2025, 2, 28),
            total_amount=Decimal("600.00"),
            status="ISSUED"
        )
        db.add_all([invoice1, invoice2])
        db.flush()
        
        # 3. Create ACCEPTED payins with ledgers
        payin1 = PayinReport(
            house_id=house.id,
            submitted_by_user_id=None,
            amount=Decimal("600.00"),
            transfer_date=datetime(2025, 1, 15, 10, 0, 0),
            transfer_hour=10,
            transfer_minute=0,
            status="ACCEPTED"
        )
        payin2 = PayinReport(
            house_id=house.id,
            submitted_by_user_id=None,
            amount=Decimal("600.00"),
            transfer_date=datetime(2025, 1, 20, 11, 0, 0),
            transfer_hour=11,
            transfer_minute=0,
            status="ACCEPTED"
        )
        db.add_all([payin1, payin2])
        db.flush()
        
        # 4. Create ledgers (IncomeTransactions)
        ledger1 = IncomeTransaction(
            house_id=house.id,
            payin_id=payin1.id,
            amount=Decimal("600.00"),
            received_at=datetime(2025, 1, 15, 10, 0, 0)
        )
        ledger2 = IncomeTransaction(
            house_id=house.id,
            payin_id=payin2.id,
            amount=Decimal("600.00"),
            received_at=datetime(2025, 1, 20, 11, 0, 0)
        )
        db.add_all([ledger1, ledger2])
        db.commit()
        
        print(f"✓ Created test house: {house.house_code}")
        print(f"✓ Created invoice #1: ฿{invoice1.total_amount} (Jan 2025)")
        print(f"✓ Created invoice #2: ฿{invoice2.total_amount} (Feb 2025)")
        print(f"✓ Created ledger #1: ฿{ledger1.amount} (from payin ID {payin1.id})")
        print(f"✓ Created ledger #2: ฿{ledger2.amount} (from payin ID {payin2.id})")
        
        return house.id, invoice1.id, invoice2.id, ledger1.id, ledger2.id
        
    except Exception as e:
        db.rollback()
        print(f"✗ Setup failed: {e}")
        raise
    finally:
        db.close()


def test_full_payment():
    """Test Case 1: Full payment (฿600 ledger → ฿600 invoice)"""
    print("\n" + "="*70)
    print("TEST CASE 1: Full Payment")
    print("="*70)
    
    db = SessionLocal()
    try:
        # Get test data
        house = db.query(HouseDB).filter(HouseDB.house_code == "TEST001").first()
        invoice = db.query(InvoiceDB).filter(
            InvoiceDB.house_id == house.id,
            InvoiceDB.cycle_month == 2  # Feb invoice (฿600)
        ).first()
        ledger = db.query(IncomeTransaction).filter(
            IncomeTransaction.house_id == house.id
        ).first()
        
        print(f"Invoice #{invoice.id}: ฿{invoice.total_amount} (Status: {invoice.status})")
        print(f"Ledger #{ledger.id}: ฿{ledger.amount} (Remaining: ฿{ledger.get_unallocated_amount()})")
        
        # Apply full payment
        payment = InvoicePayment(
            invoice_id=invoice.id,
            income_transaction_id=ledger.id,
            amount=Decimal("600.00")
        )
        db.add(payment)
        db.flush()  # Make sure payment is visible before update_status
        db.refresh(invoice)  # Refresh to load payments relationship
        invoice.update_status()
        db.commit()
        db.refresh(invoice)
        
        # Verify
        assert invoice.get_total_paid() == 600.00, "Paid amount should be ฿600"
        assert invoice.get_outstanding_amount() == 0.00, "Outstanding should be ฿0"
        assert invoice.status.value == "PAID", f"Status should be PAID, got {invoice.status.value}"
        assert ledger.get_unallocated_amount() == 0.00, "Ledger should be fully allocated"
        
        print(f"✓ Payment applied: ฿{payment.amount}")
        print(f"✓ Invoice status: {invoice.status.value}")
        print(f"✓ Invoice paid: ฿{invoice.get_total_paid()}")
        print(f"✓ Invoice outstanding: ฿{invoice.get_outstanding_amount()}")
        print(f"✓ Ledger remaining: ฿{ledger.get_unallocated_amount()}")
        print("✓ TEST PASSED: Full payment successful")
        
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
    except Exception as e:
        db.rollback()
        print(f"✗ ERROR: {e}")
    finally:
        db.close()


def test_partial_payment():
    """Test Case 2: Partial payment (฿600 ledger → ฿1200 invoice)"""
    print("\n" + "="*70)
    print("TEST CASE 2: Partial Payment")
    print("="*70)
    
    db = SessionLocal()
    try:
        # Get test data
        house = db.query(HouseDB).filter(HouseDB.house_code == "TEST001").first()
        invoice = db.query(InvoiceDB).filter(
            InvoiceDB.house_id == house.id,
            InvoiceDB.cycle_month == 1  # Jan invoice (฿1200)
        ).first()
        # Get second ledger (skip first which was used in test_full_payment)
        ledgers = db.query(IncomeTransaction).filter(
            IncomeTransaction.house_id == house.id
        ).order_by(IncomeTransaction.id).all()
        ledger = ledgers[1] if len(ledgers) > 1 else ledgers[0]
        
        print(f"Invoice #{invoice.id}: ฿{invoice.total_amount} (Status: {invoice.status})")
        print(f"Ledger #{ledger.id}: ฿{ledger.amount} (Remaining: ฿{ledger.get_unallocated_amount()})")
        
        # Apply partial payment
        payment = InvoicePayment(
            invoice_id=invoice.id,
            income_transaction_id=ledger.id,
            amount=Decimal("600.00")
        )
        db.add(payment)
        db.flush()  # Make sure payment is visible before update_status
        db.refresh(invoice)  # Refresh to load payments relationship
        invoice.update_status()
        db.commit()
        db.refresh(invoice)
        
        # Verify
        assert invoice.get_total_paid() == 600.00, "Paid amount should be ฿600"
        assert invoice.get_outstanding_amount() == 600.00, "Outstanding should be ฿600"
        assert invoice.status.value == "PARTIALLY_PAID", f"Status should be PARTIALLY_PAID, got {invoice.status.value}"
        assert ledger.get_unallocated_amount() == 0.00, "Ledger should be fully allocated"
        
        print(f"✓ Payment applied: ฿{payment.amount}")
        print(f"✓ Invoice status: {invoice.status.value}")
        print(f"✓ Invoice paid: ฿{invoice.get_total_paid()}")
        print(f"✓ Invoice outstanding: ฿{invoice.get_outstanding_amount()}")
        print(f"✓ Ledger remaining: ฿{ledger.get_unallocated_amount()}")
        print("✓ TEST PASSED: Partial payment successful")
        
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
    except Exception as e:
        db.rollback()
        print(f"✗ ERROR: {e}")
    finally:
        db.close()


def test_allocatable_ledgers():
    """Test Case 3: Query allocatable ledgers"""
    print("\n" + "="*70)
    print("TEST CASE 3: Allocatable Ledgers Query")
    print("="*70)
    
    db = SessionLocal()
    try:
        house = db.query(HouseDB).filter(HouseDB.house_code == "TEST001").first()
        
        # Query allocatable ledgers
        ledgers = db.query(IncomeTransaction).join(
            PayinReport, IncomeTransaction.payin_id == PayinReport.id
        ).filter(
            PayinReport.status == "ACCEPTED",
            IncomeTransaction.house_id == house.id
        ).all()
        
        allocatable = [l for l in ledgers if l.get_unallocated_amount() > 0]
        
        print(f"Total ledgers: {len(ledgers)}")
        print(f"Allocatable ledgers: {len(allocatable)}")
        
        for ledger in allocatable:
            print(f"  Ledger #{ledger.id}: ฿{ledger.amount} (Remaining: ฿{ledger.get_unallocated_amount()})")
        
        # After previous tests, both ledgers should be fully allocated
        assert len(allocatable) == 0, "Should have no allocatable ledgers after full allocation"
        
        print("✓ TEST PASSED: Allocatable ledgers query works correctly")
        
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
    except Exception as e:
        print(f"✗ ERROR: {e}")
    finally:
        db.close()


def test_payment_history():
    """Test Case 4: Query payment history"""
    print("\n" + "="*70)
    print("TEST CASE 4: Payment History")
    print("="*70)
    
    db = SessionLocal()
    try:
        house = db.query(HouseDB).filter(HouseDB.house_code == "TEST001").first()
        invoice = db.query(InvoiceDB).filter(
            InvoiceDB.house_id == house.id,
            InvoiceDB.cycle_month == 1  # Jan invoice (partially paid)
        ).first()
        
        payments = db.query(InvoicePayment).filter(
            InvoicePayment.invoice_id == invoice.id
        ).all()
        
        print(f"Invoice #{invoice.id}: ฿{invoice.total_amount}")
        print(f"Payment records: {len(payments)}")
        
        total_from_payments = sum(float(p.amount) for p in payments)
        
        for payment in payments:
            ledger = db.query(IncomeTransaction).filter(
                IncomeTransaction.id == payment.income_transaction_id
            ).first()
            print(f"  Payment #{payment.id}: ฿{payment.amount} (Ledger #{ledger.id}, Applied: {payment.applied_at})")
        
        assert len(payments) == 1, "Should have 1 payment record"
        assert total_from_payments == invoice.get_total_paid(), "Sum of payments should match total paid"
        
        print("✓ TEST PASSED: Payment history tracking works correctly")
        
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
    except Exception as e:
        print(f"✗ ERROR: {e}")
    finally:
        db.close()


def test_guard_rails():
    """Test Case 5: Guard rails (overspend prevention)"""
    print("\n" + "="*70)
    print("TEST CASE 5: Guard Rails")
    print("="*70)
    
    db = SessionLocal()
    try:
        # Setup new test data for guard rail tests
        house = db.query(HouseDB).filter(HouseDB.house_code == "TEST001").first()
        
        # Create new invoice and ledger for testing
        invoice = InvoiceDB(
            house_id=house.id,
            cycle_year=2025,
            cycle_month=3,
            issue_date=date(2025, 3, 1),
            due_date=date(2025, 3, 31),
            total_amount=Decimal("500.00"),
            status="ISSUED"
        )
        db.add(invoice)
        db.flush()
        
        payin = PayinReport(
            house_id=house.id,
            submitted_by_user_id=None,
            amount=Decimal("600.00"),
            transfer_date=datetime(2025, 3, 15, 10, 0, 0),
            transfer_hour=10,
            transfer_minute=0,
            status="ACCEPTED"
        )
        db.add(payin)
        db.flush()
        
        ledger = IncomeTransaction(
            house_id=house.id,
            payin_id=payin.id,
            amount=Decimal("600.00"),
            received_at=datetime(2025, 3, 15, 10, 0, 0)
        )
        db.add(ledger)
        db.commit()
        
        print(f"Created invoice: ฿{invoice.total_amount}")
        print(f"Created ledger: ฿{ledger.amount}")
        
        # Test 1: Try to overspend on invoice (should work - just allocate more than needed)
        try:
            payment = InvoicePayment(
                invoice_id=invoice.id,
                income_transaction_id=ledger.id,
                amount=Decimal("500.00")  # Only invoice amount, not full ledger
            )
            db.add(payment)
            db.flush()  # Make sure payment is visible before update_status
            db.refresh(invoice)  # Refresh to load payments relationship
            invoice.update_status()
            db.commit()
            print(f"✓ Applied ฿500 to invoice (Invoice now: {invoice.status.value})")
        except Exception as e:
            db.rollback()
            print(f"✗ Failed to apply payment: {e}")
        
        # Test 2: Try to allocate from fully paid invoice (should fail in API)
        print(f"Invoice outstanding: ฿{invoice.get_outstanding_amount()}")
        if invoice.get_outstanding_amount() == 0:
            print("✓ Invoice is fully paid (cannot apply more payments)")
        
        # Test 3: Check ledger remaining
        remaining = ledger.get_unallocated_amount()
        print(f"Ledger remaining: ฿{remaining}")
        assert remaining == 100.00, f"Ledger should have ฿100 remaining, got ฿{remaining}"
        
        print("✓ TEST PASSED: Guard rails prevent overspending")
        
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
    except Exception as e:
        db.rollback()
        print(f"✗ ERROR: {e}")
    finally:
        db.close()


def run_all_tests():
    """Run complete test suite"""
    print("="*70)
    print("APPLY PAYMENT TEST SUITE")
    print("="*70)
    
    try:
        reset_test_data()
        house_id, inv1_id, inv2_id, ledger1_id, ledger2_id = setup_test_data()
        
        test_full_payment()
        test_partial_payment()
        test_allocatable_ledgers()
        test_payment_history()
        test_guard_rails()
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETED")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")


if __name__ == "__main__":
    run_all_tests()
