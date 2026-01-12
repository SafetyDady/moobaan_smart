from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class HouseMember(Base):
    __tablename__ = "house_members"

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    member_role = Column(String(50), nullable=False, default="resident")  # owner, resident, tenant
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    house = relationship("House")
    user = relationship("User")

    def to_dict(self):
        """Convert model to dictionary matching frontend expectations"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "user_id": self.user_id,
            "member_role": self.member_role,
            "phone": self.phone,
            "name": self.user.full_name if self.user else None,
            "email": self.user.email if self.user else None,
            "house_no": self.house.house_no if self.house else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }