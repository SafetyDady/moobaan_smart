"""
Quick test to verify transfer_datetime property and matching validation
"""
import sys
sys.path.append('.')

from datetime import datetime, timedelta
from app.db.models.payin_report import PayinReport, PayinStatus
from app.db.models.bank_transaction import BankTransaction
from app.db.session import SessionLocal
import pytz

def test_transfer_datetime():
    """Test that transfer_datetime property computes correctly"""
    print("\n" + "="*60)
    print("TEST: transfer_datetime Property")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Get first PENDING payin (if any)
        payin = db.query(PayinReport).filter(
            PayinReport.status == PayinStatus.PENDING
        ).first()
        
        if not payin:
            print("❌ No PENDING pay-ins found. Create one first.")
            return False
        
        print(f"\n✓ Found Pay-in ID: {payin.id}")
        print(f"  House: {payin.house.house_code}")
        print(f"  Amount: ฿{payin.amount}")
        print(f"  transfer_date: {payin.transfer_date}")
        print(f"  transfer_hour: {payin.transfer_hour}")
        print(f"  transfer_minute: {payin.transfer_minute}")
        print(f"\n  transfer_datetime (computed): {payin.transfer_datetime}")
        
        # Verify computation
        if payin.transfer_datetime:
            expected_dt = payin.transfer_date.replace(
                hour=payin.transfer_hour, 
                minute=payin.transfer_minute, 
                second=0, 
                microsecond=0
            )
            if payin.transfer_datetime == expected_dt:
                print(f"  ✓ Computation correct!")
            else:
                print(f"  ❌ Computation error! Expected {expected_dt}")
                return False
        else:
            print(f"  ❌ transfer_datetime is None!")
            return False
        
        # Check matching status
        print(f"\n  matched_statement_txn_id: {payin.matched_statement_txn_id}")
        print(f"  is_matched: {payin.matched_statement_txn_id is not None}")
        
        return True
        
    finally:
        db.close()

def test_unmatched_transactions():
    """Test listing unmatched bank transactions"""
    print("\n" + "="*60)
    print("TEST: Unmatched Bank Transactions")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Query unmatched credit transactions
        txns = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.is_(None),
            BankTransaction.credit > 0
        ).order_by(BankTransaction.effective_at.desc()).limit(5).all()
        
        print(f"\n✓ Found {len(txns)} unmatched credit transactions (showing first 5):")
        
        for i, txn in enumerate(txns, 1):
            print(f"\n  {i}. Transaction ID: {str(txn.id)[:8]}...")
            print(f"     Amount: ฿{txn.credit}")
            print(f"     Time: {txn.effective_at}")
            print(f"     Description: {txn.description[:50]}...")
            print(f"     Matched: {txn.matched_payin_id is not None}")
        
        return len(txns) > 0
        
    finally:
        db.close()

def test_time_tolerance():
    """Test time tolerance calculation"""
    print("\n" + "="*60)
    print("TEST: Time Tolerance Calculation")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Get first payin and first unmatched bank txn
        payin = db.query(PayinReport).filter(
            PayinReport.status == PayinStatus.PENDING
        ).first()
        
        txn = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.is_(None),
            BankTransaction.credit > 0
        ).first()
        
        if not payin or not txn:
            print("❌ Need both payin and unmatched transaction for test")
            return False
        
        payin_time = payin.transfer_datetime
        bank_time = txn.effective_at
        
        if not payin_time:
            print("❌ payin.transfer_datetime is None")
            return False
        
        time_diff = abs((payin_time - bank_time).total_seconds())
        
        print(f"\n  Pay-in time: {payin_time}")
        print(f"  Bank txn time: {bank_time}")
        print(f"  Time difference: {time_diff} seconds ({time_diff/60:.2f} minutes)")
        print(f"\n  Within ±1 minute? {time_diff <= 60}")
        print(f"  Within ±5 minutes? {time_diff <= 300}")
        
        # Check amount match
        amount_diff = abs(float(txn.credit) - float(payin.amount))
        print(f"\n  Pay-in amount: ฿{payin.amount}")
        print(f"  Bank txn amount: ฿{txn.credit}")
        print(f"  Amount difference: ฿{amount_diff}")
        print(f"  Exact match? {amount_diff < 0.01}")
        
        return True
        
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔍 MANUAL MATCHING - Verification Tests")
    print("=" * 60)
    
    success = True
    
    # Run tests
    if not test_transfer_datetime():
        success = False
    
    if not test_unmatched_transactions():
        success = False
    
    if not test_time_tolerance():
        success = False
    
    print("\n" + "="*60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("="*60 + "\n")
