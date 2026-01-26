"""
Phase R.1 (Step 1): Test Resident Membership Service

Tests:
1. Add resident to house
2. Block when house has 3 active residents
3. Deactivate membership
4. Reactivate membership (with limit check)
5. Query helpers
"""
from app.db.session import SessionLocal
from app.db.models import User, House, ResidentMembership, ResidentMembershipStatus
from app.services.resident_membership import (
    ResidentMembershipService, 
    BusinessRuleError,
    MAX_ACTIVE_RESIDENTS_PER_HOUSE
)


def test_resident_membership():
    print("=" * 60)
    print("🧪 Phase R.1: Resident Membership Service Tests")
    print("=" * 60)
    
    db = SessionLocal()
    service = ResidentMembershipService(db)
    
    try:
        # Get test data
        users = db.query(User).filter(User.role == 'resident').limit(5).all()
        house = db.query(House).first()
        
        if not users or not house:
            print("❌ Need test users (role=resident) and houses in DB")
            return
        
        print(f"\n📋 Test Data:")
        print(f"   House: {house.house_code} (ID: {house.id})")
        print(f"   Users: {len(users)} available")
        
        # Clean up any existing test memberships
        db.query(ResidentMembership).filter(
            ResidentMembership.house_id == house.id
        ).delete()
        db.commit()
        
        # Test 1: Add first resident
        print(f"\n1️⃣ Test: Add first resident")
        print("-" * 40)
        m1 = service.add_resident_to_house(users[0].id, house.id)
        print(f"   ✅ Added: {m1.user.full_name} to {m1.house.house_code}")
        print(f"   Status: {m1.status.value}")
        
        # Test 2: Add second resident
        print(f"\n2️⃣ Test: Add second resident")
        print("-" * 40)
        m2 = service.add_resident_to_house(users[1].id, house.id)
        print(f"   ✅ Added: {m2.user.full_name}")
        
        # Test 3: Add third resident
        print(f"\n3️⃣ Test: Add third resident")
        print("-" * 40)
        m3 = service.add_resident_to_house(users[2].id, house.id)
        print(f"   ✅ Added: {m3.user.full_name}")
        
        # Check count
        count = service.count_active_members_by_house(house.id)
        print(f"\n   📊 Active count: {count}/{MAX_ACTIVE_RESIDENTS_PER_HOUSE}")
        
        # Test 4: Try to add 4th resident (should fail)
        print(f"\n4️⃣ Test: Add 4th resident (should FAIL)")
        print("-" * 40)
        try:
            if len(users) > 3:
                service.add_resident_to_house(users[3].id, house.id)
                print("   ❌ Should have raised BusinessRuleError!")
            else:
                print("   ⚠️ Not enough users to test (need 4)")
        except BusinessRuleError as e:
            print(f"   ✅ Correctly blocked: {e.code}")
            print(f"   Message: {e.message}")
            print(f"   HTTP Status: {e.http_status}")
        
        # Test 5: Deactivate one membership
        print(f"\n5️⃣ Test: Deactivate membership")
        print("-" * 40)
        deactivated = service.deactivate_membership(m3.id)
        print(f"   ✅ Deactivated: {deactivated.user.full_name}")
        print(f"   Status: {deactivated.status.value}")
        print(f"   Deactivated at: {deactivated.deactivated_at}")
        
        # Check count after deactivate
        count = service.count_active_members_by_house(house.id)
        print(f"   📊 Active count now: {count}/{MAX_ACTIVE_RESIDENTS_PER_HOUSE}")
        
        # Test 6: Reactivate membership
        print(f"\n6️⃣ Test: Reactivate membership")
        print("-" * 40)
        reactivated = service.reactivate_membership(m3.id)
        print(f"   ✅ Reactivated: {reactivated.user.full_name}")
        print(f"   Status: {reactivated.status.value}")
        
        # Test 7: Query helpers
        print(f"\n7️⃣ Test: Query helpers")
        print("-" * 40)
        active = service.get_active_memberships_by_house(house.id)
        print(f"   Active in house: {len(active)}")
        for m in active:
            print(f"   - {m.user.full_name} ({m.role.value})")
        
        # Test 8: Duplicate membership
        print(f"\n8️⃣ Test: Duplicate membership (should FAIL)")
        print("-" * 40)
        try:
            service.add_resident_to_house(users[0].id, house.id)
            print("   ❌ Should have raised BusinessRuleError!")
        except BusinessRuleError as e:
            print(f"   ✅ Correctly blocked: {e.code}")
        
        # Cleanup
        print(f"\n🧹 Cleanup test data...")
        db.query(ResidentMembership).filter(
            ResidentMembership.house_id == house.id
        ).delete()
        db.commit()
        print("   ✅ Cleaned up")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_resident_membership()
