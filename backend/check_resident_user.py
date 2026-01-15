from app.db.models.user import User
from app.db.session import SessionLocal

db = SessionLocal()

user = db.query(User).filter(User.email == "resident@moobaan.com").first()

if user:
    print(f"User found: {user.email}")
    print(f"ID: {user.id}")
    print(f"Role: {user.role}")
    print(f"Active: {user.is_active}")
    print(f"Has password: {bool(user.hashed_password)}")
else:
    print("User not found!")

db.close()
