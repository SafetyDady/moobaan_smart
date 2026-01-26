"""
Phase R.2: Resident Authentication API

Purpose:
- OTP-based login for residents
- Phone number as primary identifier
- Returns resident memberships after login

Endpoints:
- POST /api/resident/login/request-otp
- POST /api/resident/login/verify-otp
- POST /api/resident/logout
- GET /api/resident/me

IMPORTANT:
- NO house selection yet (Phase R.3)
- NO accounting endpoints
- Mock OTP only
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import User
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus, ResidentMembershipRole
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.api.auth import set_auth_cookies, clear_auth_cookies
from app.services.otp_service import request_otp, verify_otp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resident", tags=["resident-auth"])


# --- Request/Response Models ---

class RequestOTPRequest(BaseModel):
    """Request OTP for phone"""
    phone: str = Field(..., min_length=9, max_length=15, description="Phone number")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Normalize and validate phone number"""
        # Remove common formatting
        v = v.replace(' ', '').replace('-', '').replace('.', '')
        
        # Handle Thai format
        if v.startswith('+66'):
            v = '0' + v[3:]
        elif v.startswith('66'):
            v = '0' + v[2:]
        
        # Must be digits only after normalization
        if not v.isdigit():
            raise ValueError('เบอร์โทรศัพท์ต้องเป็นตัวเลขเท่านั้น')
        
        # Thai mobile phone: 10 digits starting with 0
        if len(v) != 10 or not v.startswith('0'):
            raise ValueError('กรุณาใส่เบอร์โทรศัพท์ 10 หลัก เช่น 0812345678')
        
        return v


class RequestOTPResponse(BaseModel):
    """Response for OTP request"""
    success: bool
    message: str
    phone_masked: str  # e.g., "081****678"
    
    # Only in mock mode - for testing
    otp_hint: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    """Verify OTP"""
    phone: str = Field(..., min_length=9, max_length=15)
    otp: str = Field(..., min_length=6, max_length=6)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Same normalization as RequestOTPRequest"""
        v = v.replace(' ', '').replace('-', '').replace('.', '')
        if v.startswith('+66'):
            v = '0' + v[3:]
        elif v.startswith('66'):
            v = '0' + v[2:]
        return v
    
    @field_validator('otp')
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """OTP must be 6 digits"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError('OTP ต้องเป็นตัวเลข 6 หลัก')
        return v


class HouseMembershipInfo(BaseModel):
    """House membership info for resident"""
    house_id: int
    house_number: str
    role: str  # "owner" | "family"
    status: str  # "active" | "inactive"


class VerifyOTPResponse(BaseModel):
    """Response for OTP verification"""
    success: bool
    message: str
    user_id: Optional[int] = None
    phone: Optional[str] = None
    memberships: List[HouseMembershipInfo] = []


class ResidentMeResponse(BaseModel):
    """Current resident info"""
    user_id: int
    phone: str
    memberships: List[HouseMembershipInfo]


# --- Helper Functions ---

def mask_phone(phone: str) -> str:
    """Mask phone number: 081****678"""
    if len(phone) < 7:
        return '****'
    return f"{phone[:3]}****{phone[-3:]}"


async def get_or_create_resident_user(
    db: AsyncSession, 
    phone: str
) -> User:
    """
    Get existing user by phone or create new resident user.
    
    Returns:
        User: The user object
    """
    # Find existing user by phone
    result = await db.execute(
        select(User).where(User.phone == phone)
    )
    user = result.scalar_one_or_none()
    
    if user:
        logger.info(f"[Resident Login] Found existing user: {user.id}")
        return user
    
    # Create new user with phone only
    user = User(
        username=f"resident_{phone}",  # Temporary username
        phone=phone,
        role="resident",
        is_active=True,
        # No password - OTP only
    )
    db.add(user)
    await db.flush()  # Get the ID
    
    logger.info(f"[Resident Login] Created new user: {user.id} for phone: ***{phone[-4:]}")
    return user


