#!/usr/bin/env python3
"""Check payin reports and user relationships"""
from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport
from app.db.models.user import User
from app.db.models.house_member import HouseMember
from app.db.models.house import House

db = SessionLocal()

print("=" * 80)
print("PAYIN REPORTS ANALYSIS")
print("=" * 80)

# Check all payins
payins = db.query(PayinReport).all()
print(f"\nTotal payin reports: {len(payins)}")

for p in payins:
    house = db.query(House).filter(House.id == p.house_id).first()
    user = db.query(User).filter(User.id == p.submitted_by_user_id).first()
    print(f"\nPayin ID {p.id}:")
    print(f"  House ID: {p.house_id} ({house.house_code if house else 'UNKNOWN'})")
    print(f"  Amount: ฿{p.amount}")
    print(f"  Status: {p.status}")
    print(f"  Submitted by: User ID {p.submitted_by_user_id} ({user.username if user else 'UNKNOWN'})")
    print(f"  Created: {p.created_at}")

print("\n" + "=" * 80)
print("USER-HOUSE RELATIONSHIPS")
print("=" * 80)

# Check all users and their houses
users = db.query(User).filter(User.role == 'resident').all()
print(f"\nTotal resident users: {len(users)}")

for u in users:
    membership = db.query(HouseMember).filter(HouseMember.user_id == u.id).first()
    if membership:
        house = db.query(House).filter(House.id == membership.house_id).first()
        print(f"\nUser ID {u.id} ({u.username}):")
        print(f"  Linked to: House ID {membership.house_id} ({house.house_code if house else 'UNKNOWN'})")
        
        # Check payins for this user
        user_payins = db.query(PayinReport).filter(PayinReport.submitted_by_user_id == u.id).all()
        print(f"  Submitted payins: {len(user_payins)}")
        for p in user_payins:
            print(f"    - ID {p.id}: ฿{p.amount}, {p.status}")
    else:
        print(f"\nUser ID {u.id} ({u.username}): ❌ NOT LINKED TO ANY HOUSE")

db.close()
