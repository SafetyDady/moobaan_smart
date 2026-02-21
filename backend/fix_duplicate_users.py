"""
Fix duplicate users in production.

Problem: user_id=6 and user_id=17 have the same phone (0635162459)
- user_id=6: has LINE linked, house 28/73 (created Feb 13)
- user_id=17: no LINE, house 28/72 (created Feb 21)

Solution:
1. Transfer user_id=17's ResidentMembership (house 28/72) → user_id=6
2. Transfer user_id=17's HouseMember (house 28/72) → user_id=6
3. Deactivate user_id=17

Run: python fix_duplicate_users.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.db.models.user import User
from app.db.models.house_member import HouseMember
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus

PHONE = "0635162459"
KEEP_USER_ID = 6       # Has LINE linked
REMOVE_USER_ID = 17    # Duplicate, no LINE

def fix():
    db = SessionLocal()
    try:
        # Verify both users exist with same phone
        keep_user = db.query(User).filter(User.id == KEEP_USER_ID).first()
        remove_user = db.query(User).filter(User.id == REMOVE_USER_ID).first()
        
        if not keep_user or not remove_user:
            print(f"ERROR: Users not found. keep={keep_user}, remove={remove_user}")
            return
        
        if keep_user.phone != PHONE or remove_user.phone != PHONE:
            print(f"ERROR: Phone mismatch!")
            print(f"  keep_user phone: {keep_user.phone}")
            print(f"  remove_user phone: {remove_user.phone}")
            return
        
        print(f"=== Fixing duplicate users for phone {PHONE} ===")
        print(f"  KEEP: user_id={KEEP_USER_ID} ({keep_user.full_name}), LINE={keep_user.line_user_id is not None}")
        print(f"  REMOVE: user_id={REMOVE_USER_ID} ({remove_user.full_name}), LINE={remove_user.line_user_id is not None}")
        
        # Step 1: Transfer ResidentMembership records
        memberships = db.query(ResidentMembership).filter(
            ResidentMembership.user_id == REMOVE_USER_ID
        ).all()
        
        for m in memberships:
            # Check if KEEP user already has membership for this house
            existing = db.query(ResidentMembership).filter(
                ResidentMembership.user_id == KEEP_USER_ID,
                ResidentMembership.house_id == m.house_id
            ).first()
            
            if existing:
                print(f"  ResidentMembership: house {m.house_id} already exists for user {KEEP_USER_ID}, deleting duplicate")
                db.delete(m)
            else:
                print(f"  ResidentMembership: transferring house {m.house_id} from user {REMOVE_USER_ID} → {KEEP_USER_ID}")
                m.user_id = KEEP_USER_ID
        
        # Step 2: Transfer HouseMember records (legacy)
        house_members = db.query(HouseMember).filter(
            HouseMember.user_id == REMOVE_USER_ID
        ).all()
        
        for hm in house_members:
            existing = db.query(HouseMember).filter(
                HouseMember.user_id == KEEP_USER_ID,
                HouseMember.house_id == hm.house_id
            ).first()
            
            if existing:
                print(f"  HouseMember: house {hm.house_id} already exists for user {KEEP_USER_ID}, deleting duplicate")
                db.delete(hm)
            else:
                print(f"  HouseMember: transferring house {hm.house_id} from user {REMOVE_USER_ID} → {KEEP_USER_ID}")
                hm.user_id = KEEP_USER_ID
        
        # Step 3: Deactivate the duplicate user
        print(f"  Deactivating user {REMOVE_USER_ID}")
        remove_user.is_active = False
        
        db.commit()
        
        # Verify result
        final_memberships = db.query(ResidentMembership).filter(
            ResidentMembership.user_id == KEEP_USER_ID,
            ResidentMembership.status == ResidentMembershipStatus.ACTIVE
        ).all()
        
        print(f"\n=== Result ===")
        print(f"  User {KEEP_USER_ID} now has {len(final_memberships)} active house(s):")
        for m in final_memberships:
            print(f"    - house_id={m.house_id}, role={m.role}, status={m.status}")
        print(f"  User {REMOVE_USER_ID} is_active={remove_user.is_active}")
        print("  Done!")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix()
