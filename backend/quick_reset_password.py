"""Quick password reset without importing auth module"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.models.user import User
from app.db.session import SessionLocal
from passlib.context import CryptContext

# Create password context (same as in auth.py)
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def reset_admin_password(new_password="Admin123!"):
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@moobaan.com").first()
        
        if admin:
            # Hash password
            if len(new_password.encode('utf-8')) > 72:
                new_password = new_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
            
            admin.hashed_password = pwd_context.hash(new_password)
            db.commit()
            
            print("=" * 50)
            print("Password Reset Successful!")
            print("=" * 50)
            print(f"Email: admin@moobaan.com")
            print(f"Password: {new_password}")
            print("=" * 50)
            return True
        else:
            print("ERROR: Admin user not found")
            return False
            
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
