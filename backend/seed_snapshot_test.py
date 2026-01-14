"""
Seed data for testing month-end snapshot calculation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from datetime import datetime, date, timedelta
from app.db.session import SessionLocal
from app.db.models import House, HouseStatus, Invoice, InvoiceStatus, IncomeTransaction, CreditNote, User, PayinReport, PayinStatus


def seed_test_data():
    """Create test data for snapshot testing"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("🌱 Seeding test data for month-end snapshot")
        print("=" * 80)
        
        # Get admin user
        admin = db.query(User).filter(User.role == "super_admin").first()
        if not admin:
            print("❌ No super_admin user found. Run simple_seed.py first.")
            return
        
        # Get or create test houses
        print("\n1️⃣ Getting test houses...")
        houses = db.query(House).filter(House.house_code.in_(['28/1', '28/2', '28/3'])).all()
        
        # Create houses if they don't exist
        if len(houses) < 3:
            existing_codes = [h.house_code for h in houses]
            for i in range(1, 4):
                code = f"28/{i}"
                if code not in existing_codes:
                    house = House(
                        house_code=code,
                        house_status=HouseStatus.ACTIVE,
                        owner_name=f"Test Owner {i}",
                        floor_area=Decimal("120.0"),
                        land_area=Decimal("100.0")
                    )
                    db.add(house)
                    houses.append(house)
            
            db.commit()
            houses = db.query(House).filter(House.house_code.in_(['28/1', '28/2', '28/3'])).all()
        
        print(f"✅ Using {len(houses)} houses: {', '.join([h.house_code for h in houses])}")
        
        # Create invoices for November 2024 (opening balance)
        print("\n2️⃣ Creating November 2024 invoices (for opening balance)...")
        nov_invoices = []
        for house in houses:
            invoice = Invoice(
                house_id=house.id,
                cycle_year=2024,
                cycle_month=11,
                issue_date=date(2024, 11, 1),
                due_date=date(2024, 11, 30),
                total_amount=Decimal("600.00"),
                status=InvoiceStatus.ISSUED,
                created_by=admin.id,
                notes="November invoice for testing"
            )
            db.add(invoice)
            nov_invoices.append(invoice)
        
        db.commit()
        print(f"✅ Created {len(nov_invoices)} November invoices")
        
        # Create December 2024 invoices (target month)
        print("\n3️⃣ Creating December 2024 invoices (target month)...")
        dec_invoices = []
        for house in houses:
            invoice = Invoice(
                house_id=house.id,
                cycle_year=2024,
                cycle_month=12,
                issue_date=date(2024, 12, 1),
                due_date=date(2024, 12, 31),
                total_amount=Decimal("600.00"),
                status=InvoiceStatus.ISSUED,
                created_by=admin.id,
                notes="December invoice for testing"
            )
            db.add(invoice)
            dec_invoices.append(invoice)
        
        db.commit()
        print(f"✅ Created {len(dec_invoices)} December invoices")
        
        # Create payments for house 1 (November payment)
        print("\n4️⃣ Creating test payments...")
        
        # Payment 1: November payment for house 1
        payin1 = PayinReport(
            house_id=houses[0].id,
            amount=Decimal("600.00"),
            transfer_date=datetime(2024, 11, 15, 10, 0, 0),
            transfer_hour=10,
            transfer_minute=0,
            slip_url="test_slip_1.jpg",
            status=PayinStatus.ACCEPTED,
            accepted_by=admin.id,
            accepted_at=datetime(2024, 11, 15, 15, 0, 0),
            submitted_by_user_id=admin.id
        )
        db.add(payin1)
        db.flush()
        
        income1 = IncomeTransaction(
            house_id=houses[0].id,
            payin_id=payin1.id,
            amount=Decimal("600.00"),
            received_at=datetime(2024, 11, 15, 10, 0, 0)
        )
        db.add(income1)
        
        # Payment 2: December payment for house 1
        payin2 = PayinReport(
            house_id=houses[0].id,
            amount=Decimal("300.00"),
            transfer_date=datetime(2024, 12, 10, 14, 0, 0),
            transfer_hour=14,
            transfer_minute=0,
            slip_url="test_slip_2.jpg",
            status=PayinStatus.ACCEPTED,
            accepted_by=admin.id,
            accepted_at=datetime(2024, 12, 10, 16, 0, 0),
            submitted_by_user_id=admin.id
        )
        db.add(payin2)
        db.flush()
        
        income2 = IncomeTransaction(
            house_id=houses[0].id,
            payin_id=payin2.id,
            amount=Decimal("300.00"),
            received_at=datetime(2024, 12, 10, 14, 0, 0)
        )
        db.add(income2)
        
        db.commit()
        print("✅ Created 2 payments for house 1")
        
        # Create credit note for house 2 (December)
        print("\n5️⃣ Creating test credit notes...")
        credit = CreditNote(
            house_id=houses[1].id,
            amount=Decimal("100.00"),
            reason="Test discount for December",
            reference="TEST-CN-001",
            created_by=admin.id,
            created_at=datetime(2024, 12, 5, 10, 0, 0)
        )
        db.add(credit)
        db.commit()
        print("✅ Created 1 credit note for house 2")
        
        print("\n" + "=" * 80)
        print("✅ Test data seeded successfully!")
        print("=" * 80)
        print("\nExpected Results for December 2024:")
        print("\nHouse 28/1:")
        print("  - Opening Balance: 600.00 (Nov invoice) - 600.00 (Nov payment) = 0.00")
        print("  - Invoice Total: 600.00 (Dec invoice)")
        print("  - Payment Total: 300.00 (Dec payment)")
        print("  - Credit Total: 0.00")
        print("  - Closing Balance: 0.00 + 600.00 - 300.00 - 0.00 = 300.00")
        
        print("\nHouse 28/2:")
        print("  - Opening Balance: 600.00 (Nov invoice)")
        print("  - Invoice Total: 600.00 (Dec invoice)")
        print("  - Payment Total: 0.00")
        print("  - Credit Total: 100.00 (Dec credit)")
        print("  - Closing Balance: 600.00 + 600.00 - 0.00 - 100.00 = 1100.00")
        
        print("\nHouse 28/3:")
        print("  - Opening Balance: 600.00 (Nov invoice)")
        print("  - Invoice Total: 600.00 (Dec invoice)")
        print("  - Payment Total: 0.00")
        print("  - Credit Total: 0.00")
        print("  - Closing Balance: 600.00 + 600.00 - 0.00 - 0.00 = 1200.00")
        
        print("\nAggregated:")
        print("  - Total Houses: 3")
        print("  - Closing Balance: 300.00 + 1100.00 + 1200.00 = 2600.00")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_data()
