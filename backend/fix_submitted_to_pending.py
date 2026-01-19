"""
Fix existing SUBMITTED pay-ins to PENDING
Per A.1.2.2 spec: Resident must be able to edit before admin acceptance
"""
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.db.models.payin_report import PayinReport, PayinStatus

def main():
    db = SessionLocal()
    try:
        # Find all SUBMITTED pay-ins
        submitted = db.query(PayinReport).filter(
            PayinReport.status == PayinStatus.SUBMITTED
        ).all()
        
        print(f"Found {len(submitted)} SUBMITTED pay-ins")
        
        if len(submitted) == 0:
            print("No pay-ins to fix")
            return
        
        # Show what will be changed
        for p in submitted:
            print(f"  ID={p.id}, house_id={p.house_id}, status={p.status.value}")
        
        # Confirm
        confirm = input("\nChange all to PENDING? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted")
            return
        
        # Update to PENDING
        count = db.query(PayinReport).filter(
            PayinReport.status == PayinStatus.SUBMITTED
        ).update({PayinReport.status: PayinStatus.PENDING})
        
        db.commit()
        print(f"\n✅ Updated {count} pay-ins from SUBMITTED to PENDING")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
