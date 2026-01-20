from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.house_member import HouseMember
from app.core.auth import (
    authenticate_user, create_user_token, verify_password, get_password_hash,
    create_refresh_token, verify_token, generate_csrf_token,
    COOKIE_SECURE, COOKIE_SAMESITE, COOKIE_DOMAIN, REFRESH_TOKEN_EXPIRE_DAYS
)
from app.core.deps import get_current_user
from app.models import LoginRequest, TokenResponse, UserResponse
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
import logging

logger = logging.getLogger(__name__)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str):
    """Set httpOnly cookies for authentication"""
    # Access token - httpOnly, short-lived
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=15 * 60,  # 15 minutes
        path="/",
        domain=COOKIE_DOMAIN
    )
    
    # Refresh token - httpOnly, long-lived
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 7 days
        path="/api/auth/refresh",  # Only sent to refresh endpoint
        domain=COOKIE_DOMAIN
    )
    
    # CSRF token - NOT httpOnly (JS needs to read it)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Must be readable by JS
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
        domain=COOKIE_DOMAIN
    )


def clear_auth_cookies(response: Response):
    """Clear all auth cookies on logout"""
    response.delete_cookie(key="access_token", path="/", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="refresh_token", path="/api/auth/refresh", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="csrf_token", path="/", domain=COOKIE_DOMAIN)


@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return access token via httpOnly cookie"""
    # Debug: Log received credentials (mask password for security)
    logger.info(f"Login attempt: email={login_data.email}, password_len={len(login_data.password)}")
    
    user = authenticate_user(login_data.email, login_data.password, db)
    
    if not user:
        logger.warning(f"Login failed for email: {login_data.email}")
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
    
    # Create tokens
    access_token = create_user_token(user, house_id)
    refresh_token_value = create_refresh_token({"sub": str(user.id), "role": user.role})
    csrf_token = generate_csrf_token()
    
    # Create response with cookies
    response = JSONResponse(content={
        "access_token": access_token,
        "token_type": "bearer"
    })
    
    # Set httpOnly cookies on the response
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=15 * 60,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth"
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )
    
    logger.info(f"Login successful for {user.email}, cookies set")
    return response


@router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """Refresh access token using refresh token from httpOnly cookie"""
    refresh_token_cookie = request.cookies.get("refresh_token")
    
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )
    
    # Verify refresh token
    token_data = verify_token(refresh_token_cookie, token_type="refresh")
    if not token_data:
        # Return response that clears cookies
        response = JSONResponse(
            status_code=401,
            content={"detail": "Invalid or expired refresh token"}
        )
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/api/auth")
        response.delete_cookie(key="csrf_token", path="/")
        return response
    
    # Get user
    user = db.query(User).filter(User.id == int(token_data["user_id"])).first()
    if not user or not user.is_active:
        response = JSONResponse(
            status_code=401,
            content={"detail": "User not found or inactive"}
        )
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/api/auth")
        response.delete_cookie(key="csrf_token", path="/")
        return response
    
    # Get house_id for resident users
    house_id = None
    if user.role == "resident":
        house_member = db.query(HouseMember).filter(HouseMember.user_id == user.id).first()
        house_id = house_member.house_id if house_member else None
    
    # Create new tokens (rotate refresh token for security)
    new_access_token = create_user_token(user, house_id)
    new_refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role})
    csrf_token = generate_csrf_token()
    
    # Create response with new cookies
    response = JSONResponse(content={
        "message": "Token refreshed",
        "access_token": new_access_token
    })
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=15 * 60,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth"
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )
    
    logger.info(f"Token refreshed for user {user.id} ({user.email})")
    return response


@router.post("/logout")
async def logout():
    """Logout user - clear all auth cookies"""
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")
    response.delete_cookie(key="csrf_token", path="/")
    return response


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
