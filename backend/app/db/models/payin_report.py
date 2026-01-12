from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class PayinReport(Base):
    __tablename__ = "payin_reports"

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    transfer_date = Column(DateTime(timezone=True), nullable=False)
    transfer_hour = Column(Integer, nullable=False)  # 0-23
    transfer_minute = Column(Integer, nullable=False)  # 0-59
    slip_url = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    house = relationship("House")
    submitted_by = relationship("User")

    def to_dict(self):
        """Convert model to dictionary matching frontend expectations"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "house_no": self.house.house_no if self.house else None,
            "submitted_by_user_id": self.submitted_by_user_id,
            "submitted_by_name": self.submitted_by.display_name if self.submitted_by else None,
            "amount": float(self.amount) if self.amount else 0,
            "transfer_date": self.transfer_date.isoformat() if self.transfer_date else None,
            "transfer_hour": self.transfer_hour,
            "transfer_minute": self.transfer_minute,
            "slip_url": self.slip_url,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }