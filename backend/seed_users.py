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
        
        # Create admin/accounting users only (residents are OTP-only, created by admin)
        users_data = [
            {
                "email": "admin@moobaan.com",
                "full_name": "System Administrator",
                "password": "admin123",
                "role": "super_admin",
                "phone": "02-123-4567"
            },
            {
                "email": "accounting@moobaan.com", 
                "full_name": "Accounting Manager",
                "password": "acc123",
                "role": "accounting",
                "phone": "02-234-5678"
            }
            # NOTE: Resident seed removed - residents are OTP-only (Phase R cleanup)
            # Residents are created by Admin via /api/users/residents
        ]
        
        # Create users with hashed passwords
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
        print("\n📝 Note: Residents are OTP-only. Create residents via Admin UI.")


if __name__ == "__main__":
    try:
        seed_users()
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        import traceback
        traceback.print_exc()