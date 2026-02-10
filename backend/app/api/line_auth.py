"""
Phase D.4.1: LINE Login API Endpoints

Purpose:
- LINE OAuth login for residents
- Residents enter ONLY via LINE OA

Flow:
1. POST /api/auth/line/login with authorization code
2. Verify with LINE API → get line_user_id
3. Find user by line_user_id
4. Validate: user exists, role=resident, has ACTIVE membership
5. Issue JWT session (60 days)

Error Codes:
- 403 NOT_REGISTERED_RESIDENT: LINE user not registered or no membership

IMPORTANT:
- NO user creation
- NO OTP
- NO phone anchor
- NO accounting logic
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Response, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus
from app.services.line_auth import get_line_auth_service, get_line_login_url, LINEAuthConfig
from app.core.auth import (
    create_access_token, 
    create_refresh_token, 
    generate_csrf_token,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/line", tags=["LINE Auth"])


# --- Phase D.4.1: Session TTL = 60 days for residents via LINE ---
RESIDENT_LINE_SESSION_DAYS = int(os.getenv("RESIDENT_LINE_SESSION_DAYS", "60"))


# --- Request/Response Models ---

class LINELoginRequest(BaseModel):
    """LINE Login request with authorization code"""
    code: str
    redirect_uri: str


class LINELoginResponse(BaseModel):
    """LINE Login response"""
    success: bool
    message: str  # "เข้าสู่ระบบสำเร็จ" or "SELECT_HOUSE_REQUIRED"
    user_id: Optional[int] = None
    display_name: Optional[str] = None
    house_id: Optional[int] = None
    house_code: Optional[str] = None
    houses: Optional[list] = None


class LINEConfigResponse(BaseModel):
    """LINE OAuth configuration for frontend"""
    channel_id: str
    login_url: str


# --- Helper Functions ---

def _set_auth_cookies(
    response: Response, 
    access_token: str, 
    refresh_token: str, 
    csrf_token: str
):
    """
    Set authentication cookies for LINE login session.
    
    Phase D.4.1: 60-day session for residents
    """
    from datetime import timedelta
    
    # 60-day session for LINE residents
    access_max_age = int(timedelta(days=RESIDENT_LINE_SESSION_DAYS).total_seconds())
    refresh_max_age = int(timedelta(days=RESIDENT_LINE_SESSION_DAYS).total_seconds())
    
    # Access token cookie (httpOnly)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=access_max_age,
        path="/"
    )
    
    # Refresh token cookie (httpOnly)
    # PATCH-1: Normalized path = /api/auth (covers /api/auth/refresh)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/api/auth"
    )
    
    # CSRF token cookie (readable by JavaScript)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/"
    )


def _get_user_houses(db: Session, user_id: int) -> list:
    """Get user's active house memberships"""
    from app.db.models.house import House
    
    memberships = db.query(ResidentMembership).filter(
        ResidentMembership.user_id == user_id,
        ResidentMembership.status == ResidentMembershipStatus.ACTIVE
    ).all()
    
    houses = []
    for m in memberships:
        house = db.query(House).filter(House.id == m.house_id).first()
        if house:
            houses.append({
                "id": house.id,
                "house_code": house.house_code,
                "address": getattr(house, 'address', None),
                "role": m.role.value if hasattr(m.role, 'value') else m.role,
            })
    
    return houses


