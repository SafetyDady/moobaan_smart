"""Unmatch all matched pay-ins for testing"""
from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport
from app.db.models.bank_transaction import BankTransaction

db = SessionLocal()

# Find all matched payins
matched_payins = db.query(PayinReport).filter(
    PayinReport.matched_statement_txn_id != None
).all()

print(f"Found {len(matched_payins)} matched payins")

for payin in matched_payins:
    txn_id = payin.matched_statement_txn_id
    
    # Unmatch payin
    payin.matched_statement_txn_id = None
    
    # Unmatch bank transaction
    txn = db.query(BankTransaction).filter(BankTransaction.id == txn_id).first()
    if txn:
        txn.matched_payin_id = None
    
    print(f"Unmatched payin #{payin.id}")

db.commit()
print("✅ All payins unmatched")
db.close()
