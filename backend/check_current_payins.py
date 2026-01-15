#!/usr/bin/env python3
"""Check current payin reports"""
from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport
from app.db.models.house import House

db = SessionLocal()

payins = db.query(PayinReport).order_by(PayinReport.id).all()
print(f"Total payin reports: {len(payins)}\n")

for p in payins:
    house = db.query(House).filter(House.id == p.house_id).first()
    print(f"ID {p.id}:")
    print(f"  House: {house.house_code if house else 'UNKNOWN'} (ID {p.house_id})")
    print(f"  Amount: ฿{p.amount}")
    print(f"  Status: {p.status}")
    print(f"  Transfer: {p.transfer_date} {p.transfer_hour:02d}:{p.transfer_minute:02d}")
    print()

db.close()
