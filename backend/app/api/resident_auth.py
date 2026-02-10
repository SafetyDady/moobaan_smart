"""
Phase R.2 + R.3: Resident Authentication & House Selection API

Purpose:
- OTP-based login for residents (R.2)
- Phone number as primary identifier (R.2)
- House selection and context binding (R.3)

Endpoints (R.2):
- POST /api/resident/login/request-otp
- POST /api/resident/login/verify-otp
- POST /api/resident/logout
- GET /api/resident/me

Endpoints (R.3):
- GET /api/resident/houses
- POST /api/resident/select-house
- POST /api/resident/switch-house
- GET /api/resident/me/context

IMPORTANT:
- NO accounting endpoints
- Mock OTP only (R.2)
- active_house_id required for future resident actions (R.3)
- Uses SYNC database session (SQLAlchemy 1.x style)
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.db.models import User, House
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus, ResidentMembershipRole
from app.db.models.resident_house_audit import ResidentHouseAuditLog
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_csrf_token,
)
from app.api.auth import set_auth_cookies, clear_auth_cookies
from app.services.otp_service import request_otp, verify_otp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resident", tags=["resident-auth"])


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
    house_code: str  # e.g., "28/1"
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


def get_or_create_resident_user(db: Session, phone: str) -> User:
    """
    Get existing user by phone or create new resident user.
    
    SYNC version for SQLAlchemy 1.x style.
    """
    # Find existing user by phone
    user = db.query(User).filter(User.phone == phone).first()
    
    if user:
        logger.info(f"[Resident Login] Found existing user: {user.id}")
        return user
    
    # Create new user with phone only
    user = User(
        username=f"resident_{phone}",  # Temporary username
        full_name=f"ลูกบ้าน {phone[-4:]}",  # Default display name
        phone=phone,
        role="resident",
        is_active=True,
        # No password - OTP only
    )
    db.add(user)
    db.flush()  # Get the ID
    
    logger.info(f"[Resident Login] Created new user: {user.id} for phone: ***{phone[-4:]}")
    return user


def get_resident_memberships(db: Session, user_id: int) -> List[HouseMembershipInfo]:
    """
    Get all memberships for a resident user.
    
    SYNC version for SQLAlchemy 1.x style.
    """
    memberships = db.query(ResidentMembership)\
        .options(joinedload(ResidentMembership.house))\
        .filter(ResidentMembership.user_id == user_id)\
        .order_by(ResidentMembership.created_at.desc())\
        .all()
    
    return [
        HouseMembershipInfo(
            house_id=m.house_id,
            house_code=m.house.house_code if m.house else f"House#{m.house_id}",
            role=m.role.value,
            status=m.status.value
        )
        for m in memberships
    ]


# --- Endpoints ---

@router.post("/login/request-otp", response_model=RequestOTPResponse)
def resident_request_otp(request: RequestOTPRequest):
    """
    Request OTP for resident login.
    
    - Normalizes phone number
    - Checks sandbox whitelist (production mock mode)
    - Checks rate limit
    - Sends OTP (mock mode: returns hint)
    
    Error Codes:
    - 403: Phone not in sandbox whitelist (OTP_SANDBOX_ONLY)
    - 429: Rate limited
    """
    phone = request.phone
    
    # Request OTP
    success, message = request_otp(phone)
    
    if not success:
        # Phase D.3: Return 403 for sandbox whitelist rejection
        if message == "OTP_SANDBOX_ONLY":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="หมายเลขนี้ไม่ได้อยู่ในรายการทดสอบ กรุณาติดต่อผู้ดูแลระบบ"
            )
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
def resident_verify_otp(
    request: VerifyOTPRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and login resident.
    
    Phase D.1 Hardening:
    - Rate limited: 5 wrong attempts → 10 min lockout
    - Returns 429 for lockout, 401 for wrong OTP
    
    Phase D.3 Additions:
    - Returns 403 for sandbox whitelist rejection
    
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
        # Phase D.3: Return 403 for sandbox whitelist rejection
        if message == "OTP_SANDBOX_ONLY":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="หมายเลขนี้ไม่ได้อยู่ในรายการทดสอบ กรุณาติดต่อผู้ดูแลระบบ"
            )
        # Phase D.1: Return 429 for lockout, 401 for other failures
        if "กรุณารอ" in message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    # Get or create user
    user = get_or_create_resident_user(db, phone)
    db.commit()
    
    # Get memberships
    memberships = get_resident_memberships(db, user.id)
    
    # Create tokens - NO house_id yet (set in Phase R.3 when house selected)
    # Phase D.1: Role-based token expiry (resident = 7 days)
    # Phase D.2: Include session_version for session revocation
    token_data = {
        "sub": str(user.id),
        "role": "resident",
        "session_version": user.session_version,  # Phase D.2
        # house_id will be added in Phase R.3 when resident selects house
    }
    
    access_token = create_access_token(data=token_data, role="resident")
    refresh_token = create_refresh_token(data={"sub": str(user.id), "role": "resident", "session_version": user.session_version}, role="resident")
    csrf_token = generate_csrf_token()
    
    # Set cookies (Phase D.1: role-based max_age)
    set_auth_cookies(response, access_token, refresh_token, csrf_token, role="resident")
    
    logger.info(f"[Resident Login] User {user.id} logged in, memberships: {len(memberships)}")
    
    return VerifyOTPResponse(
        success=True,
        message="เข้าสู่ระบบสำเร็จ",
        user_id=user.id,
        phone=mask_phone(phone),
        memberships=memberships
    )


@router.post("/logout")
def resident_logout(response: Response):
    """
    Logout resident.
    
    Clears httpOnly cookies.
    """
    clear_auth_cookies(response)
    return {"success": True, "message": "ออกจากระบบสำเร็จ"}


@router.get("/me", response_model=ResidentMeResponse)
def get_resident_me(request: Request, db: Session = Depends(get_db)):
    """
    Get current resident info and memberships.
    
    Requires valid session cookie.
    Phase D.2: Validates session_version for session revocation support.
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
    
    user_id = int(payload.get("user_id"))
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบข้อมูลผู้ใช้"
        )
    
    # Phase D.2: Validate session_version for session revocation
    token_session_version = payload.get("session_version")
    if token_session_version is not None and token_session_version != user.session_version:
        logger.warning(f"[SESSION_REVOKED] User {user.id}: token_version={token_session_version}, db_version={user.session_version}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_REVOKED"
        )
    
    # Get memberships
    memberships = get_resident_memberships(db, user_id)
    
    return ResidentMeResponse(
        user_id=user.id,
        phone=mask_phone(user.phone or ""),
        memberships=memberships
    )


