#!/usr/bin/env python
"""
Simple script to create test users with plain text passwords for development
"""
import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.models.user import User

def create_simple_users():
    """Create users with plain text passwords for development testing"""
    with Session(engine) as db:
        print("🌱 Creating simple test users...")
        
        # Delete existing users for clean slate
        db.query(User).delete()
        
        # Create users with plain passwords (no hashing)
        users = [
            User(
                email="admin@moobaan.com",
                full_name="System Administrator", 
                phone="02-123-4567",
                hashed_password="admin123",  # Plain text for development
                role="super_admin",
                is_active=True
            ),
            User(
                email="accounting@moobaan.com",
                full_name="Accounting Manager",
                phone="02-234-5678", 
                hashed_password="acc123",  # Plain text for development
                role="accounting",
                is_active=True
            ),
            User(
                email="resident@moobaan.com",
                full_name="Test Resident",
                phone="02-345-6789",
                hashed_password="res123",  # Plain text for development
                role="resident",
                is_active=True
            )
        ]
        
        for user in users:
            db.add(user)
            print(f"✅ Created: {user.email} / {user.hashed_password}")
        
        db.commit()
        print("🎉 Simple users created successfully!")
        print("\n📝 Login with:")
        print("  admin@moobaan.com / admin123")
        print("  accounting@moobaan.com / acc123")
        print("  resident@moobaan.com / res123")

if __name__ == "__main__":
    create_simple_users()