from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.house import House as HouseModel, HouseStatus
from app.db.models.user import User
from app.db.session import get_db
from app.core.deps import require_admin_or_accounting

router = APIRouter(prefix="/api/houses", tags=["houses"])


@router.get("", response_model=List[dict])
async def list_houses(status: Optional[str] = None, search: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_accounting)):
    """List all houses with optional filters"""
    query = db.query(HouseModel)
    
    if status:
        query = query.filter(HouseModel.house_status == status)
    
    if search:
        search_lower = search.lower()
        query = query.filter(
            (HouseModel.house_code.ilike(f"%{search_lower}%")) |
            (HouseModel.owner_name.ilike(f"%{search_lower}%")) |
            (HouseModel.notes.ilike(f"%{search_lower}%"))
        )
    
    houses = query.all()
    return [house.to_dict() for house in houses]


@router.get("/{house_id}", response_model=dict)
async def get_house(house_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_accounting)):
    """Get a specific house by ID"""
    house = db.query(HouseModel).filter(HouseModel.id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return house.to_dict()


@router.post("", response_model=dict)
async def create_house(house: dict, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_accounting)):
    """Create a new house"""
    import re
    
    house_code = house.get('house_code')
    owner_name = house.get('owner_name')
    house_status = house.get('house_status', 'ACTIVE')
    
    # Validate required fields
    if not house_code or not owner_name:
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "Missing required fields",
                "error_th": "ข้อมูลไม่ครบถ้วน",
                "error_en": "house_code and owner_name are required"
            }
        )
    
    # Validate house_code format
    if not re.match(r'^28\/[1-9][0-9]*$', house_code):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid house code format",
                "error_th": "รูปแบบรหัสบ้านไม่ถูกต้อง",
                "error_en": "House code must be in format 28/[1-9][0-9]* (e.g., 28/1, 28/15, 28/158)"
            }
        )
    
    # Check if house_code already exists
    existing = db.query(HouseModel).filter(HouseModel.house_code == house_code).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "House code already exists",
                "error_th": "รหัสบ้านนี้มีอยู่แล้ว",
                "error_en": f"House code {house_code} already exists"
            }
        )
    
    # Map the house status
    if house_status.upper() not in ['ACTIVE', 'BANK_OWNED', 'VACANT', 'ARCHIVED', 'SUSPENDED']:
        house_status = 'ACTIVE'
    
    try:
        new_house = HouseModel(
            house_code=house_code,
            owner_name=owner_name,
            house_status=getattr(HouseStatus, house_status.upper()),
            floor_area=house.get('floor_area'),
            land_area=house.get('land_area'),
            zone=house.get('zone'),
            notes=house.get('notes')
        )
        
        db.add(new_house)
        db.commit()
        db.refresh(new_house)
        
        return {
            "success": True,
            "house": new_house.to_dict(),
            "message": "House created successfully",
            "message_th": "สร้างข้อมูลบ้านเรียบร้อยแล้ว"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to create house",
                "error_th": "ไม่สามารถสร้างข้อมูลบ้านได้",
                "error_en": str(e)
            }
        )


@router.put("/{house_id}", response_model=dict)
async def update_house(house_id: int, house_update: dict, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_accounting)):
    """Update a house"""
    house = db.query(HouseModel).filter(HouseModel.id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Update allowed fields
    for key, value in house_update.items():
        if hasattr(house, key):
            setattr(house, key, value)
    
    db.commit()
    db.refresh(house)
    
    return house.to_dict()


@router.delete("/{house_id}")
async def delete_house(house_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_accounting)):
    """Delete a house"""
    house = db.query(HouseModel).filter(HouseModel.id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    db.delete(house)
    db.commit()
    
    return {"message": "House deleted successfully"}
