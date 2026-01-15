from app.db.models.payin_report import PayinReport, PayinStatus
from app.db.models.income_transaction import IncomeTransaction
from app.db.session import SessionLocal

db = SessionLocal()

# Check payin report status
payin = db.query(PayinReport).filter(PayinReport.id == 17).first()
print("=== PayIn Report ===")
print(f"ID: {payin.id}")
print(f"House ID: {payin.house_id}")
print(f"Amount: {payin.amount}")
print(f"Status: {payin.status}")
print(f"Accepted by: {payin.accepted_by}")
print(f"Accepted at: {payin.accepted_at}")

# Check if IncomeTransaction was created
income = db.query(IncomeTransaction).filter(IncomeTransaction.payin_id == 17).first()
print("\n=== Income Transaction ===")
if income:
    print(f"ID: {income.id}")
    print(f"House ID: {income.house_id}")
    print(f"Amount: {income.amount}")
    print(f"Description: {income.description}")
    print(f"Transaction date: {income.transaction_date}")
    print(f"Payin ID: {income.payin_id}")
    print("✅ Income transaction created successfully!")
else:
    print("❌ No income transaction found")

db.close()
