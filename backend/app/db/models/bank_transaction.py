from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, UniqueConstraint, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid
import enum


class PostingStatus(enum.Enum):
    UNMATCHED = "UNMATCHED"
    MATCHED = "MATCHED"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_statement_batch_id = Column(UUID(as_uuid=True), ForeignKey("bank_statement_batches.id"), nullable=False)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    
    effective_at = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=False)
    debit = Column(Numeric(15, 2), nullable=True)
    credit = Column(Numeric(15, 2), nullable=True)
    balance = Column(Numeric(15, 2), nullable=True)
    channel = Column(String(100), nullable=True)
    
    raw_row = Column(JSON, nullable=False)  # Store original parsed row
    fingerprint = Column(String(64), nullable=False)  # Hash for duplicate detection
    
    # Reconciliation: 1:1 match with payin_report
    matched_payin_id = Column(Integer, ForeignKey("payin_reports.id", ondelete="SET NULL"), nullable=True, unique=True)
    
    # Phase P1: Statement-Driven posting status
    posting_status = Column(
        SAEnum(PostingStatus, name='posting_status_enum', create_constraint=False, native_enum=True),
        nullable=False,
        server_default='UNMATCHED'
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    batch = relationship("BankStatementBatch", backref="transactions")
    bank_account = relationship("BankAccount", backref="transactions")
    # 1:1 with PayinReport - ONLY declare on BankTransaction side (has the FK)
    matched_payin = relationship("PayinReport", foreign_keys=[matched_payin_id], uselist=False)
    
    # Constraint: No duplicate fingerprint per bank account
    __table_args__ = (
        UniqueConstraint('bank_account_id', 'fingerprint', name='uq_bank_account_fingerprint'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "bank_statement_batch_id": str(self.bank_statement_batch_id),
            "bank_account_id": str(self.bank_account_id),
            "effective_at": self.effective_at.isoformat() if self.effective_at else None,
            "description": self.description,
            "debit": float(self.debit) if self.debit else None,
            "credit": float(self.credit) if self.credit else None,
            "balance": float(self.balance) if self.balance else None,
            "channel": self.channel,
            "matched_payin_id": self.matched_payin_id,
            "is_matched": self.matched_payin_id is not None,
            "posting_status": self.posting_status.value if self.posting_status else "UNMATCHED",
            "raw_row": self.raw_row,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
