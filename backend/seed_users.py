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
        
        # Create users with fallback plain text passwords for development
        users_data = [
            {
                "email": "admin@moobaan.com",
                "full_name": "System Administrator",
                "password": "admin123",  # Plain text for development
                "role": "super_admin",
                "phone": "02-123-4567"
            },
            {
                "email": "accounting@moobaan.com", 
                "full_name": "Accounting Manager",
                "password": "acc123",  # Plain text for development
                "role": "accounting",
                "phone": "02-234-5678"
            },
            {
                "email": "resident@moobaan.com",
                "full_name": "Test Resident",
                "password": "res123",  # Plain text for development
                "role": "resident", 
                "phone": "02-345-6789"
            }
        ]
        
        # Create users with plain text passwords for development
        for user_data in users_data:
            try:
                hashed_password = get_password_hash(user_data["password"])
            except:
                # Fallback to plain text for development
                hashed_password = user_data["password"]
            
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                phone=user_data["phone"],
                hashed_password=hashed_password,
                role=user_data["role"],
                is_active=True
            )
            db.add(user)
            print(f"✅ Created user: {user_data['email']} ({user_data['role']})")
        
        db.commit()
        print("🎉 User seeding completed successfully!")


if __name__ == "__main__":
    seed_users()
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
        print(f"   📧 Resident: resident@moobaan.com / res123 (linked to house {test_house.house_code})")
        print()
        print("🚀 You can now test authentication!")

if __name__ == "__main__":
    try:
        seed_users()
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        import traceback
        traceback.print_exc()