from fastapi import APIRouter, HTTPException
from typing import List
from app.models import House, HouseCreate
from app.mock_data import MOCK_HOUSES

router = APIRouter(prefix="/api/houses", tags=["houses"])

# In-memory storage for demo
houses_db = list(MOCK_HOUSES)
next_id = max([h.id for h in houses_db]) + 1


@router.get("", response_model=List[House])
async def list_houses(status: str = None, search: str = None):
    """List all houses with optional filters"""
    result = houses_db
    
    if status:
        result = [h for h in result if h.status.value == status]
    
    if search:
        search_lower = search.lower()
        result = [h for h in result if 
                  search_lower in h.house_number.lower() or
                  (h.address and search_lower in h.address.lower())]
    
    return result


@router.get("/{house_id}", response_model=House)
async def get_house(house_id: int):
    """Get a specific house by ID"""
    house = next((h for h in houses_db if h.id == house_id), None)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return house


@router.post("", response_model=House)
async def create_house(house: HouseCreate):
    """Create a new house"""
    global next_id
    from datetime import datetime
    
    new_house = House(
        id=next_id,
        house_number=house.house_number,
        address=house.address,
        status=house.status,
        member_count=0,
        created_at=datetime.now()
    )
    houses_db.append(new_house)
    next_id += 1
    return new_house


@router.put("/{house_id}", response_model=House)
async def update_house(house_id: int, house: HouseCreate):
    """Update an existing house"""
    existing = next((h for h in houses_db if h.id == house_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="House not found")
    
    existing.house_number = house.house_number
    existing.address = house.address
    existing.status = house.status
    return existing


@router.delete("/{house_id}")
async def delete_house(house_id: int):
    """Delete a house"""
    global houses_db
    house = next((h for h in houses_db if h.id == house_id), None)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    houses_db = [h for h in houses_db if h.id != house_id]
    return {"message": "House deleted successfully"}
