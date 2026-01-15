from app.db.models.user import User
from app.db.session import SessionLocal

db = SessionLocal()

# Delete resident_test@test.com
user = db.query(User).filter(User.email == "resident_test@test.com").first()

if user:
    print(f"Deleting user: {user.email} (ID: {user.id})")
    db.delete(user)
    db.commit()
    print("✅ User deleted")
else:
    print("User not found")

db.close()