# ============================================================
# Phase R.3: House Selection Endpoints
# ============================================================

# --- R.3 Request/Response Models ---

class HouseListItem(BaseModel):
    """House info for list"""
    house_id: int
    house_code: str


class HouseListResponse(BaseModel):
    """Response for GET /api/resident/houses"""
    houses: List[HouseListItem]


class SelectHouseRequest(BaseModel):
    """Request for POST /api/resident/select-house"""
    house_id: int = Field(..., gt=0, description="House ID to select")


class SelectHouseResponse(BaseModel):
    """Response for select-house"""
    status: str  # "HOUSE_SELECTED"
    house_id: int
    house_code: str


class SwitchHouseRequest(BaseModel):
    """Request for POST /api/resident/switch-house"""
    house_id: int = Field(..., gt=0, description="House ID to switch to")


class SwitchHouseResponse(BaseModel):
    """Response for switch-house"""
    status: str  # "HOUSE_SWITCHED"
    from_house_id: Optional[int]
    from_house_code: Optional[str]
    to_house_id: int
    to_house_code: str


class ResidentMeWithHouseResponse(BaseModel):
    """Current resident info with active house context"""
    user_id: int
    phone: str
    active_house_id: Optional[int] = None
    active_house_code: Optional[str] = None
    memberships: List[HouseMembershipInfo]


# --- R.3 Helper Functions ---

