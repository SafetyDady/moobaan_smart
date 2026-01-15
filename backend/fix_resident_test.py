from app.db.models.user import User
from app.db.models.house_member import HouseMember
from app.db.session import SessionLocal
from datetime import datetime

db = SessionLocal()

# Find resident_test@test.com
user = db.query(User).filter(User.email == "resident_test@test.com").first()

if user:
    print(f"Found user: {user.email} (ID: {user.id})")
    
    # Check if house_member exists
    existing = db.query(HouseMember).filter(HouseMember.user_id == user.id).first()
    if existing:
        print("House member already exists!")
    else:
        # Create house_member for house 28/1 (ID=3)
        house_member = HouseMember(
            house_id=3,
            user_id=user.id,
            member_role="owner",
            phone=user.phone,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(house_member)
        db.commit()
        print(f"✅ Created house_member: House 28/1 (ID=3) for user {user.email}")
else:
    print("User not found")

db.close()
