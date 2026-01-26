"""
Phase R.1 (Step 1): Resident Membership Model

Purpose:
- Track user ↔ house membership (many-to-many)
- Support 1 phone → multiple houses
- Enforce max 3 active residents per house
- Audit-friendly with deactivate/reactivate

IMPORTANT:
- This is SEPARATE from house_members (legacy table)
- User identity stays in users table
- This table only handles membership binding

Explicit Non-Goals:
- NO accounting logic
- NO pay-in logic
- NO auth/OTP
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class ResidentMembershipStatus(enum.Enum):
    """Membership status enum"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ResidentMembershipRole(enum.Enum):
    """Role within the house"""
    OWNER = "OWNER"
    FAMILY = "FAMILY"


class ResidentMembership(Base):
    """
    Resident Membership - binds a user to a house.
    
    Rules:
    - One user can have multiple memberships (different houses)
    - One house can have max 3 ACTIVE memberships
    - Deactivate sets status to INACTIVE (no hard delete)
    - Reactivate must check the 3-member limit
    
    Constraints:
    - Unique (user_id, house_id) - no duplicate memberships
    - No cascade delete - preserve audit trail
    """
    __tablename__ = "resident_memberships"
    __table_args__ = (
        UniqueConstraint('user_id', 'house_id', name='uq_resident_membership_user_house'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    status = Column(
        Enum(ResidentMembershipStatus), 
        nullable=False, 
        default=ResidentMembershipStatus.ACTIVE,
        index=True
    )
    role = Column(
        Enum(ResidentMembershipRole),
        nullable=False,
        default=ResidentMembershipRole.FAMILY
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    house = relationship("House", foreign_keys=[house_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "house_id": self.house_id,
            "user_name": self.user.full_name if self.user else None,
            "user_phone": self.user.phone if self.user else None,
            "house_code": self.house.house_code if self.house else None,
            "status": self.status.value if self.status else None,
            "role": self.role.value if self.role else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deactivated_at": self.deactivated_at.isoformat() if self.deactivated_at else None,
        }
    
    def is_active(self) -> bool:
        """Check if membership is currently active"""
        return self.status == ResidentMembershipStatus.ACTIVE
