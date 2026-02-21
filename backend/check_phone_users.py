"""Quick script to check users + memberships for a phone number on production"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text

# Use production DATABASE_URL from environment or .env
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    # Try to load from .env
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    print("ERROR: Set DATABASE_URL environment variable")
    sys.exit(1)

# Fix scheme
if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)

PHONE = "0635162459"

with engine.connect() as conn:
    print(f"\n{'='*60}")
    print(f"  Checking phone: {PHONE}")
    print(f"{'='*60}")
    
    # 1. Find all users with this phone
    print(f"\n--- Users with phone {PHONE} ---")
    users = conn.execute(text("""
        SELECT id, full_name, email, phone, role, is_active, line_user_id,
               created_at
        FROM users 
        WHERE phone = :phone
        ORDER BY id
    """), {"phone": PHONE}).fetchall()
    
    if not users:
        print("  (none found)")
    for u in users:
        print(f"  User ID={u.id}, name='{u.full_name}', email='{u.email}', "
              f"role={u.role}, active={u.is_active}, "
              f"line_id={'YES' if u.line_user_id else 'NO'}, "
              f"created={u.created_at}")
    
    user_ids = [u.id for u in users]
    
    # 2. Check resident_memberships for all these user_ids
    if user_ids:
        print(f"\n--- ResidentMemberships for user_ids {user_ids} ---")
        memberships = conn.execute(text("""
            SELECT rm.id, rm.user_id, rm.house_id, h.house_code, 
                   rm.status, rm.role, rm.created_at, rm.deactivated_at
            FROM resident_memberships rm
            JOIN houses h ON h.id = rm.house_id
            WHERE rm.user_id = ANY(:ids)
            ORDER BY rm.user_id, rm.house_id
        """), {"ids": user_ids}).fetchall()
        
        if not memberships:
            print("  (none found)")
        for m in memberships:
            print(f"  Membership: user_id={m.user_id} → house {m.house_code} (house_id={m.house_id}), "
                  f"status={m.status}, role={m.role}, created={m.created_at}")
    
    # 3. Check legacy house_members
    if user_ids:
        print(f"\n--- Legacy HouseMembers for user_ids {user_ids} ---")
        hm = conn.execute(text("""
            SELECT hm.id, hm.user_id, hm.house_id, h.house_code, 
                   hm.member_role, hm.phone
            FROM house_members hm
            JOIN houses h ON h.id = hm.house_id
            WHERE hm.user_id = ANY(:ids)
            ORDER BY hm.user_id, hm.house_id
        """), {"ids": user_ids}).fetchall()
        
        if not hm:
            print("  (none found)")
        for m in hm:
            print(f"  HouseMember: user_id={m.user_id} → house {m.house_code} (house_id={m.house_id}), "
                  f"role={m.member_role}, phone={m.phone}")
    
    # 4. Summary
    print(f"\n--- Summary ---")
    print(f"  Total users with phone {PHONE}: {len(users)}")
    print(f"  User IDs: {user_ids}")
    if len(users) > 1:
        print(f"  ⚠️  DUPLICATE USERS! Same phone has {len(users)} separate user records")
        line_users = [u for u in users if u.line_user_id]
        if line_users:
            print(f"  LINE linked to user_id: {[u.id for u in line_users]}")
        no_line = [u for u in users if not u.line_user_id]
        if no_line:
            print(f"  No LINE link: user_id: {[u.id for u in no_line]}")
    
    print()
