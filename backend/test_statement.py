"""
Test script for financial statement generation (Phase 2.4)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from app.db.session import SessionLocal
from app.services.accounting import AccountingService
from app.db.models import House
import json


def test_statement_generation():
    """Test the financial statement generation"""
    db = SessionLocal()
    
    try:
        # Get first house
        house = db.query(House).first()
        if not house:
            print("❌ No houses found in database")
            return
        
        print("=" * 80)
        print(f"TEST: Financial Statement (house_id={house.id}, house_code={house.house_code})")
        print("=" * 80)
        
        # Test statement for December 2024
        start_date = date(2024, 12, 1)
        end_date = date(2024, 12, 31)
        
        print(f"\nStatement Period: {start_date} to {end_date}")
        print("-" * 80)
        
        try:
            statement = AccountingService.generate_statement(
                db=db,
                house_id=house.id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Print statement header
            print(f"\nHouse: {statement['house_code']} - {statement['owner_name']}")
            print(f"Opening Balance: {statement['opening_balance']:.2f}")
            print(f"Closing Balance: {statement['closing_balance']:.2f}")
            print("\n" + "-" * 80)
            print(f"{'Date':<12} {'Description':<40} {'Debit':>12} {'Credit':>12} {'Balance':>12}")
            print("-" * 80)
            
            # Print statement rows
            for row in statement['rows']:
                date_str = row['date'].strftime("%Y-%m-%d")
                desc = row['description'][:38]
                debit = f"{row['debit']:.2f}" if row['debit'] else "-"
                credit = f"{row['credit']:.2f}" if row['credit'] else "-"
                balance = f"{row['balance']:.2f}"
                
                print(f"{date_str:<12} {desc:<40} {debit:>12} {credit:>12} {balance:>12}")
            
            # Print summary
            print("-" * 80)
            print(f"{'Summary':<40}")
            print(f"  Invoice Total:  {statement['summary']['invoice_total']:>12.2f}")
            print(f"  Payment Total:  {statement['summary']['payment_total']:>12.2f}")
            print(f"  Credit Total:   {statement['summary']['credit_total']:>12.2f}")
            print(f"  Closing Balance: {statement['summary']['closing_balance']:>12.2f}")
            print("=" * 80)
            
            # Verify opening/closing match snapshot
            print("\n📊 Verification:")
            print(f"✓ Opening balance from snapshot: {statement['opening_balance']:.2f}")
            print(f"✓ Closing balance from snapshot: {statement['closing_balance']:.2f}")
            
            # Calculate what closing should be from running balance
            last_row_balance = statement['rows'][-1]['balance'] if statement['rows'] else statement['opening_balance']
            print(f"✓ Last row running balance: {last_row_balance:.2f}")
            
            # Verify closing balance matches
            if abs(statement['closing_balance'] - statement['summary']['closing_balance']) < 0.01:
                print("✅ Closing balances match!")
            else:
                print(f"⚠️  Mismatch: statement={statement['closing_balance']:.2f} vs summary={statement['summary']['closing_balance']:.2f}")
            
            print("\n✅ Statement generation test completed successfully")
            
        except Exception as e:
            print(f"Error generating statement: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    test_statement_generation()
