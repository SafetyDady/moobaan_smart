"""
Phase H.1.1: Vendor & Category Foundation

Vendor model for managing expense payees.

Rules:
- name is immutable after creation
- Unique constraint is case-insensitive (LOWER(TRIM(name)))
- Soft delete only (is_active = false)
- vendor_category_id links to vendor_categories table
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class VendorCategory(Base):
    """
    Vendor categories (e.g., Contractor, Utility Provider, Service Provider)
    
    Rules:
    - name unique case-insensitive
    - Soft delete only (is_active)
    """
    __tablename__ = "vendor_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    vendors = relationship("Vendor", back_populates="category")

    __table_args__ = (
        Index('ix_vendor_categories_name_ci', text("LOWER(TRIM(name))"), unique=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Vendor(Base):
    """
    Vendor (payee) master data.
    
    Rules:
    - name is IMMUTABLE after creation
    - name unique case-insensitive via functional index
    - Soft delete only (is_active = false)
    """
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    vendor_category_id = Column(Integer, ForeignKey("vendor_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    bank_account = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("VendorCategory", back_populates="vendors")

    __table_args__ = (
        Index('ix_vendors_name_ci', text("LOWER(TRIM(name))"), unique=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "vendor_category_id": self.vendor_category_id,
            "category_name": self.category.name if self.category else None,
            "phone": self.phone,
            "bank_account": self.bank_account,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ExpenseCategoryMaster(Base):
    """
    Expense categories master table (replaces hardcoded EXPENSE_CATEGORIES enum).
    
    Rules:
    - name unique case-insensitive
    - Soft delete only (is_active)
    """
    __tablename__ = "expense_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_expense_categories_name_ci', text("LOWER(TRIM(name))"), unique=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
