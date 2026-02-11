"""
Phase H.1.1: Vendors & Categories API

Endpoints:
  Vendors:
    GET    /api/vendors                  - List vendors (active_only filter)
    POST   /api/vendors                  - Create vendor
    PUT    /api/vendors/{id}             - Update vendor (name IMMUTABLE)
    POST   /api/vendors/{id}/deactivate  - Soft delete vendor

  Vendor Categories:
    GET    /api/vendors/categories        - List vendor categories
    POST   /api/vendors/categories        - Create vendor category
    PUT    /api/vendors/categories/{id}   - Update vendor category (name IMMUTABLE)
    POST   /api/vendors/categories/{id}/deactivate - Soft delete

  Expense Categories:
    GET    /api/vendors/expense-categories        - List expense categories
    POST   /api/vendors/expense-categories        - Create expense category
    PUT    /api/vendors/expense-categories/{id}   - Update expense category (name IMMUTABLE)
    POST   /api/vendors/expense-categories/{id}/deactivate - Soft delete

RBAC: super_admin, admin only (read: + accounting)

Validation:
  - 409 VENDOR_NAME_ALREADY_EXISTS
  - 400 VENDOR_NAME_IMMUTABLE
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sa_func
from pydantic import BaseModel, Field
from typing import Optional, List

from app.db.session import get_db
from app.db.models import User, Expense
from app.db.models.vendor import Vendor, VendorCategory, ExpenseCategoryMaster
from app.core.deps import require_admin_or_accounting, require_admin


router = APIRouter(prefix="/api/vendors", tags=["vendors"])


# ============================================
# Pydantic Schemas
# ============================================

class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    vendor_category_id: Optional[int] = None
    phone: Optional[str] = Field(None, max_length=20)
    bank_account: Optional[str] = Field(None, max_length=100)

class VendorUpdate(BaseModel):
    """Update vendor - name is NOT allowed"""
    vendor_category_id: Optional[int] = None
    phone: Optional[str] = Field(None, max_length=20)
    bank_account: Optional[str] = Field(None, max_length=100)

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class CategoryUpdate(BaseModel):
    """Update category - name is NOT allowed"""
    # No fields allowed to update except via dedicated endpoints
    pass


# ============================================
# Vendor Endpoints
# ============================================

@router.get("")
async def list_vendors(
    active_only: bool = Query(True, description="Show only active vendors"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """List vendors with optional active filter."""
    query = db.query(Vendor).options(joinedload(Vendor.category))
    if active_only:
        query = query.filter(Vendor.is_active == True)
    vendors = query.order_by(Vendor.name).all()
    return {"vendors": [v.to_dict() for v in vendors]}


@router.post("")
async def create_vendor(
    data: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new vendor.
    
    Validation:
    - Name must be unique (case-insensitive, trimmed)
    - 409 if duplicate
    """
    normalized = data.name.strip().lower()
    
    # Check for duplicate (case-insensitive)
    existing = db.query(Vendor).filter(
        sa_func.lower(sa_func.trim(Vendor.name)) == normalized
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"code": "VENDOR_NAME_ALREADY_EXISTS", "message": f"Vendor '{data.name.strip()}' already exists"}
        )
    
    # Validate category if provided
    if data.vendor_category_id:
        cat = db.query(VendorCategory).filter(VendorCategory.id == data.vendor_category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Vendor category not found")
    
    vendor = Vendor(
        name=data.name.strip(),
        vendor_category_id=data.vendor_category_id,
        phone=data.phone,
        bank_account=data.bank_account,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    return {**vendor.to_dict(), "message": "Vendor created successfully"}


@router.put("/{vendor_id}")
async def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update vendor details (name is IMMUTABLE).
    
    - 400 VENDOR_NAME_IMMUTABLE if name change attempted
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Update allowed fields
    if data.vendor_category_id is not None:
        if data.vendor_category_id == 0:
            vendor.vendor_category_id = None
        else:
            cat = db.query(VendorCategory).filter(VendorCategory.id == data.vendor_category_id).first()
            if not cat:
                raise HTTPException(status_code=404, detail="Vendor category not found")
            vendor.vendor_category_id = data.vendor_category_id
    
    if data.phone is not None:
        vendor.phone = data.phone
    if data.bank_account is not None:
        vendor.bank_account = data.bank_account
    
    db.commit()
    db.refresh(vendor)
    
    return {**vendor.to_dict(), "message": "Vendor updated successfully"}


@router.post("/{vendor_id}/deactivate")
async def deactivate_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft-delete (deactivate) a vendor."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.is_active = False
    db.commit()
    
    return {"message": f"Vendor '{vendor.name}' deactivated", "id": vendor_id}


@router.post("/{vendor_id}/reactivate")
async def reactivate_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Re-activate a deactivated vendor."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.is_active = True
    db.commit()
    
    return {"message": f"Vendor '{vendor.name}' reactivated", "id": vendor_id}


# ============================================
# Vendor Category Endpoints
# ============================================

@router.get("/categories")
async def list_vendor_categories(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """List vendor categories."""
    query = db.query(VendorCategory)
    if active_only:
        query = query.filter(VendorCategory.is_active == True)
    categories = query.order_by(VendorCategory.name).all()
    return {"categories": [c.to_dict() for c in categories]}


@router.post("/categories")
async def create_vendor_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create vendor category (name must be unique, case-insensitive)."""
    normalized = data.name.strip().lower()
    existing = db.query(VendorCategory).filter(
        sa_func.lower(sa_func.trim(VendorCategory.name)) == normalized
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"code": "CATEGORY_NAME_ALREADY_EXISTS", "message": f"Category '{data.name.strip()}' already exists"}
        )
    
    cat = VendorCategory(name=data.name.strip())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {**cat.to_dict(), "message": "Vendor category created"}


@router.put("/categories/{category_id}")
async def update_vendor_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Vendor category name is immutable. No updatable fields."""
    raise HTTPException(
        status_code=400,
        detail={"code": "CATEGORY_NAME_IMMUTABLE", "message": "Category name cannot be changed after creation"}
    )


@router.post("/categories/{category_id}/deactivate")
async def deactivate_vendor_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft-delete vendor category."""
    cat = db.query(VendorCategory).filter(VendorCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Vendor category not found")
    cat.is_active = False
    db.commit()
    return {"message": f"Vendor category '{cat.name}' deactivated", "id": category_id}


@router.post("/categories/{category_id}/reactivate")
async def reactivate_vendor_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Re-activate vendor category."""
    cat = db.query(VendorCategory).filter(VendorCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Vendor category not found")
    cat.is_active = True
    db.commit()
    return {"message": f"Vendor category '{cat.name}' reactivated", "id": category_id}


# ============================================
# Expense Category Endpoints
# ============================================

@router.get("/expense-categories")
async def list_expense_categories(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """List expense categories."""
    query = db.query(ExpenseCategoryMaster)
    if active_only:
        query = query.filter(ExpenseCategoryMaster.is_active == True)
    categories = query.order_by(ExpenseCategoryMaster.name).all()
    return {"categories": [c.to_dict() for c in categories]}


@router.post("/expense-categories")
async def create_expense_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create expense category (name must be unique, case-insensitive)."""
    normalized = data.name.strip().lower()
    existing = db.query(ExpenseCategoryMaster).filter(
        sa_func.lower(sa_func.trim(ExpenseCategoryMaster.name)) == normalized
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"code": "CATEGORY_NAME_ALREADY_EXISTS", "message": f"Expense category '{data.name.strip()}' already exists"}
        )
    
    cat = ExpenseCategoryMaster(name=data.name.strip())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {**cat.to_dict(), "message": "Expense category created"}


@router.put("/expense-categories/{category_id}")
async def update_expense_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Expense category name is immutable. No updatable fields."""
    raise HTTPException(
        status_code=400,
        detail={"code": "CATEGORY_NAME_IMMUTABLE", "message": "Category name cannot be changed after creation"}
    )


@router.post("/expense-categories/{category_id}/deactivate")
async def deactivate_expense_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft-delete expense category."""
    cat = db.query(ExpenseCategoryMaster).filter(ExpenseCategoryMaster.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Expense category not found")
    cat.is_active = False
    db.commit()
    return {"message": f"Expense category '{cat.name}' deactivated", "id": category_id}


@router.post("/expense-categories/{category_id}/reactivate")
async def reactivate_expense_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Re-activate expense category."""
    cat = db.query(ExpenseCategoryMaster).filter(ExpenseCategoryMaster.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Expense category not found")
    cat.is_active = True
    db.commit()
    return {"message": f"Expense category '{cat.name}' reactivated", "id": category_id}
