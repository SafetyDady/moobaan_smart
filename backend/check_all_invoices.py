from app.db.models.invoice import Invoice
from app.db.session import SessionLocal

db = SessionLocal()

# Check all invoices
invoices = db.query(Invoice).order_by(Invoice.cycle_year.desc(), Invoice.cycle_month.desc()).all()

print(f"=== All Invoices ({len(invoices)} total) ===")
for inv in invoices:
    print(f"\nCycle: {inv.cycle_year}-{inv.cycle_month:02d}")
    print(f"  House ID: {inv.house_id}")
    print(f"  Amount: ฿{inv.total_amount}")
    print(f"  Status: {inv.status}")
    print(f"  Due: {inv.due_date}")

# Count by house
from collections import defaultdict
by_house = defaultdict(list)
for inv in invoices:
    by_house[inv.house_id].append(inv)

print(f"\n=== By House ===")
for house_id, invs in by_house.items():
    total = sum(float(inv.total_amount) for inv in invs)
    print(f"House ID {house_id}: {len(invs)} invoices, Total: ฿{total}")

db.close()
