from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid


class BankStatementBatch(Base):
    __tablename__ = "bank_statement_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    source_type = Column(String(20), nullable=False, default="CSV")
    original_filename = Column(String(255), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), nullable=False, default="PARSED")  # PARSED, CONFIRMED, REJECTED
    
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    opening_balance = Column(Numeric(15, 2), nullable=True)
    closing_balance = Column(Numeric(15, 2), nullable=True)
    warnings = Column(JSON, nullable=True)  # Store validation warnings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bank_account = relationship("BankAccount", backref="statement_batches")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    # Constraint: One batch per bank account per month
    __table_args__ = (
        UniqueConstraint('bank_account_id', 'year', 'month', name='uq_bank_account_year_month'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "bank_account_id": str(self.bank_account_id),
            "year": self.year,
            "month": self.month,
            "source_type": self.source_type,
            "original_filename": self.original_filename,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "status": self.status,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "opening_balance": float(self.opening_balance) if self.opening_balance else None,
            "closing_balance": float(self.closing_balance) if self.closing_balance else None,
            "warnings": self.warnings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
