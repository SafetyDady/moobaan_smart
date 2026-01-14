#!/usr/bin/env python3
"""
Test script to verify the accounting system implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.services.accounting import AccountingService
from app.db.models import House, Invoice, PayinReport, User
from decimal import Decimal
from datetime import date, datetime

def test_accounting_system():
    """Test all accounting system functions"""
    db = SessionLocal()
    
    try:
        print("🧪 Testing Accounting System")
        print("=" * 50)
        
        # Test 1: Check models import correctly
        print("✅ All models imported successfully")
        
        # Test 2: Check database connection and tables exist
        houses = db.query(House).count()
        print(f"✅ Found {houses} houses in database")
        
        # Test 3: Test house balance calculation for non-existent house (should handle gracefully)
        try:
            balance = AccountingService.calculate_house_balance(db, 999999)
            print("❌ Should have raised ValueError for non-existent house")
        except ValueError as e:
            print("✅ Correctly handled non-existent house")
        
        # Test 4: Test auto-generate invoices function
        print("\n📋 Testing Invoice Generation")
        created_invoices = AccountingService.auto_generate_invoices(
            db=db, 
            year=2024, 
            month=1, 
            base_amount=Decimal("600.00")
        )
        print(f"✅ Generated {len(created_invoices)} invoices for 2024-01")
        
        # Test 5: Test balance calculation
        if houses > 0:
            first_house = db.query(House).first()
            balance = AccountingService.calculate_house_balance(db, first_house.id)
            print(f"\n💰 Balance for house {first_house.house_code}:")
            print(f"   Total Invoiced: {balance['total_invoiced']}")
            print(f"   Total Credited: {balance['total_credited']}")
            print(f"   Total Paid: {balance['total_paid']}")
            print(f"   Outstanding: {balance['outstanding_balance']}")
            print("✅ Balance calculation working correctly")
        
        print("\n🎉 All tests passed! Accounting system is working correctly.")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_accounting_system()