async def get_resident_memberships(
    db: AsyncSession,
    user_id: int
) -> List[HouseMembershipInfo]:
    """
    Get all memberships for a resident user.
    
    Returns list of HouseMembershipInfo
    """
    result = await db.execute(
        select(ResidentMembership)
        .options(selectinload(ResidentMembership.house))
        .where(ResidentMembership.user_id == user_id)
        .order_by(ResidentMembership.created_at.desc())
    )
    memberships = result.scalars().all()
    
    return [
        HouseMembershipInfo(
            house_id=m.house_id,
            house_number=m.house.house_number if m.house else f"House#{m.house_id}",
            role=m.role.value,
            status=m.status.value
        )
        for m in memberships
    ]


# --- Endpoints ---

@router.post("/login/request-otp", response_model=RequestOTPResponse)
async def resident_request_otp(
    request: RequestOTPRequest
):
    """
    Request OTP for resident login.
    
    - Normalizes phone number
    - Checks rate limit
    - Sends OTP (mock mode: returns hint)
    """
    phone = request.phone
    
    # Request OTP
    success, message = request_otp(phone)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message
        )
    
    # In mock mode, provide hint
    from app.services.otp_service import OTPConfig
    otp_hint = None
    if OTPConfig.MODE == "mock":
        otp_hint = OTPConfig.MOCK_CODE
    
    return RequestOTPResponse(
        success=True,
        message="ส่ง OTP ไปยังเบอร์โทรศัพท์แล้ว",
        phone_masked=mask_phone(phone),
        otp_hint=otp_hint
    )


@router.post("/login/verify-otp", response_model=VerifyOTPResponse)
async def resident_verify_otp(
    request: VerifyOTPRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP and login resident.
    
    - Verifies OTP
    - Creates or gets user
    - Creates session (httpOnly cookie)
    - Returns user info and memberships
    """
    phone = request.phone
    otp = request.otp
    
    # Verify OTP
    success, message = verify_otp(phone, otp)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    # Get or create user
    user = await get_or_create_resident_user(db, phone)
    await db.commit()
    
    # Get memberships
    memberships = await get_resident_memberships(db, user.id)
    
    # Create tokens - NO house_id yet (set in Phase R.3 when house selected)
    token_data = {
        "sub": str(user.id),
        "role": "resident",
        # house_id will be added in Phase R.3 when resident selects house
    }
    
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data={"sub": str(user.id), "role": "resident"})
    
    # Set cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    logger.info(f"[Resident Login] User {user.id} logged in, memberships: {len(memberships)}")
    
    return VerifyOTPResponse(
        success=True,
        message="เข้าสู่ระบบสำเร็จ",
        user_id=user.id,
        phone=mask_phone(phone),
        memberships=memberships
    )


@router.post("/logout")
async def resident_logout(
    response: Response
):
    """
    Logout resident.
    
    Clears httpOnly cookies.
    """
    clear_auth_cookies(response)
    return {"success": True, "message": "ออกจากระบบสำเร็จ"}


@router.get("/me", response_model=ResidentMeResponse)
async def get_resident_me(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current resident info and memberships.
    
    Requires valid session cookie.
    """
    # Get token from cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="กรุณาเข้าสู่ระบบ"
        )
    
    # Verify token
    payload = verify_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session หมดอายุ กรุณาเข้าสู่ระบบใหม่"
        )
    
    # Check role
    if payload.get("role") != "resident":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="เฉพาะลูกบ้านเท่านั้น"
        )
    
    user_id = int(payload.get("sub"))
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบข้อมูลผู้ใช้"
        )
    
    # Get memberships
    memberships = await get_resident_memberships(db, user_id)
    
    return ResidentMeResponse(
        user_id=user.id,
        phone=mask_phone(user.phone or ""),
        memberships=memberships
    )
