"""
Attachment model — operational evidence storage.

Single table for all attachment types:
- PAYIN → SLIP (resident payment proof)
- EXPENSE → INVOICE (before payment) / RECEIPT (after payment)

Soft delete only. No versioning, no approval workflow.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base
import uuid


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(20), nullable=False)   # PAYIN | EXPENSE
    entity_id = Column(Integer, nullable=False)         # FK to payin_reports.id or expenses.id
    file_type = Column(String(20), nullable=False)      # SLIP | INVOICE | RECEIPT
    original_filename = Column(String(500), nullable=True)
    content_type = Column(String(100), nullable=True)   # e.g. image/jpeg, application/pdf
    object_key = Column(String(1000), nullable=False)   # R2 key: attachments/expense/42/receipt_abc.pdf
    file_size = Column(Integer, nullable=True)           # bytes (informational)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, nullable=False, server_default="false")

    __table_args__ = (
        Index('ix_attachment_entity', 'entity_type', 'entity_id'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "file_type": self.file_type,
            "original_filename": self.original_filename,
            "content_type": self.content_type,
            "object_key": self.object_key,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_deleted": self.is_deleted,
        }
