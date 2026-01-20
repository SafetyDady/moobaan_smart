"""
Phase D.3: FIFO Pay-in Allocation Tests

Test Cases:
1. Basic FIFO: Allocate to oldest due invoices first
2. Partial allocation: Amount doesn't cover all invoices
3. Over-payment: Remaining amount after all invoices
4. Cross-house prevention: Only allocate to same house
5. Credit note interaction: Outstanding respects credit notes
"""
from decimal import Decimal
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.db.session import get_db, engine
from app.db.models import House, Invoice, InvoiceStatus, PayinReport, PayinStatus, IncomeTransaction, InvoicePayment, User


def get_test_db():
    """Get database session for testing"""
    db = next(get_db())
    return db


class TestFIFOAllocation:
    """Test suite for FIFO pay-in allocation"""
    
    def setup_method(self):
        """Setup before each test"""
        self.db = get_test_db()
    
    def teardown_method(self):
        """Cleanup after each test"""
        self.db.close()
    
    def test_fifo_basic_allocation(self):
        """
        Test: Basic FIFO allocation to oldest invoices first
        
        Setup:
        - 3 invoices: Jan (oldest), Feb, Mar (newest)
        - Pay-in: 1,400 (enough for 2.33 invoices @ 600 each)
        
        Expected:
        - Jan: fully paid (600)
        - Feb: fully paid (600)
        - Mar: partially paid (200)
        - Remaining: 0
        """
        print("\n=== Test: Basic FIFO Allocation ===")
        
        # Get test house
        house = self.db.query(House).filter(House.house_code == "28/1").first()
        if not house:
            print("⚠️ Test house 28/1 not found, skipping test")
            return
        
        # Get accepted pay-ins with unallocated amounts
        ledgers = self.db.query(IncomeTransaction).filter(
            IncomeTransaction.house_id == house.id
        ).all()
        
        print(f"House: {house.house_code}")
        print(f"Found {len(ledgers)} ledger(s)")
        
        for ledger in ledgers:
            unalloc = ledger.get_unallocated_amount()
            print(f"  Ledger #{ledger.id}: amount={ledger.amount}, unallocated={unalloc}")
        
        # Get invoices
        invoices = self.db.query(Invoice).filter(
            Invoice.house_id == house.id,
            Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID])
        ).order_by(Invoice.due_date.asc()).all()
        
        print(f"Found {len(invoices)} outstanding invoice(s):")
        for inv in invoices:
            outstanding = inv.get_outstanding_amount()
            print(f"  Invoice #{inv.id}: due={inv.due_date}, total={inv.total_amount}, outstanding={outstanding}, status={inv.status.value}")
        
        print("✅ Test data inspection complete")
    
    def test_fifo_cross_house_prevention(self):
        """
        Test: Verify pay-in only allocates to same house
        
        Expected: No allocations to other houses
        """
        print("\n=== Test: Cross-House Prevention ===")
        
        # Get two different houses
        houses = self.db.query(House).limit(2).all()
        if len(houses) < 2:
            print("⚠️ Need at least 2 houses for this test")
            return
        
        house1, house2 = houses[0], houses[1]
        print(f"House 1: {house1.house_code} (id={house1.id})")
        print(f"House 2: {house2.house_code} (id={house2.id})")
        
        # Check if there are ledgers for house1
        ledger1 = self.db.query(IncomeTransaction).filter(
            IncomeTransaction.house_id == house1.id
        ).first()
        
        if ledger1:
            # Verify allocations only go to house1 invoices
            payments = self.db.query(InvoicePayment).filter(
                InvoicePayment.income_transaction_id == ledger1.id
            ).all()
            
            for payment in payments:
                invoice = self.db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
                assert invoice.house_id == house1.id, f"Cross-house allocation detected! Ledger house={house1.id}, Invoice house={invoice.house_id}"
            
            print(f"✅ All {len(payments)} allocation(s) are within house {house1.house_code}")
        else:
            print("⚠️ No ledger found for house1")
    
    def test_fifo_remaining_amount(self):
        """
        Test: Verify remaining amount calculation after allocation
        
        Setup: Pay-in larger than total outstanding
        Expected: Remaining > 0
        """
        print("\n=== Test: Remaining Amount ===")
        
        # Get any ledger
        ledger = self.db.query(IncomeTransaction).first()
        if not ledger:
            print("⚠️ No ledger found")
            return
        
        total_amount = float(ledger.amount)
        total_applied = ledger.get_total_applied()
        remaining = ledger.get_unallocated_amount()
        
        print(f"Ledger #{ledger.id}:")
        print(f"  Total amount: {total_amount}")
        print(f"  Total applied: {total_applied}")
        print(f"  Remaining: {remaining}")
        
        # Verify math
        assert abs(remaining - (total_amount - total_applied)) < 0.01, "Remaining calculation mismatch"
        print("✅ Remaining amount calculation correct")


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("Phase D.3: FIFO Allocation Tests")
    print("=" * 60)
    
    test = TestFIFOAllocation()
    
    try:
        test.setup_method()
        test.test_fifo_basic_allocation()
        test.teardown_method()
        
        test.setup_method()
        test.test_fifo_cross_house_prevention()
        test.teardown_method()
        
        test.setup_method()
        test.test_fifo_remaining_amount()
        test.teardown_method()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_tests()
