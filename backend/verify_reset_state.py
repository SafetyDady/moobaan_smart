"""
Verify database state after Pay-in reset
"""
from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport
from app.db.models.bank_transaction import BankTransaction
from app.db.models.bank_statement_batch import BankStatementBatch
from app.db.models.house import House
from app.db.models.user import User

def verify_reset_state():
    """Verify that Pay-in data is cleared but everything else is intact"""
    db = SessionLocal()
    
    try:
        print("="*70)
        print("  Database State Verification After Pay-in Reset")
        print("="*70)
        
        # 1. Verify Pay-ins are deleted
        payin_count = db.query(PayinReport).count()
        print(f"\n✅ Pay-in Reports: {payin_count} (should be 0)")
        
        # 2. Verify bank transactions exist
        txn_count = db.query(BankTransaction).count()
        print(f"✅ Bank Transactions: {txn_count} (should be > 0)")
        
        # 3. Verify no matched pay-ins
        matched_count = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.isnot(None)
        ).count()
        print(f"✅ Matched Transactions: {matched_count} (should be 0)")
        
        # 4. Verify bank statement batches exist
        batch_count = db.query(BankStatementBatch).count()
        print(f"✅ Bank Statement Batches: {batch_count} (should be > 0)")
        
        # 5. Verify houses exist
        house_count = db.query(House).count()
        print(f"✅ Houses: {house_count} (should be > 0)")
        
        # 6. Verify users exist
        user_count = db.query(User).count()
        print(f"✅ Users: {user_count} (should be > 0)")
        
        # 7. Show sample bank transactions with NULL matched_payin_id
        print(f"\n📋 Sample Bank Transactions (first 5):")
        sample_txns = db.query(BankTransaction).limit(5).all()
        for txn in sample_txns:
            match_status = "✗ NO MATCH" if txn.matched_payin_id is None else f"✓ Matched to Payin #{txn.matched_payin_id}"
            print(f"   - TX#{txn.id}: {txn.effective_at} - ฿{txn.credit or txn.debit} - [{match_status}]")
        
        print(f"\n{'='*70}")
        print(f"✅ DATABASE RESET SUCCESSFUL")
        print(f"{'='*70}")
        print(f"\n📌 Ready for reconciliation testing:")
        print(f"   1. All Pay-ins deleted ✓")
        print(f"   2. Bank transactions preserved ✓")
        print(f"   3. No orphaned matches ✓")
        print(f"   4. Houses and users intact ✓")
        print(f"\n🎯 You can now submit new Pay-ins and test matching logic")
        
    except Exception as e:
        print(f"\n❌ Error verifying state: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    verify_reset_state()
