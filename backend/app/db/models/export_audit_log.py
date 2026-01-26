"""
Phase G.2: Export Audit Log Model

Purpose:
- Track all accounting exports
- Audit trail for compliance
- READ ONLY - no mutation to source data
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class ExportAuditLog(Base):
    """
    Audit log for accounting exports.
    Records who exported what and when.
    """
    __tablename__ = "export_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Export parameters
    from_period = Column(String(10), nullable=False)  # YYYY-MM format
    to_period = Column(String(10), nullable=False)    # YYYY-MM format
    export_type = Column(String(50), nullable=False)  # "csv", "xlsx"
    
    # What was exported
    reports_included = Column(Text, nullable=False)  # JSON array of report names
    
    # Metadata
    exported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "from_period": self.from_period,
            "to_period": self.to_period,
            "export_type": self.export_type,
            "reports_included": self.reports_included,
            "exported_at": self.exported_at.isoformat() if self.exported_at else None,
        }
