from app.db.models.user import User
from app.db.session import SessionLocal
from app.core.auth import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.email == "admin@moobaan.com").first()

if admin:
    admin.hashed_password = get_password_hash("password")
    db.commit()
    print("✅ Admin password reset to: password")
else:
    print("❌ Admin user not found")

db.close()
