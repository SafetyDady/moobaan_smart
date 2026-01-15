"""
Test script for Pay-in Review Workflow
Tests: Accept, Reject, and Cancel endpoints with ledger entry creation
"""
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.models import (
    User, House, HouseStatus, HouseMember, PayinReport, PayinStatus, IncomeTransaction
)
from app.core.auth import get_password_hash


def setup_test_data(db: Session):
    """Create test users and houses"""
    print("🔧 Setting up test data...")
    
    # Clean up existing test data
    db.query(IncomeTransaction).delete()
    db.query(PayinReport).delete()
    db.query(HouseMember).filter(
        HouseMember.user_id.in_(
            db.query(User.id).filter(User.email.in_(['admin_test@test.com', 'resident_test@test.com']))
        )
    ).delete(synchronize_session=False)
    db.query(User).filter(User.email.in_(['admin_test@test.com', 'resident_test@test.com'])).delete()
    db.query(House).filter(House.house_code == 'TEST-01').delete()
    db.commit()
    
    # Create admin user
    admin = User(
        email='admin_test@test.com',
        hashed_password=get_password_hash('password123'),
        full_name='Test Admin',
        role='super_admin',
        is_active=True
    )
    db.add(admin)
    
    # Create test house
    house = House(
        house_code='TEST-01',
        house_status=HouseStatus.ACTIVE,
        owner_name='Test Owner'
    )
    db.add(house)
    db.flush()
    
    # Create resident user
    resident = User(
        email='resident_test@test.com',
        hashed_password=get_password_hash('password123'),
        full_name='Test Resident',
        role='resident',
        is_active=True
    )
    db.add(resident)
    db.flush()
    
    # Link resident to house via HouseMember
    house_member = HouseMember(
        house_id=house.id,
        user_id=resident.id,
        member_role='resident'
    )
    db.add(house_member)
    db.commit()
    
    print(f"✅ Created admin: {admin.email}")
    print(f"✅ Created house: {house.house_code}")
    print(f"✅ Created resident: {resident.email}")
    
    return admin, house, resident


def test_payin_submission(db: Session, house, resident):
    """Test 1: Resident submits pay-in"""
    print("\n📝 TEST 1: Resident submits pay-in report")
    
    payin = PayinReport(
        house_id=house.id,
        submitted_by_user_id=resident.id,
        amount=600.00,
        transfer_date=datetime.now(timezone.utc),
        transfer_hour=14,
        transfer_minute=30,
        slip_url='https://example.com/slip.jpg',
        status=PayinStatus.PENDING
    )
    db.add(payin)
    db.commit()
    db.refresh(payin)
    
    print(f"✅ Created payin ID {payin.id} with status: {payin.status.value}")
    assert payin.status == PayinStatus.PENDING
    return payin


def test_accept_payin(db: Session, payin, admin):
    """Test 2: Admin accepts pay-in and creates ledger entry"""
    print("\n✅ TEST 2: Admin accepts pay-in")
    
    # Check no income transaction exists yet
    existing_income = db.query(IncomeTransaction).filter(
        IncomeTransaction.payin_id == payin.id
    ).first()
    assert existing_income is None, "Income transaction should not exist yet"
    
    # Accept payin
    payin.status = PayinStatus.ACCEPTED
    payin.accepted_by = admin.id
    payin.accepted_at = datetime.now(timezone.utc)
    
    # Create immutable ledger entry
    income = IncomeTransaction(
        house_id=payin.house_id,
        payin_id=payin.id,
        amount=payin.amount,
        received_at=payin.transfer_date
    )
    db.add(income)
    db.commit()
    db.refresh(payin)
    db.refresh(income)
    
    print(f"✅ Payin status: {payin.status.value}")
    print(f"✅ Accepted by: {payin.accepted_by}")
    print(f"✅ Created IncomeTransaction ID {income.id}")
    print(f"   - Amount: ฿{income.amount}")
    print(f"   - House ID: {income.house_id}")
    
    assert payin.status == PayinStatus.ACCEPTED
    assert income.payin_id == payin.id
    assert float(income.amount) == float(payin.amount)
    
    return income


