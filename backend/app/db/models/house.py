from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.session import Base


class House(Base):
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True, index=True)
    house_no = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")  # active, inactive
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
            "house_no": self.house_no,
            "status": self.status,
            "floor_area": self.floor_area,
            "land_area": self.land_area,
            "zone": self.zone,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }