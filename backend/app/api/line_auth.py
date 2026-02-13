"""
Phase D.4.1 + R.3: LINE Login API Endpoints

Purpose:
- LINE OAuth login for residents
- Self-service LINE account linking (Controlled — admin must pre-create resident)

Flow:
1. POST /api/auth/line/login with authorization code
2. Verify with LINE API → get line_user_id
3a. Found user → validate role/membership → issue JWT (60 days)
3b. Not found → return NEED_LINK + pending token (line_user_id inside)
4. POST /api/auth/line/link-account with phone + house_code
   → match admin-created resident → write line_user_id → issue JWT

Security Rules:
- NO user creation from LINE (admin must pre-create)
- NO override if line_user_id already bound
- Must match: phone + house_code + ACTIVE membership
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from pydantic import BaseModel, Field
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
    message: str  # "เข้าสู่ระบบสำเร็จ" / "SELECT_HOUSE_REQUIRED" / "NEED_LINK"
    user_id: Optional[int] = None
    display_name: Optional[str] = None
    house_id: Optional[int] = None
    house_code: Optional[str] = None
    houses: Optional[list] = None


class LINELinkAccountRequest(BaseModel):
    """Request to link LINE account to existing resident"""
    phone: str = Field(..., min_length=9, max_length=15)
    house_code: str = Field(..., min_length=1, max_length=30)


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
        # R.3: LINE user not bound yet → issue NEED_LINK pending token
        logger.info(f"[LINE_LOGIN] No user bound to LINE ID {line_user_id[:8]}... → NEED_LINK")
        
        LINK_TTL_MINUTES = 10
        link_token_data = {
            "line_user_id": line_user_id,
            "line_display_name": profile.display_name or "",
            "purpose": "link_account",
        }
        link_token = _create_pending_token(link_token_data, ttl_minutes=LINK_TTL_MINUTES)
        
        # Set pending token as cookie so /link-account can read it
        response.set_cookie(
            key="access_token",
            value=link_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=LINK_TTL_MINUTES * 60,
            path="/"
        )
        csrf_token = generate_csrf_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=LINK_TTL_MINUTES * 60,
            path="/"
        )
        
        return LINELoginResponse(
            success=True,
            message="NEED_LINK",
            display_name=profile.display_name,
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


# ─────────────────────────────────────────────────────────────
# R.3: Link LINE Account to existing Resident
# ─────────────────────────────────────────────────────────────

@router.post("/link-account")
def link_line_account(
    request_obj: Request,
    body: LINELinkAccountRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    R.3: Controlled self-service LINE account linking.
    
    Precondition: Caller has a pending cookie token with purpose=link_account
                  (issued by /login when line_user_id not found).
    
    Rules:
    1. NO user creation — must match admin-created resident
    2. NO override — if user.line_user_id is already set → 409
    3. Must match phone + house_code + ACTIVE membership
    """
    from jose import jwt, JWTError
    from app.core.auth import SECRET_KEY, ALGORITHM
    from app.db.models.house import House as HouseModel
    from datetime import timedelta
    
    # ── Step 1: Read pending token from cookie ──
    token = request_obj.cookies.get("access_token")
    if not token:
        logger.warning("[LINK_ACCOUNT] No access_token cookie found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NO_TOKEN", "message": "กรุณาเข้าสู่ระบบผ่าน LINE ก่อน"}
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        logger.warning(f"[LINK_ACCOUNT] Token decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "เซสชันหมดอายุ กรุณาเข้าสู่ระบบผ่าน LINE ใหม่"}
        )
    
    # Must be a pending token with purpose=link_account
    token_type = payload.get("type")
    token_purpose = payload.get("purpose")
    logger.info(f"[LINK_ACCOUNT] Token type={token_type}, purpose={token_purpose}, keys={list(payload.keys())}")
    
    if token_type != "pending" or token_purpose != "link_account":
        logger.warning(f"[LINK_ACCOUNT] Wrong token: type={token_type}, purpose={token_purpose}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": "Token ไม่ถูกต้อง กรุณาเข้าสู่ระบบผ่าน LINE ใหม่"}
        )
    
    line_user_id = payload.get("line_user_id")
    if not line_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": "ไม่พบข้อมูล LINE"}
        )
    
    # ── Step 2: Normalize phone ──
    phone = body.phone.strip().replace("-", "").replace(" ", "")
    house_code = body.house_code.strip()
    
    logger.info(f"[LINK_ACCOUNT] Attempting link: phone={phone[-4:]}, house={house_code}")
    
    # ── Step 3: Find house by house_code ──
    house = db.query(HouseModel).filter(HouseModel.house_code == house_code).first()
    if not house:
        logger.warning(f"[LINK_ACCOUNT] House not found: {house_code}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "ไม่พบข้อมูล กรุณาตรวจสอบเบอร์โทรและบ้านเลขที่"}
        )
    
    # ── Step 4: Find resident user by phone ──
    user = db.query(User).filter(
        User.phone == phone,
        User.role == "resident",
        User.is_active == True,
    ).first()
    
    if not user:
        logger.warning(f"[LINK_ACCOUNT] No resident with phone {phone[-4:]}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "ไม่พบข้อมูล กรุณาตรวจสอบเบอร์โทรและบ้านเลขที่"}
        )
    
    # ── Step 5: Verify ACTIVE membership for this house ──
    membership = db.query(ResidentMembership).filter(
        ResidentMembership.user_id == user.id,
        ResidentMembership.house_id == house.id,
        ResidentMembership.status == ResidentMembershipStatus.ACTIVE
    ).first()
    
    if not membership:
        logger.warning(f"[LINK_ACCOUNT] User {user.id} has no ACTIVE membership for house {house.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "ไม่พบข้อมูล กรุณาตรวจสอบเบอร์โทรและบ้านเลขที่"}
        )
    
    # ── Step 6: Check line_user_id not already bound (ห้าม override) ──
    if user.line_user_id and user.line_user_id != line_user_id:
        logger.warning(f"[LINK_ACCOUNT] User {user.id} already bound to different LINE account")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_LINKED", "message": "บัญชีนี้ผูกกับ LINE อื่นอยู่แล้ว กรุณาติดต่อผู้ดูแลหมู่บ้าน"}
        )
    
    # Also check: is this line_user_id already used by another user?
    existing_line_user = db.query(User).filter(
        User.line_user_id == line_user_id,
        User.id != user.id,
    ).first()
    if existing_line_user:
        logger.warning(f"[LINK_ACCOUNT] LINE ID already used by user {existing_line_user.id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "LINE_ALREADY_USED", "message": "LINE นี้ผูกกับบัญชีอื่นอยู่แล้ว"}
        )
    
    # ── Step 7: Bind line_user_id ──
    user.line_user_id = line_user_id
    db.commit()
    logger.info(f"[LINK_ACCOUNT] ✅ Bound LINE {line_user_id[:8]}... → user {user.id} ({user.full_name})")
    
    # ── Step 8: Issue full JWT (same logic as single-house login) ──
    houses = _get_user_houses(db, user.id)
    display_name = user.full_name or payload.get("line_display_name", "")
    
    # Count active memberships to decide single vs multi-house
    active_memberships = db.query(ResidentMembership).filter(
        ResidentMembership.user_id == user.id,
        ResidentMembership.status == ResidentMembershipStatus.ACTIVE
    ).all()
    
    if len(active_memberships) == 1:
        # Single house → full JWT immediately
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
        
        return LINELoginResponse(
            success=True,
            message="เข้าสู่ระบบสำเร็จ",
            user_id=user.id,
            display_name=display_name,
            house_id=selected_house_id,
            house_code=selected_house_code,
            houses=houses,
        )
    
    else:
        # Multi-house → pending token for house selection
        pending_token_data = {
            "sub": str(user.id),
            "role": "resident",
            "line_user_id": line_user_id,
            "session_version": user.session_version,
        }
        PENDING_TTL_MINUTES = 10
        pending_token = _create_pending_token(pending_token_data, ttl_minutes=PENDING_TTL_MINUTES)
        
        response.set_cookie(
            key="access_token", value=pending_token,
            httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
            max_age=PENDING_TTL_MINUTES * 60, path="/"
        )
        csrf_token = generate_csrf_token()
        response.set_cookie(
            key="csrf_token", value=csrf_token,
            httponly=False, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
            max_age=PENDING_TTL_MINUTES * 60, path="/"
        )
        
        return LINELoginResponse(
            success=True,
            message="SELECT_HOUSE_REQUIRED",
            user_id=user.id,
            display_name=display_name,
            houses=houses,
        )
