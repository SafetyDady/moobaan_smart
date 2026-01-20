"""
Phase G.1: Period Snapshot Model

Purpose:
- Logical soft lock for historical data
- Preserve historical truth for reporting
- Aggregated totals only, NO per-account balances

Explicit Non-Goals:
- No journal entries
- No GL accounts
- No balance calculation
"""
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class PeriodStatus(str, enum.Enum):
    """Period status enum"""
    DRAFT = "DRAFT"
    LOCKED = "LOCKED"


class PeriodSnapshot(Base):
    """
    Period Snapshot - represents a finalized view of the system as of month-end.
    
    Snapshot is derived from: Invoices, Payments, Credits, Expenses
    Snapshot does NOT store ledger balances, only aggregated results.
    """
    __tablename__ = "period_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)  # 1-12
    as_of_date = Column(Date, nullable=False, comment="Last day of the period month")
    
    # Aggregated snapshot data as JSON
    # Example: {"ar_total": 125000, "cash_received_total": 98000, ...}
    snapshot_data = Column(JSONB, nullable=False, default={})
    
    status = Column(Enum(PeriodStatus), nullable=False, default=PeriodStatus.LOCKED)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    notes = Column(Text, nullable=True, comment="Admin notes for the snapshot")
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    unlock_logs = relationship("PeriodUnlockLog", back_populates="period_snapshot")
    
    def to_dict(self):
        return {
            "id": self.id,
            "period_year": self.period_year,
            "period_month": self.period_month,
            "period_label": f"{self.period_year}-{str(self.period_month).zfill(2)}",
            "as_of_date": self.as_of_date.isoformat() if self.as_of_date else None,
            "snapshot_data": self.snapshot_data or {},
            "status": self.status.value if self.status else None,
            "created_by": self.created_by,
            "created_by_name": self.creator.full_name if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
        }


class PeriodUnlockLog(Base):
    """
    Audit log for period unlocks.
    Records who unlocked a period and why.
    """
    __tablename__ = "period_unlock_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    period_snapshot_id = Column(Integer, ForeignKey("period_snapshots.id"), nullable=False)
    unlocked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reason = Column(Text, nullable=False, comment="Reason for unlock (required)")
    previous_status = Column(String(20), nullable=False)
    
    # Relationships
    period_snapshot = relationship("PeriodSnapshot", back_populates="unlock_logs")
    user = relationship("User", foreign_keys=[unlocked_by])
    
    def to_dict(self):
        return {
            "id": self.id,
            "period_snapshot_id": self.period_snapshot_id,
            "unlocked_by": self.unlocked_by,
            "unlocked_by_name": self.user.full_name if self.user else None,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
            "reason": self.reason,
            "previous_status": self.previous_status,
        }
