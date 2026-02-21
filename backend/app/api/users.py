from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.models.user import User
from app.db.models.house import House
from app.db.models.house_member import HouseMember
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipRole, ResidentMembershipStatus
from app.db.session import get_db
from app.core.deps import require_admin_or_accounting, get_current_user, require_roles
from app.core.auth import get_password_hash
from app.models import UserCreate
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/users", tags=["users"])

# Allowed staff roles (super_admin can only create these)
STAFF_ROLES = ["accounting", "admin"]


class StaffCreateRequest(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    role: str = Field(..., pattern="^(accounting|admin)$")
    phone: Optional[str] = None


def count_active_house_members(house_id: int, db: Session) -> int:
    """Count only ACTIVE house members (single source of truth for 3-member limit)"""
    return db.query(HouseMember).join(User).filter(
        HouseMember.house_id == house_id,
        User.is_active == True
    ).count()


# ========== Staff Management (super_admin only) ==========

@router.post("/staff")
async def create_staff_user(
    data: StaffCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin"]))
):
    """
    Create a staff user (accounting / admin). Super Admin only.
    """
    # Check duplicate email
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        phone=data.phone,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "message": f"Staff user '{data.email}' created with role '{data.role}'"
    }


@router.get("/staff")
async def list_staff_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin"]))
):
    """List all staff users (non-resident). Super Admin only."""
    staff = db.query(User).filter(User.role.in_(["super_admin", "accounting", "admin"])).all()
    return {
        "staff": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in staff
        ]
    }


