#!/usr/bin/env python3
"""Delete admin_test user"""
from app.db.session import SessionLocal
from app.db.models.user import User

db = SessionLocal()

try:
    # Find admin_test
    user = db.query(User).filter(User.email == 'admin_test@moobaan.com').first()
    
    if user:
        print(f"Found user: ID {user.id}, Email: {user.email}, Role: {user.role}")
        db.delete(user)
        db.commit()
        print("✅ Deleted admin_test user")
    else:
        print("❌ admin_test user not found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
