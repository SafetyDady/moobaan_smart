from app.db.models.user import User
from app.db.session import SessionLocal
from app.core.auth import get_password_hash

db = SessionLocal()

user = db.query(User).filter(User.email == "resident@moobaan.com").first()

if user:
    # Set password to "password"
    user.hashed_password = get_password_hash("password")
    db.commit()
    print(f"✅ Password reset for {user.email}")
    print(f"   New password: password")
else:
    print("User not found!")

db.close()
