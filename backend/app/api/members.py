from fastapi import APIRouter, HTTPException
from typing import List
from app.models import Member, MemberCreate
from app.mock_data import MOCK_MEMBERS, MOCK_HOUSES

router = APIRouter(prefix="/api/members", tags=["members"])

# In-memory storage
members_db = list(MOCK_MEMBERS)
next_id = max([m.id for m in members_db]) + 1


@router.get("", response_model=List[Member])
async def list_members(house_id: int = None):
    """List all members with optional house filter"""
    result = members_db
    if house_id:
        result = [m for m in result if m.house_id == house_id]
    return result


@router.get("/{member_id}", response_model=Member)
async def get_member(member_id: int):
    """Get a specific member by ID"""
    member = next((m for m in members_db if m.id == member_id), None)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.post("", response_model=Member)
async def create_member(member: MemberCreate):
    """Create a new member"""
    global next_id
    from datetime import datetime
    
    # Check house exists
    house = next((h for h in MOCK_HOUSES if h.id == member.house_id), None)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Check member limit (max 3 per house)
    house_members = [m for m in members_db if m.house_id == member.house_id]
    if len(house_members) >= 3:
        raise HTTPException(status_code=400, detail="House already has maximum 3 members")
    
    new_member = Member(
        id=next_id,
        house_id=member.house_id,
        house_number=house.house_number,
        name=member.name,
        phone=member.phone,
        email=member.email,
        role=member.role,
        created_at=datetime.now()
    )
    members_db.append(new_member)
    next_id += 1
    return new_member


@router.put("/{member_id}", response_model=Member)
async def update_member(member_id: int, member: MemberCreate):
    """Update an existing member"""
    existing = next((m for m in members_db if m.id == member_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check house exists
    house = next((h for h in MOCK_HOUSES if h.id == member.house_id), None)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    existing.house_id = member.house_id
    existing.house_number = house.house_number
    existing.name = member.name
    existing.phone = member.phone
    existing.email = member.email
    existing.role = member.role
    return existing


@router.delete("/{member_id}")
async def delete_member(member_id: int):
    """Delete a member"""
    global members_db
    member = next((m for m in members_db if m.id == member_id), None)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    members_db = [m for m in members_db if m.id != member_id]
    return {"message": "Member deleted successfully"}
