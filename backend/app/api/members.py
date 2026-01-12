from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.models import Member as MemberSchema, MemberCreate
from app.db.models.house_member import HouseMember as HouseMemberModel
from app.db.models.house import House as HouseModel
from app.db.models.user import User as UserModel
from app.db.session import get_db
from app.core.deps import require_admin_or_accounting

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("", response_model=List[dict])
async def list_members(house_id: Optional[int] = None, db: Session = Depends(get_db), current_user: UserModel = require_admin_or_accounting):
    """List all members with optional house filter"""
    query = db.query(HouseMemberModel).options(
        joinedload(HouseMemberModel.house),
        joinedload(HouseMemberModel.user)
    )
    
    if house_id:
        query = query.filter(HouseMemberModel.house_id == house_id)
    
    house_members = query.all()
    
    return [{
        "id": hm.user.id,
        "house_id": hm.house_id,
        "house_number": hm.house.house_no,
        "name": hm.user.full_name,
        "phone": hm.user.phone,
        "email": hm.user.email,
        "role": hm.member_role,
        "created_at": hm.created_at
    } for hm in house_members]


@router.get("/{member_id}", response_model=dict)
async def get_member(member_id: int, db: Session = Depends(get_db), current_user: UserModel = require_admin_or_accounting):
    """Get a specific member by ID"""
    house_member = db.query(HouseMemberModel).options(
        joinedload(HouseMemberModel.house),
        joinedload(HouseMemberModel.user)
    ).filter(HouseMemberModel.user_id == member_id).first()
    
    if not house_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return {
        "id": house_member.user.id,
        "house_id": house_member.house_id,
        "house_number": house_member.house.house_no,
        "name": house_member.user.full_name,
        "phone": house_member.user.phone,
        "email": house_member.user.email,
        "role": house_member.member_role,
        "created_at": house_member.created_at
    }


@router.post("", response_model=dict)
async def create_member(member: MemberCreate, db: Session = Depends(get_db), current_user: UserModel = require_admin_or_accounting):
    """Create a new member"""
    from datetime import datetime
    
    # Check house exists
    house = db.query(HouseModel).filter(HouseModel.id == member.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Check member limit (max 3 per house)
    member_count = db.query(HouseMemberModel).filter(HouseMemberModel.house_id == member.house_id).count()
    if member_count >= 3:
        raise HTTPException(status_code=400, detail="House already has maximum 3 members")
    
    # Create user first (if not exists)
    existing_user = db.query(UserModel).filter(UserModel.email == member.email).first()
    if existing_user:
        # Check if user is already a member of this house
        existing_membership = db.query(HouseMemberModel).filter(
            HouseMemberModel.user_id == existing_user.id,
            HouseMemberModel.house_id == member.house_id
        ).first()
        if existing_membership:
            raise HTTPException(status_code=400, detail="User is already a member of this house")
        user = existing_user
    else:
        user = UserModel(
            email=member.email,
            full_name=member.name,
            phone=member.phone,
            hashed_password="",  # Placeholder - actual auth would handle this
            is_active=True,
            created_at=datetime.now()
        )
        db.add(user)
        db.flush()  # Get the user ID
    
    # Create house membership
    house_member = HouseMemberModel(
        house_id=member.house_id,
        user_id=user.id,
        member_role=member.role.value if hasattr(member.role, 'value') else member.role,
        created_at=datetime.now()
    )
    
    db.add(house_member)
    db.commit()
    db.refresh(house_member)
    
    return {
        "id": user.id,
        "house_id": house_member.house_id,
        "house_number": house.house_no,
        "name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "role": house_member.member_role,
        "created_at": house_member.created_at
    }


@router.put("/{member_id}", response_model=dict)
async def update_member(member_id: int, member_update: MemberCreate, db: Session = Depends(get_db), current_user: UserModel = require_admin_or_accounting):
    """Update an existing member"""
    house_member = db.query(HouseMemberModel).options(
        joinedload(HouseMemberModel.house),
        joinedload(HouseMemberModel.user)
    ).filter(HouseMemberModel.user_id == member_id).first()
    
    if not house_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check house exists if changing house
    if member_update.house_id != house_member.house_id:
        house = db.query(HouseModel).filter(HouseModel.id == member_update.house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="House not found")
        
        # Check member limit for new house
        member_count = db.query(HouseMemberModel).filter(HouseMemberModel.house_id == member_update.house_id).count()
        if member_count >= 3:
            raise HTTPException(status_code=400, detail="House already has maximum 3 members")
    
    # Update user info
    house_member.user.full_name = member_update.name
    house_member.user.phone = member_update.phone
    house_member.user.email = member_update.email
    
    # Update house membership
    house_member.house_id = member_update.house_id
    house_member.member_role = member_update.role.value if hasattr(member_update.role, 'value') else member_update.role
    
    db.commit()
    db.refresh(house_member)
    
    return {
        "id": house_member.user.id,
        "house_id": house_member.house_id,
        "house_number": house_member.house.house_no,
        "name": house_member.user.full_name,
        "phone": house_member.user.phone,
        "email": house_member.user.email,
        "role": house_member.member_role,
        "created_at": house_member.created_at
    }


@router.delete("/{member_id}")
async def delete_member(member_id: int, db: Session = Depends(get_db), current_user: UserModel = require_admin_or_accounting):
    """Delete a member"""
    house_member = db.query(HouseMemberModel).filter(HouseMemberModel.user_id == member_id).first()
    if not house_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db.delete(house_member)
    db.commit()
    
    return {"message": "Member deleted successfully"}
