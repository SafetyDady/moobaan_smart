from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.house_member import HouseMember
from app.core.auth import authenticate_user, create_user_token
from app.core.deps import get_current_user
from app.models import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    user = authenticate_user(login_data.email, login_data.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get house_id for resident users
    house_id = None
    if user.role == "resident":
        house_member = db.query(HouseMember).filter(HouseMember.user_id == user.id).first()
        house_id = house_member.house_id if house_member else None
    
    access_token = create_user_token(user, house_id)
    
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout():
    """Logout user (stateless, just return success)"""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    # Get house_id for resident users
    house_id = None
    if current_user.role == "resident":
        house_member = db.query(HouseMember).filter(HouseMember.user_id == current_user.id).first()
        house_id = house_member.house_id if house_member else None
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        house_id=house_id
    )
