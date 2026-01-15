from app.db.models.user import User
from app.db.models.house_member import HouseMember
from app.db.models.house import House
from app.db.session import SessionLocal

db = SessionLocal()

# Check all users
users = db.query(User).all()

print("=== All Users ===")
for user in users:
    print(f"\nID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Name: {user.full_name}")
    print(f"Role: {user.role}")
    
    if user.role == "resident":
        house_member = db.query(HouseMember).filter(HouseMember.user_id == user.id).first()
        if house_member:
            house = db.query(House).filter(House.id == house_member.house_id).first()
            print(f"  → House: {house.house_code if house else 'N/A'} (ID: {house_member.house_id})")
        else:
            print(f"  → ❌ No house assigned")

db.close()