def _create_pending_token(data: dict, ttl_minutes: int = 10) -> str:
    """
    PATCH-2 rev: Create a short-lived 'pending' token for house selection.
    
    - type = "pending" (not "access")
    - No house_id
    - Short TTL (default 10 minutes)
    - Cannot be used to access /api/auth/me or /api/auth/refresh
    """
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    to_encode.update({"exp": expire, "type": "pending"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- Endpoints ---

@router.get("/config", response_model=LINEConfigResponse)
def get_line_config(redirect_uri: str):
    """
    Get LINE OAuth configuration for frontend.
    
    Frontend uses this to redirect to LINE authorization.
    """
    if not LINEAuthConfig.CHANNEL_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LINE Login not configured"
        )
    
    login_url = get_line_login_url(redirect_uri=redirect_uri)
    
    return LINEConfigResponse(
        channel_id=LINEAuthConfig.CHANNEL_ID,
        login_url=login_url
    )


@router.post("/login", response_model=LINELoginResponse)
def line_login(
    request: LINELoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    LINE OAuth Login for residents.
    
    Phase D.4.1 Flow:
    1. Verify authorization code with LINE API
    2. Get line_user_id from LINE profile
    3. Find user by line_user_id
    4. Validate:
       - User exists
       - User role == "resident"
       - User has at least 1 ACTIVE resident_membership
    5. Issue JWT session (60 days)
    
    Error Codes:
    - 403 NOT_REGISTERED_RESIDENT: Not registered or no membership
    - 400 LINE_AUTH_FAILED: LINE API verification failed
    """
    code = request.code
    redirect_uri = request.redirect_uri
    
    logger.info(f"[LINE_LOGIN] Processing login request")
    
    # Step 1: Verify with LINE API
    line_service = get_line_auth_service()
    success, profile, error = line_service.verify_and_get_profile(code, redirect_uri)
    
    if not success:
        logger.warning(f"[LINE_LOGIN] LINE verification failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "LINE_AUTH_FAILED",
                "message": error or "LINE authentication failed"
            }
        )
    
    line_user_id = profile.user_id
    logger.info(f"[LINE_LOGIN] LINE verified: {line_user_id[:8]}...")
    
    # Step 2: Find user by line_user_id
    user = db.query(User).filter(User.line_user_id == line_user_id).first()
    
    if not user:
        logger.warning(f"[LINE_LOGIN] User not found for LINE ID: {line_user_id[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NOT_REGISTERED_RESIDENT",
                "message": "บัญชีนี้ยังไม่ได้รับสิทธิ์ใช้งาน กรุณาติดต่อผู้ดูแลหมู่บ้าน"
            }
        )
    
    # Step 3: Validate user role
    if user.role != "resident":
        logger.warning(f"[LINE_LOGIN] User {user.id} is not a resident: {user.role}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NOT_REGISTERED_RESIDENT",
                "message": "บัญชีนี้ไม่ใช่บัญชีลูกบ้าน"
            }
        )
    
    # Step 4: Validate active membership exists
    # PATCH-2: Query as list (not count) to determine house_id
    active_memberships = db.query(ResidentMembership).filter(
        ResidentMembership.user_id == user.id,
        ResidentMembership.status == ResidentMembershipStatus.ACTIVE
    ).all()
    
    if len(active_memberships) == 0:
        logger.warning(f"[LINE_LOGIN] User {user.id} has no active memberships")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NOT_REGISTERED_RESIDENT",
                "message": "บัญชีนี้ยังไม่ได้รับสิทธิ์ใช้งาน กรุณาติดต่อผู้ดูแลหมู่บ้าน"
            }
        )
    
    # Step 5: Check user is active
    if not user.is_active:
        logger.warning(f"[LINE_LOGIN] User {user.id} is deactivated")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NOT_REGISTERED_RESIDENT",
                "message": "บัญชีนี้ถูกระงับการใช้งาน กรุณาติดต่อผู้ดูแลหมู่บ้าน"
            }
        )
    
    # Step 6: Issue tokens — PATCH-2 revised (select-house flow)
    from datetime import timedelta
    from app.db.models.house import House as HouseModel
    
    houses = _get_user_houses(db, user.id)
    display_name = user.full_name or user.username or profile.display_name
    
    # ── Case A: Single house → full JWT immediately ──
    if len(active_memberships) == 1:
        selected_house_id = active_memberships[0].house_id
        h = db.query(HouseModel).filter(HouseModel.id == selected_house_id).first()
        selected_house_code = h.house_code if h else None
        
        token_data = {
            "sub": str(user.id),
            "role": "resident",
            "line_user_id": line_user_id,
            "session_version": user.session_version,
            "house_id": selected_house_id,
        }
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(days=RESIDENT_LINE_SESSION_DAYS)
        )
        refresh_tok = create_refresh_token(
            data={"sub": str(user.id), "role": "resident",
                  "session_version": user.session_version,
                  "house_id": selected_house_id},
            role="resident"
        )
        csrf_token = generate_csrf_token()
        _set_auth_cookies(response, access_token, refresh_tok, csrf_token)
        
        logger.info(f"[LINE_LOGIN] Case A: user {user.id}, single house {selected_house_id}")
        return LINELoginResponse(
            success=True,
            message="เข้าสู่ระบบสำเร็จ",
            user_id=user.id,
            display_name=display_name,
            house_id=selected_house_id,
            house_code=selected_house_code,
            houses=houses,
        )
    
    # ── Case B: Multi house → pending token, NO house_id, NO refresh ──
    pending_token_data = {
        "sub": str(user.id),
        "role": "resident",
        "line_user_id": line_user_id,
        "session_version": user.session_version,
        # NO house_id — invariant: resident token ห้ามมี house_id ถ้ายังไม่เลือกบ้าน
    }
    PENDING_TTL_MINUTES = 10
    pending_token = _create_pending_token(pending_token_data, ttl_minutes=PENDING_TTL_MINUTES)
    
    # Set ONLY access_token cookie (pending), NO refresh_token
    response.set_cookie(
        key="access_token",
        value=pending_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=PENDING_TTL_MINUTES * 60,
        path="/"
    )
    # CSRF for the pending session
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=PENDING_TTL_MINUTES * 60,
        path="/"
    )
    
    logger.info(f"[LINE_LOGIN] Case B: user {user.id}, {len(active_memberships)} houses → SELECT_HOUSE_REQUIRED")
    
    # Return SELECT_HOUSE_REQUIRED status so frontend redirects to /select-house
    return LINELoginResponse(
        success=True,
        message="SELECT_HOUSE_REQUIRED",
        user_id=user.id,
        display_name=display_name,
        house_id=None,
        house_code=None,
        houses=houses,
    )
