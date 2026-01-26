"""
Phase R.1 (Step 1): Resident Membership Service

Business Rules:
- Max 3 ACTIVE residents per house
- Deactivate/Reactivate with limit check
- Query helpers for membership data

IMPORTANT:
- NO accounting logic
- NO pay-in logic
- NO auth changes
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional

from app.db.models.resident_membership import (
    ResidentMembership, 
    ResidentMembershipStatus,
    ResidentMembershipRole
)
from app.db.models import User, House


# Constants
MAX_ACTIVE_RESIDENTS_PER_HOUSE = 3


class BusinessRuleError(Exception):
    """Business rule violation error"""
    def __init__(self, code: str, message: str, http_status: int = 409, **kwargs):
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = kwargs
        super().__init__(message)


class ResidentMembershipService:
    """Service for managing resident memberships"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # --- Query Helpers ---
    
    def get_active_memberships_by_user(self, user_id: int) -> List[ResidentMembership]:
        """Get all ACTIVE memberships for a user"""
        return self.db.query(ResidentMembership).filter(
            ResidentMembership.user_id == user_id,
            ResidentMembership.status == ResidentMembershipStatus.ACTIVE
        ).all()
    
    def get_all_memberships_by_user(self, user_id: int) -> List[ResidentMembership]:
        """Get all memberships for a user (including inactive)"""
        return self.db.query(ResidentMembership).filter(
            ResidentMembership.user_id == user_id
        ).order_by(ResidentMembership.created_at.desc()).all()
    
    def get_active_memberships_by_house(self, house_id: int) -> List[ResidentMembership]:
        """Get all ACTIVE memberships for a house"""
        return self.db.query(ResidentMembership).filter(
            ResidentMembership.house_id == house_id,
            ResidentMembership.status == ResidentMembershipStatus.ACTIVE
        ).all()
    
    def count_active_members_by_house(self, house_id: int) -> int:
        """Count ACTIVE residents in a house"""
        return self.db.query(func.count(ResidentMembership.id)).filter(
            ResidentMembership.house_id == house_id,
            ResidentMembership.status == ResidentMembershipStatus.ACTIVE
        ).scalar() or 0
    
    def get_membership(self, membership_id: int) -> Optional[ResidentMembership]:
        """Get membership by ID"""
        return self.db.query(ResidentMembership).filter(
            ResidentMembership.id == membership_id
        ).first()
    
    def get_membership_by_user_and_house(
        self, user_id: int, house_id: int
    ) -> Optional[ResidentMembership]:
        """Get membership by user and house (unique constraint)"""
        return self.db.query(ResidentMembership).filter(
            ResidentMembership.user_id == user_id,
            ResidentMembership.house_id == house_id
        ).first()
    
    # --- Business Operations ---
    
    def add_resident_to_house(
        self,
        user_id: int,
        house_id: int,
        role: ResidentMembershipRole = ResidentMembershipRole.FAMILY
    ) -> ResidentMembership:
        """
        Add a resident to a house.
        
        Rules:
        - Max 3 ACTIVE residents per house
        - If existing INACTIVE membership exists, reactivate it
        - Raises BusinessRuleError if limit reached
        """
        # Check if user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BusinessRuleError(
                code="USER_NOT_FOUND",
                message="ไม่พบผู้ใช้งาน",
                http_status=404,
                user_id=user_id
            )
        
        # Check if house exists
        house = self.db.query(House).filter(House.id == house_id).first()
        if not house:
            raise BusinessRuleError(
                code="HOUSE_NOT_FOUND",
                message="ไม่พบบ้าน",
                http_status=404,
                house_id=house_id
            )
        
        # Check existing membership
        existing = self.get_membership_by_user_and_house(user_id, house_id)
        
        if existing:
            if existing.status == ResidentMembershipStatus.ACTIVE:
                raise BusinessRuleError(
                    code="MEMBERSHIP_ALREADY_EXISTS",
                    message="ผู้ใช้งานเป็นสมาชิกของบ้านนี้อยู่แล้ว",
                    http_status=409,
                    user_id=user_id,
                    house_id=house_id,
                    membership_id=existing.id
                )
            else:
                # Reactivate existing inactive membership
                return self.reactivate_membership(existing.id)
        
        # Check house limit
        active_count = self.count_active_members_by_house(house_id)
        if active_count >= MAX_ACTIVE_RESIDENTS_PER_HOUSE:
            raise BusinessRuleError(
                code="HOUSE_RESIDENT_LIMIT_REACHED",
                message="บ้านนี้มีผู้ใช้งานครบ 3 คนแล้ว",
                http_status=409,
                house_id=house_id,
                house_code=house.house_code,
                current_count=active_count,
                max_allowed=MAX_ACTIVE_RESIDENTS_PER_HOUSE
            )
        
        # Create new membership
        membership = ResidentMembership(
            user_id=user_id,
            house_id=house_id,
            role=role,
            status=ResidentMembershipStatus.ACTIVE
        )
        
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        
        return membership
    
    def deactivate_membership(self, membership_id: int) -> ResidentMembership:
        """
        Deactivate a membership.
        
        Sets status to INACTIVE and records deactivated_at timestamp.
        Does NOT delete the record (audit trail).
        """
        membership = self.get_membership(membership_id)
        
        if not membership:
            raise BusinessRuleError(
                code="MEMBERSHIP_NOT_FOUND",
                message="ไม่พบข้อมูลการเป็นสมาชิก",
                http_status=404,
                membership_id=membership_id
            )
        
        if membership.status == ResidentMembershipStatus.INACTIVE:
            raise BusinessRuleError(
                code="MEMBERSHIP_ALREADY_INACTIVE",
                message="สมาชิกภาพนี้ถูกยกเลิกไปแล้ว",
                http_status=409,
                membership_id=membership_id
            )
        
        membership.status = ResidentMembershipStatus.INACTIVE
        membership.deactivated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(membership)
        
        return membership
    
    def reactivate_membership(self, membership_id: int) -> ResidentMembership:
        """
        Reactivate an inactive membership.
        
        Must check 3-member limit before reactivating.
        """
        membership = self.get_membership(membership_id)
        
        if not membership:
            raise BusinessRuleError(
                code="MEMBERSHIP_NOT_FOUND",
                message="ไม่พบข้อมูลการเป็นสมาชิก",
                http_status=404,
                membership_id=membership_id
            )
        
        if membership.status == ResidentMembershipStatus.ACTIVE:
            raise BusinessRuleError(
                code="MEMBERSHIP_ALREADY_ACTIVE",
                message="สมาชิกภาพนี้ยังใช้งานอยู่",
                http_status=409,
                membership_id=membership_id
            )
        
        # Check house limit before reactivating
        active_count = self.count_active_members_by_house(membership.house_id)
        if active_count >= MAX_ACTIVE_RESIDENTS_PER_HOUSE:
            house = self.db.query(House).filter(House.id == membership.house_id).first()
            raise BusinessRuleError(
                code="HOUSE_RESIDENT_LIMIT_REACHED",
                message="บ้านนี้มีผู้ใช้งานครบ 3 คนแล้ว",
                http_status=409,
                house_id=membership.house_id,
                house_code=house.house_code if house else None,
                current_count=active_count,
                max_allowed=MAX_ACTIVE_RESIDENTS_PER_HOUSE
            )
        
        membership.status = ResidentMembershipStatus.ACTIVE
        membership.deactivated_at = None
        
        self.db.commit()
        self.db.refresh(membership)
        
        return membership


# Factory function for dependency injection
def get_resident_membership_service(db: Session) -> ResidentMembershipService:
    """Get ResidentMembershipService instance"""
    return ResidentMembershipService(db)
