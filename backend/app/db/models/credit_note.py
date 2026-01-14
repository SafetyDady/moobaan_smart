from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class CreditNote(Base):
    __tablename__ = "credit_notes"

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # Positive number (will be subtracted from balance)
    reason = Column(Text, nullable=False)  # Required explanation for credit
    reference = Column(String(255), nullable=True)  # Optional reference number or document
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    house = relationship("House")
    creator = relationship("User")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "house_code": self.house.house_code if self.house else None,
            "owner_name": self.house.owner_name if self.house else None,
            "amount": float(self.amount) if self.amount else 0,
            "reason": self.reason,
            "reference": self.reference,
            "created_by": self.created_by,
            "creator_name": self.creator.full_name if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }