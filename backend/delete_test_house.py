#!/usr/bin/env python3
"""Delete TEST-01 house and all related data"""
from app.db.session import SessionLocal
from app.db.models.house import House
from app.db.models.payin_report import PayinReport
from app.db.models.house_member import HouseMember
from app.db.models.invoice import Invoice
from app.db.models.income_transaction import IncomeTransaction

db = SessionLocal()

try:
    # Find TEST-01 house
    house = db.query(House).filter(House.id == 8).first()
    
    if not house:
        print("❌ House TEST-01 (ID=8) not found!")
        exit(1)
    
    print(f"Found house: ID {house.id}, Code: {house.house_code}")
    print()
    
    # Check and delete related data
    print("=" * 60)
    print("DELETING RELATED DATA")
    print("=" * 60)
    
    # 1. Delete payin reports
    payins = db.query(PayinReport).filter(PayinReport.house_id == 8).all()
    print(f"\n1. Payin reports: {len(payins)} found")
    for p in payins:
        print(f"   - Deleting payin ID {p.id}: ฿{p.amount}, {p.status}")
        db.delete(p)
    
    # 2. Delete income transactions
    incomes = db.query(IncomeTransaction).filter(IncomeTransaction.house_id == 8).all()
    print(f"\n2. Income transactions: {len(incomes)} found")
    for inc in incomes:
        print(f"   - Deleting income ID {inc.id}: ฿{inc.amount}")
        db.delete(inc)
    
    # 3. Delete invoices
    invoices = db.query(Invoice).filter(Invoice.house_id == 8).all()
    print(f"\n3. Invoices: {len(invoices)} found")
    for inv in invoices:
        print(f"   - Deleting invoice ID {inv.id}: {inv.cycle_year}-{inv.cycle_month:02d}")
        db.delete(inv)
    
    # 4. Delete house members
    members = db.query(HouseMember).filter(HouseMember.house_id == 8).all()
    print(f"\n4. House members: {len(members)} found")
    for m in members:
        print(f"   - Deleting member ID {m.id}, User ID {m.user_id}")
        db.delete(m)
    
    # 5. Delete the house itself
    print(f"\n5. Deleting house: {house.house_code} (ID {house.id})")
    db.delete(house)
    
    # Commit all changes
    print("\n" + "=" * 60)
    print("COMMITTING CHANGES...")
    print("=" * 60)
    db.commit()
    
    print("\n✅ Successfully deleted house TEST-01 and all related data!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    db.rollback()
    raise
finally:
    db.close()
