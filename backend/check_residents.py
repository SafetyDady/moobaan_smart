from app.db.models.user import User
from app.db.models.house_member import HouseMember
from app.db.models.house import House
from app.db.session import SessionLocal

db = SessionLocal()

# Find all resident users
residents = db.query(User).filter(User.role == "resident").all()

print("=== Resident Users ===")
for user in residents:
    print(f"\nUser ID: {user.id}, Email: {user.email}, Name: {user.full_name}")
    
    # Check house_member
    house_member = db.query(HouseMember).filter(HouseMember.user_id == user.id).first()
    if house_member:
        print(f"  House Member ID: {house_member.id}, House ID: {house_member.house_id}")
        
        # Get house
        house = db.query(House).filter(House.id == house_member.house_id).first()
        if house:
            print(f"  House Code: {house.house_code}")
        else:
            print(f"  ❌ House not found for ID {house_member.house_id}")
    else:
        print(f"  ❌ No house_member record found")

db.close()