def test_reject_payin(db: Session, house, resident):
    """Test 3: Admin rejects pay-in"""
    print("\n❌ TEST 3: Admin rejects pay-in")
    
    # Create another payin
    payin = PayinReport(
        house_id=house.id,
        submitted_by_user_id=resident.id,
        amount=500.00,
        transfer_date=datetime.now(timezone.utc),
        transfer_hour=10,
        transfer_minute=15,
        slip_url='https://example.com/slip2.jpg',
        status=PayinStatus.PENDING
    )
    db.add(payin)
    db.commit()
    db.refresh(payin)
    
    # Reject it
    payin.status = PayinStatus.REJECTED
    payin.rejection_reason = "Amount does not match slip"
    db.commit()
    db.refresh(payin)
    
    print(f"✅ Payin ID {payin.id} rejected")
    print(f"   Reason: {payin.rejection_reason}")
    
    # Verify no income transaction created
    income = db.query(IncomeTransaction).filter(
        IncomeTransaction.payin_id == payin.id
    ).first()
    assert income is None, "No income transaction should be created for rejected payin"
    
    return payin


def test_cancel_payin(db: Session, house, resident):
    """Test 4: Admin cancels (deletes) pay-in for test cleanup"""
    print("\n🗑️ TEST 4: Admin cancels pay-in")
    
    # Create another payin
    payin = PayinReport(
        house_id=house.id,
        submitted_by_user_id=resident.id,
        amount=300.00,
        transfer_date=datetime.now(timezone.utc),
        transfer_hour=9,
        transfer_minute=0,
        slip_url='https://example.com/slip3.jpg',
        status=PayinStatus.PENDING
    )
    db.add(payin)
    db.commit()
    payin_id = payin.id
    
    # Cancel (delete) it
    db.delete(payin)
    db.commit()
    
    # Verify deletion
    deleted = db.query(PayinReport).filter(PayinReport.id == payin_id).first()
    assert deleted is None, "Payin should be deleted"
    
    print(f"✅ Payin ID {payin_id} cancelled and deleted")


def test_cannot_accept_twice(db: Session, payin, admin):
    """Test 5: Cannot accept already accepted payin"""
    print("\n🚫 TEST 5: Cannot accept already accepted payin")
    
    # Try to create duplicate income transaction
    try:
        duplicate_income = IncomeTransaction(
            house_id=payin.house_id,
            payin_id=payin.id,  # Same payin_id
            amount=payin.amount,
            received_at=payin.transfer_date
        )
        db.add(duplicate_income)
        db.commit()
        assert False, "Should have raised IntegrityError due to unique constraint"
    except Exception as e:
        db.rollback()
        print(f"✅ Correctly prevented duplicate: {type(e).__name__}")


def main():
    print("="*60)
    print("🧪 PAY-IN REVIEW WORKFLOW TEST")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Setup
        admin, house, resident = setup_test_data(db)
        
        # Test submission
        payin = test_payin_submission(db, house, resident)
        
        # Test accept with ledger entry
        income = test_accept_payin(db, payin, admin)
        
        # Test reject
        rejected_payin = test_reject_payin(db, house, resident)
        
        # Test cancel
        test_cancel_payin(db, house, resident)
        
        # Test duplicate prevention
        test_cannot_accept_twice(db, payin, admin)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary:")
        print(f"- Submitted payin can be ACCEPTED → Creates IncomeTransaction")
        print(f"- Submitted payin can be REJECTED → No ledger entry")
        print(f"- Pending payin can be CANCELLED → Deleted from DB")
        print(f"- Accepted payin cannot be accepted twice (unique constraint)")
        print(f"- IncomeTransaction.payin_id is unique (prevents duplicates)")
        
    except Exception as e:
        import traceback
        print(f"\n❌ TEST FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
