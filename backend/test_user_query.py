"""
Test User query to see if it triggers relationship errors
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("🔍 Testing User query...")

try:
    from app.db.session import SessionLocal
    from app.db.models import User
    
    db = SessionLocal()
    print("✅ DB session created")
    
    # This is what authenticate_user does
    user = db.query(User).filter(User.email == "admin@moobaan.com").first()
    print(f"✅ Query executed: {user.email if user else 'No user found'}")
    
    db.close()
    print("\n🎯 User query works!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
