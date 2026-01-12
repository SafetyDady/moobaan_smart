from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import House as HouseSchema, HouseCreate
from app.db.models.house import House as HouseModel
from app.db.models.user import User
from app.db.session import get_db
from app.core.deps import require_admin_or_accounting

router = APIRouter(prefix="/api/houses", tags=["houses"])


@router.get("", response_model=List[dict])
async def list_houses(status: Optional[str] = None, search: Optional[str] = None, db: Session = Depends(get_db), current_user: User = require_admin_or_accounting):
    """List all houses with optional filters"""
    query = db.query(HouseModel)
    
    if status:
        query = query.filter(HouseModel.status == status)
    
    if search:
        search_lower = search.lower()
        query = query.filter(
            (HouseModel.house_no.ilike(f"%{search_lower}%")) |
            (HouseModel.notes.ilike(f"%{search_lower}%"))
        )
    
    houses = query.all()
    return [house.to_dict() for house in houses]


@router.get("/{house_id}", response_model=dict)
async def get_house(house_id: int, db: Session = Depends(get_db), current_user: User = require_admin_or_accounting):
    """Get a specific house by ID"""
    house = db.query(HouseModel).filter(HouseModel.id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return house.to_dict()


@router.post("", response_model=dict)
async def create_house(house: HouseCreate, db: Session = Depends(get_db), current_user: User = require_admin_or_accounting):
    """Create a new house"""
    from datetime import datetime
    
    # Check if house_no already exists
    existing = db.query(HouseModel).filter(HouseModel.house_no == house.house_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="House number already exists")
    
    new_house = HouseModel(
        house_no=house.house_number,
        status=house.status.value if hasattr(house.status, 'value') else house.status,
        floor_area=getattr(house, 'floor_area', None),
        land_area=getattr(house, 'land_area', None),
        zone=getattr(house, 'zone', None),
        notes=getattr(house, 'address', None),  # Map address to notes for backward compatibility
        created_at=datetime.now()
    )
    
    db.add(new_house)
    db.commit()
    db.refresh(new_house)
    
    return new_house.to_dict()


@router.put("/{house_id}", response_model=dict)
async def update_house(house_id: int, house_update: dict, db: Session = Depends(get_db), current_user: User = require_admin_or_accounting):
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
async def delete_house(house_id: int, db: Session = Depends(get_db), current_user: User = require_admin_or_accounting):
    """Delete a house"""
    house = db.query(HouseModel).filter(HouseModel.id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    db.delete(house)
    db.commit()
    
    return {"message": "House deleted successfully"}
