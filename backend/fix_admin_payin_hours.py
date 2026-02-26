#!/usr/bin/env python3
"""
One-time data fix: Correct transfer_hour/transfer_minute for admin-created pay-ins.

Problem: admin-create-from-bank used bank_txn.effective_at.hour (UTC) 
instead of converting to Asia/Bangkok (+7) first.
e.g., 13:40 Bangkok → stored as 06:40 (UTC hour).

Fix: Recalculate from transfer_date (UTC) → Bangkok timezone.

Safe to run multiple times (idempotent — always recalculates from source).
Only affects ADMIN_CREATED and LINE_RECEIVED pay-ins.

Usage:
    python fix_admin_payin_hours.py
"""
import os
import sys

def main():
    print("🔧 Fix admin-created pay-in transfer_hour/transfer_minute (UTC → Bangkok)")
    print("=" * 70)
    
    try:
        from app.db.session import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # First, check how many records are affected
            result = conn.execute(text("""
                SELECT id, house_id, transfer_hour, transfer_minute,
                       transfer_date,
                       EXTRACT(HOUR FROM (transfer_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok'))::int AS correct_hour,
                       EXTRACT(MINUTE FROM (transfer_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok'))::int AS correct_minute
                FROM payin_reports
                WHERE source IN ('ADMIN_CREATED', 'LINE_RECEIVED')
                  AND reference_bank_transaction_id IS NOT NULL
            """))
            
            rows = result.fetchall()
            
            if not rows:
                print("✅ No admin-created pay-ins found. Nothing to fix.")
                return
            
            print(f"📋 Found {len(rows)} admin-created pay-in(s):\n")
            
            needs_fix = 0
            for row in rows:
                current = f"{row.transfer_hour:02d}:{row.transfer_minute:02d}"
                correct = f"{row.correct_hour:02d}:{row.correct_minute:02d}"
                status = "✅ OK" if current == correct else "❌ WRONG"
                if current != correct:
                    needs_fix += 1
                print(f"  Pay-in #{row.id} (house {row.house_id}): "
                      f"current={current}, correct={correct} [{status}]")
            
            if needs_fix == 0:
                print(f"\n✅ All {len(rows)} record(s) already correct. No fix needed.")
                return
            
            print(f"\n🔧 Fixing {needs_fix} record(s)...")
            
            # Apply fix
            update_result = conn.execute(text("""
                UPDATE payin_reports
                SET 
                    transfer_hour = EXTRACT(HOUR FROM (transfer_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok'))::int,
                    transfer_minute = EXTRACT(MINUTE FROM (transfer_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Bangkok'))::int
                WHERE source IN ('ADMIN_CREATED', 'LINE_RECEIVED')
                  AND reference_bank_transaction_id IS NOT NULL
            """))
            
            conn.commit()
            print(f"✅ Updated {update_result.rowcount} record(s) successfully!")
            
            # Verify
            print("\n📋 Verification:")
            verify = conn.execute(text("""
                SELECT id, house_id, transfer_hour, transfer_minute
                FROM payin_reports
                WHERE source IN ('ADMIN_CREATED', 'LINE_RECEIVED')
                  AND reference_bank_transaction_id IS NOT NULL
            """))
            for row in verify.fetchall():
                print(f"  Pay-in #{row.id} (house {row.house_id}): "
                      f"{row.transfer_hour:02d}:{row.transfer_minute:02d}")
            
            print("\n✅ Data fix complete!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