def get_resident_token_payload(request: Request, db: Session = None) -> dict:
    """
    Extract and verify resident token from cookie.
    Returns payload dict or raises HTTPException.
    
    Phase D.2: If db is provided, validates session_version for session revocation.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="กรุณาเข้าสู่ระบบ"
        )
    
    payload = verify_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session หมดอายุ กรุณาเข้าสู่ระบบใหม่"
        )
    
    if payload.get("role") != "resident":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="เฉพาะลูกบ้านเท่านั้น"
        )
    
    # Phase D.2: Validate session_version if db is provided
    if db is not None:
        user_id = int(payload.get("user_id"))
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            token_session_version = payload.get("session_version")
            if token_session_version is not None and token_session_version != user.session_version:
                logger.warning(f"[SESSION_REVOKED] User {user_id}: token_version={token_session_version}, db_version={user.session_version}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="SESSION_REVOKED"
                )
    
    return payload


def validate_house_membership(
    db: Session,
    user_id: int,
    house_id: int
) -> tuple:
    """
    Validate that user has ACTIVE membership to house.
    Returns (membership, house) or raises HTTPException 403.
    
    SYNC version for SQLAlchemy 1.x style.
    """
    membership = db.query(ResidentMembership)\
        .options(joinedload(ResidentMembership.house))\
        .filter(
            ResidentMembership.user_id == user_id,
            ResidentMembership.house_id == house_id,
            ResidentMembership.status == ResidentMembershipStatus.ACTIVE
        )\
        .first()
    
    if not membership:
        logger.warning(f"[R.3] User {user_id} attempted access to house {house_id} without ACTIVE membership")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="คุณไม่มีสิทธิ์เข้าถึงบ้านนี้"
        )
    
    if not membership.house:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบข้อมูลบ้าน"
        )
    
    return membership, membership.house


def create_house_audit_log(
    db: Session,
    event_type: str,
    user_id: int,
    request: Request,
    house_id: Optional[int] = None,
    house_code: Optional[str] = None,
    from_house_id: Optional[int] = None,
    from_house_code: Optional[str] = None,
    to_house_id: Optional[int] = None,
    to_house_code: Optional[str] = None,
):
    """
    Create audit log entry for house selection events.
    
    SYNC version for SQLAlchemy 1.x style.
    """
    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:500]  # Truncate
    
    audit_log = ResidentHouseAuditLog(
        event_type=event_type,
        user_id=user_id,
        house_id=house_id,
        house_code=house_code,
        from_house_id=from_house_id,
        from_house_code=from_house_code,
        to_house_id=to_house_id,
        to_house_code=to_house_code,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    
    logger.info(f"[R.3 Audit] {event_type}: user={user_id}, house={house_id or to_house_id}")


# --- R.3 Endpoints ---

@router.get("/houses", response_model=HouseListResponse)
def list_resident_houses(request: Request, db: Session = Depends(get_db)):
    """
    List houses that the resident has access to.
    
    Returns only ACTIVE memberships.
    Does NOT auto-select - frontend must call select-house.
    """
    payload = get_resident_token_payload(request, db)
    user_id = int(payload.get("user_id"))
    
    # Get active memberships
    memberships = db.query(ResidentMembership)\
        .options(joinedload(ResidentMembership.house))\
        .filter(
            ResidentMembership.user_id == user_id,
            ResidentMembership.status == ResidentMembershipStatus.ACTIVE
        )\
        .order_by(ResidentMembership.created_at.desc())\
        .all()
    
    houses = [
        HouseListItem(
            house_id=m.house_id,
            house_code=m.house.house_code if m.house else f"House#{m.house_id}"
        )
        for m in memberships
        if m.house  # Only include if house exists
    ]
    
    logger.info(f"[R.3] User {user_id} listed {len(houses)} houses")
    
    return HouseListResponse(houses=houses)


@router.post("/select-house", response_model=SelectHouseResponse)
def select_house(
    request: Request,
    body: SelectHouseRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Select a house to operate.
    
    - Validates house_id is in user's ACTIVE memberships
    - Binds active_house_id to session/token
    - Regenerates token to prevent session fixation
    - Creates audit log
    """
    payload = get_resident_token_payload(request, db)
    user_id = int(payload.get("user_id"))
    
    # Validate membership
    membership, house = validate_house_membership(db, user_id, body.house_id)
    
    # Create new token with active_house_id
    new_token_data = {
        "sub": str(user_id),
        "role": "resident",
        "house_id": house.id,  # JWT uses house_id, verify_token extracts it
    }
    
    access_token = create_access_token(data=new_token_data)
    refresh_token = create_refresh_token(data={
        "sub": str(user_id),
        "role": "resident",
        "house_id": house.id,
    })
    csrf_token = generate_csrf_token()
    
    # Set new cookies (regenerate to prevent fixation)
    set_auth_cookies(response, access_token, refresh_token, csrf_token)
    
    # Create audit log
    create_house_audit_log(
        db=db,
        event_type="HOUSE_SELECTED",
        user_id=user_id,
        request=request,
        house_id=house.id,
        house_code=house.house_code,
    )
    db.commit()
    
    logger.info(f"[R.3] User {user_id} selected house {house.id} ({house.house_code})")
    
    return SelectHouseResponse(
        status="HOUSE_SELECTED",
        house_id=house.id,
        house_code=house.house_code
    )


