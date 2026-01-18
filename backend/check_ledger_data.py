"""Check database for ACCEPTED payins and income transactions"""
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport, PayinStatus
from app.db.models.income_transaction import IncomeTransaction

db = SessionLocal()

# Check ACCEPTED Pay-ins
payins = db.query(PayinReport).filter(PayinReport.status == PayinStatus.ACCEPTED).all()
print(f"ACCEPTED Pay-ins: {len(payins)}")
for p in payins:
    print(f"  ID:{p.id} House:{p.house_id} Amount:{p.amount}")

# Check IncomeTransactions
incomes = db.query(IncomeTransaction).all()
print(f"\nIncomeTransactions: {len(incomes)}")
for i in incomes:
    print(f"  ID:{i.id} House:{i.house_id} Payin:{i.payin_id} Amount:{i.amount}")

db.close()
