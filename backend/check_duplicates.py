#!/usr/bin/env python3
"""Check for duplicate invoices and payment submissions"""
from app.db.session import SessionLocal
from app.db.models.invoice import Invoice
from app.db.models.payin_report import PayinReport
from app.db.models.house import House
from sqlalchemy import func

db = SessionLocal()

print("=" * 80)
print("DUPLICATE DATA INVESTIGATION")
print("=" * 80)

# Find house by code
house = db.query(House).filter(House.house_code.in_(['28/1', '#', '3'])).all()
print(f"\nHouses found: {len(house)}")
for h in house:
    print(f"  - ID {h.id}: {h.house_code} ({h.owner_name})")

# Check all houses
all_houses = db.query(House).all()
print(f"\nAll houses in database:")
for h in all_houses:
    invoice_count = db.query(func.count(Invoice.id)).filter(Invoice.house_id == h.id).scalar()
    payin_count = db.query(func.count(PayinReport.id)).filter(PayinReport.house_id == h.id).scalar()
    print(f"  - House {h.id} ({h.house_code}): {invoice_count} invoices, {payin_count} payins")

print("\n" + "=" * 80)
print("INVOICE ANALYSIS")
print("=" * 80)

# Check for duplicate invoices
invoices = db.query(Invoice).order_by(Invoice.house_id, Invoice.cycle_year, Invoice.cycle_month).all()
print(f"\nTotal invoices: {len(invoices)}")

# Group by house and cycle
from collections import defaultdict
grouped = defaultdict(list)
for inv in invoices:
    key = (inv.house_id, inv.cycle_year, inv.cycle_month)
    grouped[key].append(inv)

print("\nDuplicate invoices found:")
duplicate_found = False
for (house_id, year, month), invs in grouped.items():
    if len(invs) > 1:
        duplicate_found = True
        house_code = db.query(House.house_code).filter(House.id == house_id).scalar()
        print(f"  ⚠️  House {house_code} (ID {house_id}), {year}-{month:02d}: {len(invs)} copies")
        for inv in invs:
            print(f"      - Invoice ID {inv.id}: ฿{inv.total_amount}, Status: {inv.status}, Created: {inv.created_at}")

if not duplicate_found:
    print("  ✅ No duplicate invoices found!")
    print("\nInvoice summary by house:")
    for (house_id, year, month), invs in sorted(grouped.items()):
        house_code = db.query(House.house_code).filter(House.id == house_id).scalar()
        inv = invs[0]
        print(f"  - House {house_code}: {year}-{month:02d} = ฿{inv.total_amount}")

print("\n" + "=" * 80)
print("PAYMENT SUBMISSIONS")
print("=" * 80)

payins = db.query(PayinReport).all()
print(f"\nTotal payin reports: {len(payins)}")
for p in payins:
    house = db.query(House).filter(House.id == p.house_id).first()
    print(f"  - ID {p.id}: House {house.house_code if house else 'UNKNOWN'}, ฿{p.amount}, {p.status}, {p.created_at}")

db.close()
