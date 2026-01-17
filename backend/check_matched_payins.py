#!/usr/bin/env python3
"""Check matched pay-ins after testing Manual Matching"""

from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport
from app.db.models.bank_transaction import BankTransaction

def main():
    db = SessionLocal()
    try:
        # Query matched pay-ins
        matched_payins = db.query(PayinReport).filter(
            PayinReport.matched_statement_txn_id.isnot(None)
        ).all()
        
        print("\n" + "="*60)
        print(f"✅ Pay-ins ที่ Match แล้ว: {len(matched_payins)} รายการ")
        print("="*60)
        
        if not matched_payins:
            print("   (ยังไม่มี Pay-in ที่ Match)")
        else:
            for p in matched_payins:
                print(f"\n📌 Pay-in ID: {p.id}")
                print(f"   Amount: {p.amount:.2f} บาท")
                print(f"   Transfer Time: {p.transfer_datetime}")
                print(f"   Matched Txn ID: {p.matched_statement_txn_id}")
                print(f"   Status: {p.status}")
                
                # Get matched bank transaction details
                if p.matched_statement_txn_id:
                    txn = db.query(BankTransaction).filter(
                        BankTransaction.id == p.matched_statement_txn_id
                    ).first()
                    if txn:
                        print(f"   Bank Txn Time: {txn.effective_at}")
                        print(f"   Bank Txn Amount: {txn.credit:.2f} บาท")
        
        print("\n" + "="*60)
        
        # Query matched bank transactions
        matched_txns = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id.isnot(None)
        ).count()
        print(f"✅ Bank Transactions ที่ Match แล้ว: {matched_txns} รายการ")
        
        # Unmatched counts
        unmatched_payins = db.query(PayinReport).filter(
            PayinReport.status == 'PENDING',
            PayinReport.matched_statement_txn_id.is_(None)
        ).count()
        
        unmatched_txns = db.query(BankTransaction).filter(
            BankTransaction.credit > 0,
            BankTransaction.matched_payin_id.is_(None)
        ).count()
        
        print(f"⏳ Pay-ins ยังไม่ Match: {unmatched_payins} รายการ")
        print(f"⏳ Bank Transactions ยังไม่ Match: {unmatched_txns} รายการ")
        print("="*60 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