@router.post("/switch-house", response_model=SwitchHouseResponse)
def switch_house(
    request: Request,
    body: SwitchHouseRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Switch to a different house.
    
    - Similar to select-house but tracks from/to for audit
    - Validates new house_id is in user's ACTIVE memberships
    - Regenerates token
    - Creates audit log with from_house and to_house
    """
    payload = get_resident_token_payload(request, db)
    user_id = int(payload.get("user_id"))
    
    # Get current house context (may be None if first selection)
    current_house_id = payload.get("house_id")
    
    # Look up current house code if we have a house_id
    current_house_code = None
    if current_house_id:
        current_house = db.query(House).filter(House.id == current_house_id).first()
        if current_house:
            current_house_code = current_house.house_code
    
    # Validate new house membership
    membership, new_house = validate_house_membership(db, user_id, body.house_id)
    
    # Prevent switching to same house
    if current_house_id == new_house.id:
        return SwitchHouseResponse(
            status="HOUSE_SWITCHED",
            from_house_id=current_house_id,
            from_house_code=current_house_code,
            to_house_id=new_house.id,
            to_house_code=new_house.house_code
        )
    
    # Create new token with new active_house_id
    new_token_data = {
        "sub": str(user_id),
        "role": "resident",
        "house_id": new_house.id,
    }
    
    access_token = create_access_token(data=new_token_data)
    refresh_token = create_refresh_token(data={
        "sub": str(user_id),
        "role": "resident",
        "house_id": new_house.id,
    })
    csrf_token = generate_csrf_token()
    
    # Set new cookies
    set_auth_cookies(response, access_token, refresh_token, csrf_token)
    
    # Create audit log with from/to
    create_house_audit_log(
        db=db,
        event_type="HOUSE_SWITCH",
        user_id=user_id,
        request=request,
        from_house_id=current_house_id,
        from_house_code=current_house_code,
        to_house_id=new_house.id,
        to_house_code=new_house.house_code,
    )
    db.commit()
    
    logger.info(f"[R.3] User {user_id} switched from house {current_house_id} to {new_house.id}")
    
    return SwitchHouseResponse(
        status="HOUSE_SWITCHED",
        from_house_id=current_house_id,
        from_house_code=current_house_code,
        to_house_id=new_house.id,
        to_house_code=new_house.house_code
    )


@router.get("/me/context", response_model=ResidentMeWithHouseResponse)
def get_resident_me_with_context(request: Request, db: Session = Depends(get_db)):
    """
    Get current resident info with active house context.
    
    Use this to check if resident has selected a house.
    """
    payload = get_resident_token_payload(request, db)
    user_id = int(payload.get("user_id"))
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบข้อมูลผู้ใช้"
        )
    
    # Get memberships
    memberships = get_resident_memberships(db, user_id)
    
    # Get active house from token
    house_id = payload.get("house_id")
    house_code = None
    if house_id:
        house = db.query(House).filter(House.id == house_id).first()
        if house:
            house_code = house.house_code
    
    return ResidentMeWithHouseResponse(
        user_id=user.id,
        phone=mask_phone(user.phone or ""),
        active_house_id=house_id,
        active_house_code=house_code,
        memberships=memberships
    )


# --- R.3 Dependency for requiring active house context ---

def require_active_house(request: Request, db: Session = Depends(get_db)) -> dict:
    """
    Dependency that requires active_house_id in session.
    
    Phase D.2: Also validates session_version for session revocation.
    
    Use this in future resident endpoints:
    
    @router.get("/some-resident-endpoint")
    def some_endpoint(context: dict = Depends(require_active_house)):
        house_id = context["active_house_id"]
        ...
    """
    payload = get_resident_token_payload(request, db)
    
    active_house_id = payload.get("house_id")
    if not active_house_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="กรุณาเลือกบ้านก่อนดำเนินการ"
        )
    
    return {
        "user_id": int(payload.get("user_id")),
        "role": payload.get("role"),
        "active_house_id": active_house_id,
    }