@router.post("/staff/{user_id}/deactivate")
async def deactivate_staff(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin"]))
):
    """Deactivate a staff user. Super Admin only. Cannot deactivate yourself."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user = db.query(User).filter(User.id == user_id, User.role.in_(["accounting", "admin"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="Staff user not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Already inactive")
    user.is_active = False
    db.commit()
    return {"message": f"Staff '{user.email}' deactivated", "id": user.id}


@router.post("/staff/{user_id}/reactivate")
async def reactivate_staff(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin"]))
):
    """Reactivate a staff user. Super Admin only."""
    user = db.query(User).filter(User.id == user_id, User.role.in_(["accounting", "admin"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="Staff user not found")
    if user.is_active:
        raise HTTPException(status_code=400, detail="Already active")
    user.is_active = True
    db.commit()
    return {"message": f"Staff '{user.email}' reactivated", "id": user.id}


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)


@router.post("/staff/{user_id}/reset-password")
async def reset_staff_password(
    user_id: int,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin"]))
):
    """Reset a staff user's password. Super Admin only."""
    user = db.query(User).filter(User.id == user_id, User.role.in_(["super_admin", "accounting", "admin"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="Staff user not found")
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": f"Password reset for '{user.email}'", "id": user.id}


@router.get("/residents")
async def list_residents(
    house_id: Optional[int] = None,
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """List all resident users linked to houses"""
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    
    try:
        from sqlalchemy.orm import selectinload
        
        # Query HouseMembers with eager loading of User and House
        query = db.query(HouseMember).options(
            selectinload(HouseMember.user),
            selectinload(HouseMember.house)
        ).join(User).filter(User.role.in_(["owner", "resident", "tenant"]))
        
        # Apply filters
        if house_id:
            query = query.filter(HouseMember.house_id == house_id)
            
        if q:  # Search by email or full_name
            search = f"%{q}%"
            query = query.filter(
                (User.email.ilike(search)) | 
                (User.full_name.ilike(search))
            )
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        house_members = query.all()
        
        logger.info(f"Found {len(house_members)} house members")
        
        result = []
        for house_member in house_members:
            user = house_member.user
            house = house_member.house
            
            if user and house:  # Ensure both relationships are loaded
                result.append({
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "phone": user.phone,
                    "role": user.role,
                    "is_active": user.is_active,
                    "house": {
                        "id": house.id,
                        "house_code": house.house_code,
                        "house_status": house.house_status
                    },
                    "member_role": house_member.member_role,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                })
        
        logger.info(f"Returning {len(result)} residents")
        return {"residents": result, "total": len(result)}
        
    except Exception as e:
        logger.exception(f"Error listing residents: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve residents"
        )


@router.post("/residents")
async def create_resident(
    user_data: dict, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Create a new resident user linked to a house, OR add existing user to a new house.
    
    Phone number is the primary identifier:
    - If phone already exists → reuse existing user, add new membership to house
    - If phone is new → create new user + membership
    
    This allows one person (same phone) to be assigned to multiple houses.
    """
    
    # Extract data
    house_id = user_data.get("house_id")
    full_name = user_data.get("full_name")
    email = user_data.get("email")
    phone = user_data.get("phone")
    member_role = user_data.get("member_role", "resident")
    
    # Validate required fields — phone is required (key identifier for multi-house)
    if not house_id or not full_name or not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Missing required fields",
                "error_th": "กรุณากรอก บ้าน, ชื่อ-นามสกุล และเบอร์โทรศัพท์",
                "error_en": "house_id, full_name, and phone are required"
            }
        )
    
    # Normalize phone (strip spaces/dashes)
    phone = phone.strip().replace("-", "").replace(" ", "")
    
    # Check if house exists
    house = db.query(House).filter(House.id == house_id).first()
    if not house:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="House not found"
        )
    
    # Check member count limit (max 3 ACTIVE members per house)
    active_member_count = count_active_house_members(house_id, db)
    if active_member_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "House member limit exceeded",
                "error_th": "บ้านนี้มีสมาชิกที่ใช้งานครบ 3 คนแล้ว",
                "error_en": "Maximum 3 active members per house allowed",
                "current_count": active_member_count,
                "max_count": 3
            }
        )
    
    # Map member_role to ResidentMembershipRole
    role_mapping = {
        "owner": ResidentMembershipRole.OWNER,
        "family": ResidentMembershipRole.FAMILY,
        "resident": ResidentMembershipRole.OWNER,
        "tenant": ResidentMembershipRole.FAMILY,
    }
    membership_role = role_mapping.get(member_role.lower(), ResidentMembershipRole.OWNER)
    
    try:
        # ── Check if user with this phone already exists ──
        existing_user = db.query(User).filter(User.phone == phone).first()
        
        if existing_user:
            # ── EXISTING USER → add new house membership ──
            
            # Check if already has membership to this house
            existing_membership = db.query(ResidentMembership).filter(
                ResidentMembership.user_id == existing_user.id,
                ResidentMembership.house_id == house_id
            ).first()
            
            if existing_membership:
                if existing_membership.status == ResidentMembershipStatus.ACTIVE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "Already a member",
                            "error_th": f"เบอร์ {phone} ({existing_user.full_name}) เป็นสมาชิกบ้าน {house.house_code} อยู่แล้ว",
                            "error_en": f"Phone {phone} ({existing_user.full_name}) is already an active member of house {house.house_code}"
                        }
                    )
                else:
                    # Reactivate INACTIVE membership
                    existing_membership.status = ResidentMembershipStatus.ACTIVE
                    existing_membership.role = membership_role
                    existing_membership.deactivated_at = None
                    logger.info(f"Reactivated membership for user {existing_user.id} → house {house_id}")
            else:
                # Create new membership for existing user
                new_membership = ResidentMembership(
                    user_id=existing_user.id,
                    house_id=house_id,
                    role=membership_role,
                    status=ResidentMembershipStatus.ACTIVE
                )
                db.add(new_membership)
            
            # Also add to legacy house_members if not exists
            existing_hm = db.query(HouseMember).filter(
                HouseMember.user_id == existing_user.id,
                HouseMember.house_id == house_id
            ).first()
            if not existing_hm:
                house_member = HouseMember(
                    house_id=house_id,
                    user_id=existing_user.id,
                    member_role=member_role,
                    phone=phone
                )
                db.add(house_member)
            
            # Update name if provided and different
            if full_name and full_name != existing_user.full_name:
                existing_user.full_name = full_name
            if email and email != existing_user.email:
                # Check email uniqueness before updating
                email_taken = db.query(User).filter(User.email == email, User.id != existing_user.id).first()
                if not email_taken:
                    existing_user.email = email
            
            db.commit()
            
            # Count how many active houses this user has
            active_houses = db.query(ResidentMembership).filter(
                ResidentMembership.user_id == existing_user.id,
                ResidentMembership.status == ResidentMembershipStatus.ACTIVE
            ).count()
            
            return {
                "success": True,
                "existing_user": True,
                "user": {
                    "id": existing_user.id,
                    "email": existing_user.email,
                    "full_name": existing_user.full_name,
                    "phone": existing_user.phone,
                    "role": existing_user.role,
                    "house_id": house_id,
                    "active_houses_count": active_houses
                },
                "message": f"Existing user added to house {house.house_code}. Now has {active_houses} house(s).",
                "message_th": f"เพิ่ม {existing_user.full_name} (เบอร์ {phone}) เข้าบ้าน {house.house_code} สำเร็จ — ปัจจุบันมี {active_houses} บ้าน"
            }
        
        else:
            # ── NEW USER → create user + membership ──
            
            # Check email uniqueness (if provided)
            if email:
                email_exists = db.query(User).filter(User.email == email).first()
                if email_exists:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "Email already exists",
                            "error_th": "อีเมลนี้มีอยู่ในระบบแล้ว กรุณาใช้อีเมลอื่น",
                            "error_en": "This email is already registered"
                        }
                    )
            
            new_user = User(
                email=email or None,
                full_name=full_name,
                phone=phone,
                hashed_password=None,
                role="resident",
                is_active=True
            )
            
            db.add(new_user)
            db.flush()
            
            # Create house member (legacy)
            house_member = HouseMember(
                house_id=house_id,
                user_id=new_user.id,
                member_role=member_role,
                phone=phone
            )
            db.add(house_member)
            
            # Create resident membership
            resident_membership = ResidentMembership(
                user_id=new_user.id,
                house_id=house_id,
                role=membership_role,
                status=ResidentMembershipStatus.ACTIVE
            )
            db.add(resident_membership)
            
            db.commit()
            
            return {
                "success": True,
                "existing_user": False,
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "full_name": new_user.full_name,
                    "phone": new_user.phone,
                    "role": new_user.role,
                    "house_id": house_id
                },
                "message": "Resident created. User can login via LINE immediately.",
                "message_th": f"สร้างผู้อาศัย {full_name} สำเร็จ — เข้าสู่ระบบผ่าน LINE ได้ทันที"
            }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        db.rollback()
        logger.exception(f"Error creating/assigning resident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to create resident",
                "error_th": "ไม่สามารถสร้างผู้ใช้ได้",
                "error_en": str(e)
            }
        )




@router.get("/houses/{house_id}/member-count")
async def get_house_member_count(
    house_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """Get current member count for a house (active only)"""
    
    # Check if house exists
    house = db.query(House).filter(House.id == house_id).first()
    if not house:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="House not found"
        )
    
    # Count only active members
    active_member_count = count_active_house_members(house_id, db)
    
    return {
        "house_id": house_id,
        "house_code": house.house_code,
        "current_member_count": active_member_count,
        "max_member_count": 3,
        "available_slots": max(0, 3 - active_member_count)
    }


@router.patch("/{user_id}")
async def update_resident(
    user_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """Update resident profile (admin/accounting only)"""
    import logging
    import re
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    try:
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is a resident
        if user.role not in ["owner", "resident", "tenant"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a resident"
            )
        
        # Validate email if provided
        if "email" in update_data:
            email = update_data["email"].strip().lower()
            # Email format validation
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_en": "Invalid email format",
                        "error_th": "รูปแบบอีเมลไม่ถูกต้อง"
                    }
                )
            
            # Check email uniqueness
            existing_user = db.query(User).filter(User.email == email, User.id != user_id).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_en": "Email already exists",
                        "error_th": "อีเมลนี้มีอยู่แล้วในระบบ"
                    }
                )
            user.email = email
        
        # Update other user fields
        if "full_name" in update_data:
            if not update_data["full_name"].strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_en": "Full name is required",
                        "error_th": "ชื่อ-นามสกุลจำเป็นต้องระบุ"
                    }
                )
            user.full_name = update_data["full_name"].strip()
        
        if "phone" in update_data:
            user.phone = update_data["phone"].strip() if update_data["phone"] else None
            
        if "role" in update_data:
            # Validate role is still a resident role
            if update_data["role"] not in ["owner", "resident", "tenant"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role must be owner, resident, or tenant"
                )
            user.role = update_data["role"]
        
        # Handle house change with active member validation
        if "house_id" in update_data:
            new_house_id = update_data["house_id"]
            
            # Check if new house exists
            house = db.query(House).filter(House.id == new_house_id).first()
            if not house:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="House not found"
                )
            
            # Get current house_member record
            house_member = db.query(HouseMember).filter(HouseMember.user_id == user_id).first()
            if house_member:
                # Check member limit for new house (if different)
                if house_member.house_id != new_house_id:
                    # Count only active members in target house
                    active_count = db.query(HouseMember).join(User).filter(
                        HouseMember.house_id == new_house_id,
                        User.is_active == True
                    ).count()
                    
                    # If this user is active, they would count against the limit
                    if user.is_active and active_count >= 3:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "error_en": "Target house already has maximum 3 active members",
                                "error_th": "บ้านที่ต้องการย้ายไปมีสมาชิกครบ 3 คนแล้ว"
                            }
                        )
                    house_member.house_id = new_house_id
        
        # Update house member role if provided
        if "member_role" in update_data:
            house_member = db.query(HouseMember).filter(HouseMember.user_id == user_id).first()
            if house_member:
                house_member.member_role = update_data["member_role"]
        
        # Update timestamp
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Resident {user.id} updated by admin {current_user.id}")
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active
            }
        }
        
    except Exception as e:
        db.rollback()
        import logging
        logging.error(f"Error updating resident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resident"
        )


@router.post("/{user_id}/deactivate")
async def deactivate_resident(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """Deactivate a resident (soft delete)"""
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    try:
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is a resident
        if user.role not in ["owner", "resident", "tenant"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a resident"
            )
        
        # Already inactive
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already inactive"
            )
        
        # Deactivate user
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Resident {user.id} deactivated by admin {current_user.id}")
        
        return {
            "success": True,
            "message": "User deactivated successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating resident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate resident"
        )


@router.post("/{user_id}/reactivate")
async def reactivate_resident(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """Reactivate a resident (restore from soft delete)"""
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    try:
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is a resident
        if user.role not in ["owner", "resident", "tenant"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a resident"
            )
        
        # Already active
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active"
            )
        
        # Check member limit for user's house
        house_member = db.query(HouseMember).filter(HouseMember.user_id == user_id).first()
        if not house_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "HOUSE_MAPPING_MISSING",
                    "message_th": "ไม่พบข้อมูลการเชื่อมโยงบ้านของสมาชิกนี้",
                    "message_en": "House mapping not found for this resident"
                }
            )
        
        # Count only active members in the house
        active_count = count_active_house_members(house_member.house_id, db)
        
        if active_count >= 3:
            house = db.query(House).filter(House.id == house_member.house_id).first()
            house_code = house.house_code if house else str(house_member.house_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "HOUSE_MEMBER_LIMIT_REACHED",
                    "message_th": f"ไม่สามารถเปิดใช้งานสมาชิกได้ เนื่องจากบ้าน {house_code} มีสมาชิกใช้งานครบ 3 คนแล้ว",
                    "message_en": f"Cannot reactivate resident: house {house_code} already has 3 active members",
                    "house_code": house_code,
                    "max_active_members": 3
                }
            )
        
        # Reactivate user
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Resident {user.id} reactivated by admin {current_user.id}")
        
        return {
            "success": True,
            "message": "User reactivated successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active
            }
        }
        
    except HTTPException:
        # Re-raise HTTPException (don't catch our business logic errors)
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reactivating resident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate resident"
        )


# ============================================================
# Phase D.2: Resident Session Revocation
# ============================================================

def _mask_phone(phone: str) -> str:
    """Mask phone number for logging: 081****678"""
    if not phone or len(phone) < 7:
        return '****'
    return f"{phone[:3]}****{phone[-3:]}"


@router.post("/residents/{user_id}/revoke-session")
async def revoke_resident_session(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Phase D.2: Revoke all active sessions of a resident.
    
    This increments the user's session_version, which invalidates all
    existing JWT tokens for this user. The resident will need to
    re-login via OTP.
    
    - Only admin/accounting can revoke sessions
    - Only works for resident users (not admin/accounting)
    - Returns 404 if user not found
    - Returns 400 if user is not a resident
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Only allow revoking resident sessions
        if user.role not in ["resident", "owner", "tenant"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "NOT_RESIDENT",
                    "message_th": "สามารถบังคับออกจากระบบได้เฉพาะลูกบ้านเท่านั้น",
                    "message_en": "Can only force logout resident users"
                }
            )
        
        # Increment session_version to invalidate all existing tokens
        old_version = user.session_version
        user.session_version = old_version + 1
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        # Audit log (masked phone)
        masked_phone = _mask_phone(user.phone)
        logger.warning(
            f"[RESIDENT_SESSION_REVOKED] "
            f"user_id={user.id} phone={masked_phone} "
            f"old_version={old_version} new_version={user.session_version} "
            f"revoked_by={current_user.id}"
        )
        
        return {
            "success": True,
            "message": "All sessions revoked successfully",
            "message_th": "บังคับออกจากระบบสำเร็จ ลูกบ้านจะต้อง login ใหม่",
            "user_id": user.id,
            "session_version": user.session_version
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error revoking resident session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


# NOTE: reset-password endpoint REMOVED - Residents are OTP-only (Phase R cleanup)
