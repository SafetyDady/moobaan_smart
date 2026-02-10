from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    """
    User model supporting multiple authentication methods:
    - Admin/Accounting: email + password
    - Resident: LINE Login (Phase D.4.1)
    
    Phase D.4.1: LINE OA as Gateway
    - line_user_id is the ONLY identity for residents
    - No OTP, no phone anchor
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=True)  # Phase R.2: Display name (auto-generated for residents)
    email = Column(String(255), unique=True, nullable=True, index=True)  # Phase R.2: Nullable for residents
    full_name = Column(String(255), nullable=True)  # Phase R.2: Nullable for residents
    phone = Column(String(50), nullable=True, index=True)  # Phase R.2: Unique index (partial) for OTP
    hashed_password = Column(String(255), nullable=True)  # Phase R.2: Nullable for OTP-only residents
    
    # Phase D.4.1: LINE Login identity
    line_user_id = Column(String(100), unique=True, nullable=True, index=True)
    
    is_active = Column(Boolean, nullable=False, default=True)
    role = Column(String(50), nullable=False, default="resident")  # super_admin, accounting, resident
    
    # Phase D.2: Session version for resident session revocation
    # Admin can increment this to invalidate all active resident sessions
    session_version = Column(Integer, nullable=False, default=1)
    
    # Password reset fields
    must_change_password = Column(Boolean, nullable=False, default=False)
    password_reset_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # admin who reset it
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary matching frontend expectations"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
    def to_safe_dict(self):
        """Convert model to dictionary without sensitive information"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
        }