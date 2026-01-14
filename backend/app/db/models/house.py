from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class HouseStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    BANK_OWNED = "BANK_OWNED"
    VACANT = "VACANT"
    ARCHIVED = "ARCHIVED"
    SUSPENDED = "SUSPENDED"


class House(Base):
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True, index=True)
    house_code = Column(String(20), unique=True, nullable=False, index=True)  # "28/1" to "28/158"
    house_status = Column(Enum(HouseStatus), nullable=False, default=HouseStatus.ACTIVE)
    owner_name = Column(String(255), nullable=False)  # Owner name for accounting reference
    floor_area = Column(String(50), nullable=True)  # e.g., "120 ตร.ม."
    land_area = Column(String(50), nullable=True)   # e.g., "80 ตรว."
    zone = Column(String(10), nullable=True)        # e.g., "A", "B", "C"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary matching frontend expectations"""
        return {
            "id": self.id,
            "house_code": self.house_code,
            "house_status": self.house_status.value if self.house_status else None,
            "owner_name": self.owner_name,
            "floor_area": self.floor_area,
            "land_area": self.land_area,
            "zone": self.zone,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def can_resident_access(self):
        """Check if residents can access this house"""
        return self.house_status == HouseStatus.ACTIVE