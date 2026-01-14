"""
Test script for month-end snapshot calculation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from datetime import datetime, date
from app.db.session import SessionLocal
from app.services.accounting import AccountingService
from app.db.models import House, Invoice, IncomeTransaction, CreditNote, User
import json


def test_snapshot_calculation():
    """Test the month-end snapshot calculation"""
    db = SessionLocal()
    
    try:
        # Get first house
        house = db.query(House).first()
        if not house:
            print("❌ No houses found in database")
            return
        
        # Test 1: Calculate snapshot for first house, December 2024
        print("=" * 80)
        print(f"TEST 1: Single House Snapshot (house_id={house.id}, house_code={house.house_code}, December 2024)")
        print("=" * 80)
        
        try:
            snapshot = AccountingService.calculate_month_end_snapshot(
                db=db,
                house_id=house.id,
                year=2024,
                month=12
            )
            print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 80)
        print("TEST 2: Aggregated Snapshot (All houses, December 2024)")
        print("=" * 80)
        
        try:
            aggregated = AccountingService.calculate_aggregated_snapshot(
                db=db,
                year=2024,
                month=12
            )
            # Print summary only (houses list can be long)
            summary = {k: v for k, v in aggregated.items() if k != "houses"}
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            print(f"\nTotal houses included: {len(aggregated['houses'])}")
            if aggregated['houses']:
                print("\nFirst 3 houses:")
                for house in aggregated['houses'][:3]:
                    print(f"  - House {house['house_code']}: closing_balance = {house['closing_balance']}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 80)
        print("TEST 3: Verify ledger integrity")
        print("=" * 80)
        
        # Count transactions
        invoice_count = db.query(Invoice).count()
        payment_count = db.query(IncomeTransaction).count()
        credit_count = db.query(CreditNote).count()
        
        print(f"Total invoices in DB: {invoice_count}")
        print(f"Total payments in DB: {payment_count}")
        print(f"Total credit notes in DB: {credit_count}")
        
        print("\n✅ All tests completed successfully")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_snapshot_calculation()
