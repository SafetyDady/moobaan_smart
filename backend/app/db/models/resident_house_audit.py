"""
Phase R.3: Resident House Selection Audit Log

Purpose:
- Track HOUSE_SELECTED and HOUSE_SWITCH events
- Audit trail for security and compliance

IMPORTANT:
- Additive only - no changes to existing tables
- Only for resident house selection events
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ResidentHouseAuditLog(Base):
    """Audit log for resident house selection/switching"""
    __tablename__ = "resident_house_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Event type: HOUSE_SELECTED, HOUSE_SWITCH
    event_type = Column(String(50), nullable=False, index=True)
    
    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # House context
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=True)  # Target house
    from_house_id = Column(Integer, ForeignKey("houses.id"), nullable=True)  # For HOUSE_SWITCH
    to_house_id = Column(Integer, ForeignKey("houses.id"), nullable=True)  # For HOUSE_SWITCH
    
    # Additional context
    house_code = Column(String(50), nullable=True)  # Denormalized for quick lookup
    from_house_code = Column(String(50), nullable=True)
    to_house_code = Column(String(50), nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships (optional - for joins)
    user = relationship("User", foreign_keys=[user_id])
    house = relationship("House", foreign_keys=[house_id])

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "house_id": self.house_id,
            "from_house_id": self.from_house_id,
            "to_house_id": self.to_house_id,
            "house_code": self.house_code,
            "from_house_code": self.from_house_code,
            "to_house_code": self.to_house_code,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
