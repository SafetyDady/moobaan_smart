from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.income_transaction import IncomeTransaction
from app.db.session import SessionLocal

db = SessionLocal()

# Check invoices for house 28/1 (ID=3)
invoices = db.query(Invoice).filter(Invoice.house_id == 3).order_by(Invoice.cycle_year.desc(), Invoice.cycle_month.desc()).all()

print("=== Invoices for House 28/1 ===")
total_unpaid = 0
for inv in invoices:
    print(f"\nCycle: {inv.cycle_year}-{inv.cycle_month:02d}")
    print(f"  ID: {inv.id}")
    print(f"  Amount: ฿{inv.total_amount}")
    print(f"  Status: {inv.status}")
    print(f"  Due: {inv.due_date}")
    
    if inv.status != InvoiceStatus.PAID:
        total_unpaid += float(inv.total_amount)

print(f"\n💰 Total Unpaid: ฿{total_unpaid}")

# Check income transactions
incomes = db.query(IncomeTransaction).filter(IncomeTransaction.house_id == 3).all()
print(f"\n=== Income Transactions ===")
total_income = 0
for income in incomes:
    print(f"ID: {income.id}, Amount: ฿{income.amount}, Payin: {income.payin_id}")
    total_income += float(income.amount)

print(f"\n💵 Total Income: ฿{total_income}")
print(f"📊 Outstanding after payments: ฿{total_unpaid - total_income}")

db.close()
