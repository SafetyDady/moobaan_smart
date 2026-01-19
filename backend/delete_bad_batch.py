"""
Script to delete invalid bank statement batch with lost time data
Run this BEFORE re-importing CSV with corrected parser
"""
from app.db.session import SessionLocal
from app.db.models.bank_statement_batch import BankStatementBatch
from app.db.models.bank_transaction import BankTransaction
from sqlalchemy import text


def delete_all_batches():
    """Delete ALL bank statement batches and their transactions"""
    db = SessionLocal()
    
    try:
        # Count current data
        batch_count = db.query(BankStatementBatch).count()
        txn_count = db.query(BankTransaction).count()
        
        print(f"\n🔍 Current Data:")
        print(f"   Batches: {batch_count}")
        print(f"   Transactions: {txn_count}")
        
        if batch_count == 0:
            print("\n✅ No batches to delete. Database is clean.")
            return
        
        # List batches
        batches = db.query(BankStatementBatch).all()
        print(f"\n📋 Batches to be deleted:")
        for batch in batches:
            txn_count_batch = db.query(BankTransaction).filter(
                BankTransaction.bank_statement_batch_id == batch.id
            ).count()
            print(f"   - {batch.original_filename} ({batch.year}/{batch.month}) - {txn_count_batch} transactions")
        
        # Confirm deletion
        print(f"\n⚠️  This will DELETE ALL bank statement data!")
        confirm = input("Type 'DELETE' to confirm: ")
        
        if confirm != 'DELETE':
            print("\n❌ Deletion cancelled.")
            return
        
        # Delete transactions first (FK constraint)
        print(f"\n🗑️  Deleting transactions...")
        deleted_txns = db.query(BankTransaction).delete()
        print(f"   Deleted {deleted_txns} transactions")
        
        # Delete batches
        print(f"\n🗑️  Deleting batches...")
        deleted_batches = db.query(BankStatementBatch).delete()
        print(f"   Deleted {deleted_batches} batches")
        
        # Commit
        db.commit()
        
        print(f"\n✅ Successfully deleted all bank statement data!")
        print(f"\n📌 Next steps:")
        print(f"   1. Ensure CSV parser fix is complete")
        print(f"   2. Re-import CSV file via Bank Statements admin page")
        print(f"   3. Verify transactions show correct time (not 00:00)")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


def verify_time_integrity():
    """Check if imported transactions have proper time (not all 00:00)"""
    db = SessionLocal()
    
    try:
        # Count transactions
        total_txns = db.query(BankTransaction).count()
        
        if total_txns == 0:
            print("\n✅ No transactions in database. Ready for clean import.")
            return
        
        # Count transactions with 00:00 time
        zero_time_query = text("""
            SELECT COUNT(*) 
            FROM bank_transactions 
            WHERE EXTRACT(HOUR FROM effective_at) = 0 
              AND EXTRACT(MINUTE FROM effective_at) = 0
              AND EXTRACT(SECOND FROM effective_at) = 0
        """)
        
        zero_time_count = db.execute(zero_time_query).scalar()
        
        print(f"\n🔍 Time Integrity Check:")
        print(f"   Total transactions: {total_txns}")
        print(f"   Transactions at 00:00:00: {zero_time_count}")
        
        if zero_time_count == total_txns:
            print(f"\n⚠️  WARNING: ALL transactions have time 00:00:00!")
            print(f"   This indicates time data was lost during import.")
            print(f"   Action required:")
            print(f"   1. Run delete_all_batches() to remove invalid data")
            print(f"   2. Ensure CSV parser supports time columns")
            print(f"   3. Re-import CSV file")
        elif zero_time_count > 0:
            percentage = (zero_time_count / total_txns) * 100
            print(f"\n⚠️  {percentage:.1f}% of transactions have time 00:00:00")
            print(f"   This may be normal if:")
            print(f"   - CSV genuinely has no time data")
            print(f"   - Some transactions occurred exactly at midnight")
        else:
            print(f"\n✅ Good! All transactions have specific times.")
            print(f"   Time data is preserved correctly.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("  Bank Statement Time Integrity Fix")
    print("="*60)
    
    # First check integrity
    verify_time_integrity()
    
    print("\n" + "="*60)
    print("  Delete Invalid Batches")
    print("="*60)
    
    # Then offer deletion
    delete_all_batches()
