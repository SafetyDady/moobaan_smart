#!/usr/bin/env python3
"""Direct test of authentication logic without HTTP layer"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models.user import User
from app.core.auth import verify_password, authenticate_user
from app.core.config import settings

# Create database session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=" * 80)
print("TESTING AUTHENTICATION LOGIC")
print("=" * 80)

# Test 1: Get user from database
print("\n1. Getting user from database...")
user = db.query(User).filter(User.email == "admin@moobaan.com").first()
if user:
    print(f"   ✅ User found: {user.email}")
    print(f"   - ID: {user.id}")
    print(f"   - Role: {user.role}")
    print(f"   - Active: {user.is_active}")
    print(f"   - Hash: {user.hashed_password[:50]}...")
else:
    print("   ❌ User NOT found!")
    db.close()
    sys.exit(1)

# Test 2: Direct password verification
print("\n2. Testing direct password verification...")
test_password = "Admin123!"
print(f"   Testing password: '{test_password}'")
result = verify_password(test_password, user.hashed_password)
print(f"   Result: {result}")
if result:
    print("   ✅ Password verification PASSED")
else:
    print("   ❌ Password verification FAILED")

# Test 3: Full authenticate_user function
print("\n3. Testing authenticate_user() function...")
auth_result = authenticate_user("admin@moobaan.com", test_password, db)
if auth_result:
    print(f"   ✅ authenticate_user() PASSED")
    print(f"   - User: {auth_result.email}")
    print(f"   - Role: {auth_result.role}")
else:
    print(f"   ❌ authenticate_user() FAILED")
    print(f"   - Result: {auth_result}")

# Test 4: Test with wrong password
print("\n4. Testing with wrong password...")
wrong_result = authenticate_user("admin@moobaan.com", "WrongPassword", db)
if wrong_result:
    print(f"   ❌ Wrong password ACCEPTED (should fail!)")
else:
    print(f"   ✅ Wrong password REJECTED (correct)")

db.close()
print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
