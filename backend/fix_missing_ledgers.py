"""Fix: Create missing IncomeTransaction for ACCEPTED payins"""
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport, PayinStatus
from app.db.models.income_transaction import IncomeTransaction
from app.db.models.bank_transaction import BankTransaction

db = SessionLocal()

# Find ACCEPTED payins without IncomeTransaction
payins = db.query(PayinReport).filter(PayinReport.status == PayinStatus.ACCEPTED).all()

created_count = 0
for payin in payins:
    # Check if IncomeTransaction already exists
    existing = db.query(IncomeTransaction).filter(IncomeTransaction.payin_id == payin.id).first()
    if not existing:
        print(f"Creating IncomeTransaction for Pay-in #{payin.id}...")
        
        # Get bank transaction for received_at date
        received_at = payin.transfer_date
        if payin.matched_statement_txn_id:
            bank_txn = db.query(BankTransaction).filter(
                BankTransaction.id == payin.matched_statement_txn_id
            ).first()
            if bank_txn:
                received_at = bank_txn.effective_at or payin.transfer_date
        
        # Create IncomeTransaction
        income = IncomeTransaction(
            house_id=payin.house_id,
            payin_id=payin.id,
            reference_bank_transaction_id=payin.matched_statement_txn_id,
            amount=payin.amount,
            received_at=received_at
        )
        db.add(income)
        created_count += 1
        print(f"  ✅ Created IncomeTransaction for House:{payin.house_id} Amount:{payin.amount}")

db.commit()
print(f"\nTotal created: {created_count}")

db.close()
