#!/usr/bin/env python
"""
Script to seed initial users for authentication testing.
Run this after the authentication migration is complete.
"""
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.models.user import User
from app.db.models.house import House
from app.db.models.house_member import HouseMember
from app.core.auth import get_password_hash

def seed_users():
    """Create initial users for testing"""
    with Session(engine) as db:
        print("🌱 Seeding initial users...")
        
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"⚠️  Found {existing_users} existing users. Skipping seed.")
            return
        
        # Create Super Admin
        super_admin = User(
            email="admin@moobaan.com",
            full_name="Super Administrator",
            phone="090-123-4567",
            hashed_password=get_password_hash("admin123"),
            role="super_admin",
            is_active=True
        )
        db.add(super_admin)
        
        # Create Accounting user
        accounting = User(
            email="accounting@moobaan.com",
            full_name="Accounting Staff",
            phone="090-234-5678",
            hashed_password=get_password_hash("acc123"),
            role="accounting",
            is_active=True
        )
        db.add(accounting)
        
        # Create a test house first
        test_house = House(
            house_no="A-101",
            status="active",
            floor_area=120.5,
            land_area=200.0,
            zone="A",
            notes="Test house for resident user"
        )
        db.add(test_house)
        db.flush()  # Get the house ID
        
        # Create Resident user
        resident = User(
            email="resident@moobaan.com",
            full_name="Test Resident",
            phone="090-345-6789",
            hashed_password=get_password_hash("res123"),
            role="resident",
            is_active=True
        )
        db.add(resident)
        db.flush()  # Get the user ID
        
        # Link resident to house
        house_member = HouseMember(
            house_id=test_house.id,
            user_id=resident.id,
            member_role="owner"
        )
        db.add(house_member)
        
        db.commit()
        
        print("✅ Successfully created users:")
        print(f"   📧 Super Admin: admin@moobaan.com / admin123")
        print(f"   📧 Accounting: accounting@moobaan.com / acc123") 
        print(f"   📧 Resident: resident@moobaan.com / res123 (linked to house {test_house.house_no})")
        print()
        print("🚀 You can now test authentication!")

if __name__ == "__main__":
    try:
        seed_users()
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        import traceback
        traceback.print_exc()