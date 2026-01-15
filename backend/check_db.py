#!/usr/bin/env python3
"""Quick script to check database state"""
from app.db.session import SessionLocal, engine
from app.db.models.house import House
from app.db.models.payin_report import PayinReport
from sqlalchemy import func, inspect

db = SessionLocal()

# Check actual table structure
print("=" * 60)
print("DATABASE STRUCTURE CHECK")
print("=" * 60)
inspector = inspect(engine)
cols = inspector.get_columns('houses')
print("\nColumns in 'houses' table:")
for c in cols:
    print(f"  - {c['name']}: {c['type']}")

print("\n" + "=" * 60)
print("DATA CHECK")
print("=" * 60)

# Check house 28/1
house = db.query(House).filter(House.house_code == '28/1').first()
if house:
    print(f"\nHouse 28/1:")
    print(f"  ID: {house.id}")
    print(f"  Owner: {house.owner_name}")
    print(f"  Status: {house.house_status}")
    # Note: No balance field in current schema
else:
    print("\nHouse 28/1 NOT FOUND")

print()

# Check total houses
total_houses = db.query(func.count(House.id)).scalar()
print(f"Total houses in database: {total_houses}")

print()

# Check payin reports for house 28/1
if house:
    payins = db.query(PayinReport).filter(PayinReport.house_id == house.id).all()
    print(f"Pay-in reports for house 28/1: {len(payins)}")
    for p in payins:
        print(f"  - ID {p.id}: {p.amount} THB, Status: {p.status}, Date: {p.created_at}")
else:
    print("Cannot check pay-ins - house not found")

# Check all payin reports
print()
all_payins = db.query(PayinReport).count()
print(f"Total pay-in reports in database: {all_payins}")

db.close()
