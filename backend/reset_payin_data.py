"""
Reset Pay-in Data for Reconciliation Testing
Deletes ALL pay-in reports while preserving bank statement data
"""
from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport
from app.db.models.bank_transaction import BankTransaction
from sqlalchemy import text


def verify_current_state():
    """Check current state of pay-ins and matches"""
    db = SessionLocal()
    
    try:
        # Count pay-ins
        payin_count = db.query(PayinReport).count()
        
        # Count matched bank transactions
        matched_txns = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.isnot(None)
        ).count()
        
        print(f"\n🔍 Current State:")
        print(f"   Total Pay-ins: {payin_count}")
        print(f"   Matched Bank Transactions: {matched_txns}")
        
        if payin_count == 0:
            print(f"\n✅ No pay-ins exist. Database is already clean.")
            return False
        
        # Show sample pay-ins
        sample_payins = db.query(PayinReport).limit(5).all()
        print(f"\n📋 Sample Pay-ins (first 5):")
        for payin in sample_payins:
            match_status = "✓ Matched" if payin.matched_statement_txn_id else "○ Unmatched"
            print(f"   - ID {payin.id}: {payin.house.house_code if payin.house else 'N/A'} - ฿{payin.amount} - {payin.status.value} [{match_status}]")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking state: {e}")
        raise
    finally:
        db.close()


def reset_payin_data():
    """Delete ALL pay-in reports and clear matches"""
    db = SessionLocal()
    
    try:
        # Count before deletion
        payin_count = db.query(PayinReport).count()
        matched_count = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.isnot(None)
        ).count()
        
        if payin_count == 0:
            print("\n✅ No pay-ins to delete. Database is already clean.")
            return
        
        print(f"\n⚠️  WARNING: This will DELETE ALL pay-in data!")
        print(f"   - {payin_count} Pay-in report(s)")
        print(f"   - {matched_count} Bank transaction match(es) will be cleared")
        print(f"\n   Bank statement data will be PRESERVED:")
        print(f"   ✓ Bank accounts")
        print(f"   ✓ Bank statement batches")
        print(f"   ✓ Bank transactions")
        print(f"   ✓ Houses, invoices, users")
        
        # Auto-confirm for test environment
        print(f"\n✅ Proceeding with reset (test environment)...")
        confirm = 'RESET'
        
        if confirm != 'RESET':
            print("\n❌ Reset cancelled.")
            return
        
        # Step 1: Clear matched_payin_id from bank_transactions
        # (This should happen automatically due to FK ondelete="SET NULL", but we do it explicitly for safety)
        print(f"\n🔓 Clearing bank transaction matches...")
        cleared_matches = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.isnot(None)
        ).update({"matched_payin_id": None}, synchronize_session=False)
        print(f"   Cleared {cleared_matches} match(es)")
        
        # Step 2: Delete all pay-in reports
        print(f"\n🗑️  Deleting pay-in reports...")
        deleted_payins = db.query(PayinReport).delete()
        print(f"   Deleted {deleted_payins} pay-in(s)")
        
        # Commit transaction
        db.commit()
        
        # Verify deletion
        remaining_payins = db.query(PayinReport).count()
        remaining_matches = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.isnot(None)
        ).count()
        
        print(f"\n✅ Pay-in data reset complete!")
        print(f"\n📊 Final State:")
        print(f"   Remaining Pay-ins: {remaining_payins}")
        print(f"   Remaining Matches: {remaining_matches}")
        
        print(f"\n📌 Next Steps:")
        print(f"   1. Re-submit Pay-ins via mobile app or admin UI")
        print(f"   2. Test matching with bank transactions")
        print(f"   3. Verify reconciliation logic")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during reset: {e}")
        raise
    finally:
        db.close()


def verify_bank_data_intact():
    """Verify bank statement data remains intact after reset"""
    db = SessionLocal()
    
    try:
        from app.db.models.bank_statement_batch import BankStatementBatch
        
        batch_count = db.query(BankStatementBatch).count()
        txn_count = db.query(BankTransaction).count()
        
        print(f"\n✅ Bank Statement Data Verification:")
        print(f"   Batches: {batch_count}")
        print(f"   Transactions: {txn_count}")
        
        if batch_count > 0:
            print(f"\n   Bank statement data is INTACT ✓")
        
    except Exception as e:
        print(f"\n❌ Error verifying data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("="*70)
    print("  Pay-in Data Reset for Reconciliation Testing")
    print("="*70)
    
    # Check current state
    has_data = verify_current_state()
    
    if not has_data:
        print("\n✅ Nothing to reset. Database is ready for testing.")
    else:
        print("\n" + "="*70)
        print("  Proceed with Reset")
        print("="*70)
        
        # Execute reset
        reset_payin_data()
        
        # Verify bank data intact
        verify_bank_data_intact()
    
    print("\n" + "="*70)
