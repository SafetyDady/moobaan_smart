from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.house_member import HouseMember
from app.core.auth import authenticate_user, create_user_token, verify_password, get_password_hash
from app.core.deps import get_current_user
from app.models import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


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
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your account has been deactivated. Please contact administrator.",
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
    # Get house_id and house_code for resident users
    house_id = None
    house_code = None
    if current_user.role == "resident":
        house_member = db.query(HouseMember).filter(HouseMember.user_id == current_user.id).first()
        if house_member:
            house_id = house_member.house_id
            from app.db.models.house import House
            house = db.query(House).filter(House.id == house_id).first()
            house_code = house.house_code if house else None
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        house_id=house_id,
        house_code=house_code
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for current user (force change after reset)"""
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Verify current password (unless it's a forced change)
        if not current_user.must_change_password:
            if not verify_password(request.current_password, current_user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        
        # Validate new password
        if len(request.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters"
            )
        
        # Update password
        current_user.hashed_password = get_password_hash(request.new_password)
        current_user.must_change_password = False
        current_user.password_reset_at = None
        current_user.password_reset_by = None
        
        db.commit()
        
        logger.info(f"Password changed for user {current_user.id} ({current_user.email})")
        
        return {
            "message": "Password changed successfully",
            "must_change_password": False
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error changing password for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
