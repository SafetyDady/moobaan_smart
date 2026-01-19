"""Check payin 27 details"""
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport
from app.db.models.income_transaction import IncomeTransaction

db = SessionLocal()

# Check payin 27
p = db.query(PayinReport).filter(PayinReport.id == 27).first()
if p:
    print(f"Pay-in ID: {p.id}")
    print(f"House ID: {p.house_id}")
    print(f"Amount: {p.amount}")
    print(f"Status: {p.status}")
    print(f"matched_statement_txn_id: {p.matched_statement_txn_id}")
    print(f"accepted_at: {p.accepted_at}")
    
    # Check if IncomeTransaction exists
    income = db.query(IncomeTransaction).filter(IncomeTransaction.payin_id == p.id).first()
    if income:
        print(f"\nIncomeTransaction exists! ID: {income.id}")
    else:
        print(f"\nNo IncomeTransaction found for this pay-in!")
else:
    print("Pay-in 27 not found")

db.close()
