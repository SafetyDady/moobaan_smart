from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from app.db.session import Base
import enum
from datetime import datetime, timedelta


class PayinStatus(enum.Enum):
    """Pay-in lifecycle states with clear transitions"""
    DRAFT = "DRAFT"                         # Resident started but not submitted
    SUBMITTED = "SUBMITTED"                 # Awaiting admin review (in queue)
    REJECTED_NEEDS_FIX = "REJECTED_NEEDS_FIX"  # Admin rejected; resident must fix
    ACCEPTED = "ACCEPTED"                   # Approved; ledger created (terminal)
    # Legacy states for backward compatibility
    PENDING = "PENDING"                     # Maps to SUBMITTED (deprecated)
    REJECTED = "REJECTED"                   # Maps to REJECTED_NEEDS_FIX (deprecated)


class PayinSource(enum.Enum):
    """Source of Pay-in creation for audit trail"""
    RESIDENT = "RESIDENT"           # Created by resident via app
    ADMIN_CREATED = "ADMIN_CREATED"  # Admin created from unidentified bank txn
    LINE_RECEIVED = "LINE_RECEIVED"  # Admin created from LINE slip evidence


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
    status = Column(Enum(PayinStatus), nullable=False, default=PayinStatus.DRAFT)
    rejection_reason = Column(Text, nullable=True)
    accepted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # SUPER_ADMIN who accepted
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Source tracking for audit
    source = Column(Enum(PayinSource), nullable=False, default=PayinSource.RESIDENT)
    created_by_admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_note = Column(Text, nullable=True)  # Note when admin creates from bank/LINE
    
    # Reconciliation: 1:1 match with bank_transaction
    matched_statement_txn_id = Column(UUID(as_uuid=True), ForeignKey("bank_transactions.id", ondelete="SET NULL"), nullable=True, unique=True)
    
    # Reference to originating bank transaction (for admin-created pay-ins)
    reference_bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("bank_transactions.id", ondelete="SET NULL"), nullable=True)
    
    submitted_at = Column(DateTime(timezone=True), nullable=True)  # When resident submitted for review
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    house = relationship("House")
    submitted_by = relationship("User", foreign_keys=[submitted_by_user_id])
    accepted_by_user = relationship("User", foreign_keys=[accepted_by])
    created_by_admin = relationship("User", foreign_keys=[created_by_admin_id])
    income_transaction = relationship("IncomeTransaction", uselist=False, back_populates="payin")
    # 1:1 with BankTransaction - ONLY declare on PayinReport side (has the FK)
    matched_statement_txn = relationship("BankTransaction", foreign_keys=[matched_statement_txn_id], uselist=False)
    reference_bank_txn = relationship("BankTransaction", foreign_keys=[reference_bank_transaction_id], uselist=False)

    def to_dict(self):
        """Convert model to dictionary matching frontend expectations"""
        return {
            "id": self.id,
            "house_id": self.house_id,
            "house_code": self.house.house_code if self.house else None,
            "submitted_by_user_id": self.submitted_by_user_id,
            "submitted_by_name": self.submitted_by.full_name if self.submitted_by else None,
            "amount": float(self.amount) if self.amount else 0,
            "transfer_date": self.transfer_date.isoformat() if self.transfer_date else None,
            "transfer_hour": self.transfer_hour,
            "transfer_minute": self.transfer_minute,
            "slip_url": self.slip_url,
            "matched_statement_txn_id": str(self.matched_statement_txn_id) if self.matched_statement_txn_id else None,
            "is_matched": self.matched_statement_txn_id is not None,
            "status": self.status.value if self.status else None,
            "rejection_reason": self.rejection_reason,
            "accepted_by": self.accepted_by,
            "accepted_by_name": self.accepted_by_user.full_name if self.accepted_by_user else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "source": self.source.value if self.source else "RESIDENT",
            "created_by_admin_id": self.created_by_admin_id,
            "created_by_admin_name": self.created_by_admin.full_name if self.created_by_admin else None,
            "admin_note": self.admin_note,
            "reference_bank_transaction_id": str(self.reference_bank_transaction_id) if self.reference_bank_transaction_id else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @hybrid_property
    def transfer_datetime(self):
        """Compute complete transfer datetime from date + hour + minute (business truth)"""
        if self.transfer_date and self.transfer_hour is not None and self.transfer_minute is not None:
            # transfer_date is already datetime with timezone, just need to set hour/minute
            return self.transfer_date.replace(hour=self.transfer_hour, minute=self.transfer_minute, second=0, microsecond=0)
        return None

    def is_locked(self):
        """Check if payin is locked (accepted state is terminal)"""
        return self.status == PayinStatus.ACCEPTED

    def can_be_edited(self):
        """Check if payin can be edited by resident"""
        return self.status in [PayinStatus.DRAFT, PayinStatus.REJECTED_NEEDS_FIX]

    def can_be_submitted(self):
        """Check if payin can be submitted for review"""
        return self.status in [PayinStatus.DRAFT, PayinStatus.REJECTED_NEEDS_FIX]

    def can_be_reviewed(self):
        """Check if payin is in reviewable state"""
        return self.status in [PayinStatus.SUBMITTED, PayinStatus.PENDING]

    def can_be_accepted(self):
        """Check if payin can be accepted (must be matched first)"""
        return self.can_be_reviewed() and self.matched_statement_txn_id is not None

    def validate_for_submission(self):
        """Validate required fields before submission (quality gate)"""
        errors = []
        if not self.transfer_date:
            errors.append("Transfer date is required")
        if self.transfer_hour is None:
            errors.append("Transfer hour is required")
        if self.transfer_minute is None:
            errors.append("Transfer minute is required")
        if not self.amount or float(self.amount) <= 0:
            errors.append("Valid amount is required")
        # Slip is strongly recommended but not blocking
        # if not self.slip_url:
        #     errors.append("Slip attachment is required")
        return errors

    @staticmethod
    def get_display_status(status):
        """Map status to display-friendly string"""
        status_map = {
            PayinStatus.DRAFT: "Draft",
            PayinStatus.SUBMITTED: "In Review",
            PayinStatus.PENDING: "In Review",  # Legacy
            PayinStatus.REJECTED_NEEDS_FIX: "Needs Fix",
            PayinStatus.REJECTED: "Needs Fix",  # Legacy
            PayinStatus.ACCEPTED: "Accepted",
        }
        return status_map.get(status, "Unknown")