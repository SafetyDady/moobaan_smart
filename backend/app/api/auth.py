from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus
from app.db.models.house import House
from app.core.auth import (
    authenticate_user, create_user_token, verify_password, get_password_hash,
    create_access_token, create_refresh_token, verify_token, generate_csrf_token,
    COOKIE_SECURE, COOKIE_SAMESITE, COOKIE_DOMAIN, REFRESH_TOKEN_EXPIRE_DAYS,
    get_cookie_max_age_for_role,  # Phase D.1
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


def set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str, role: str = "resident"):
    """
    Set httpOnly cookies for authentication.
    Phase D.1: Role-aware cookie max_age
    """
    # Phase D.1: Get role-based max_age
    access_max_age = get_cookie_max_age_for_role(role, "access")
    refresh_max_age = get_cookie_max_age_for_role(role, "refresh")
    
    # Access token - httpOnly, short-lived
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=access_max_age,
        path="/",
        domain=COOKIE_DOMAIN
    )
    
    # Refresh token - httpOnly, long-lived (role-based)
    # PATCH-1: Normalized path = /api/auth (covers /api/auth/refresh)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/api/auth",
        domain=COOKIE_DOMAIN
    )
    
    # CSRF token - NOT httpOnly (JS needs to read it)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Must be readable by JS
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/",
        domain=COOKIE_DOMAIN
    )


def clear_auth_cookies(response: Response):
    """Clear all auth cookies on logout"""
    response.delete_cookie(key="access_token", path="/", domain=COOKIE_DOMAIN)
    # PATCH-1: Normalized path = /api/auth
    response.delete_cookie(key="refresh_token", path="/api/auth", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="csrf_token", path="/", domain=COOKIE_DOMAIN)


@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token via httpOnly cookie.
    Phase D.1: Role-based session TTL
    - Admin/Accounting: 8 hours
    - Resident: 7 days
    """
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
    
    # PATCH-6: Include session_version for all roles (admin + resident)
    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "email": user.email,
        "session_version": user.session_version,
    }
    
    # PATCH-3: Admin login does NOT set house_id (admin doesn't need it)
    # Resident login via this endpoint is legacy — LINE is primary path
    
    # Create tokens (Phase D.1: role-based expiry)
    access_token = create_access_token(data=token_data)
    refresh_token_value = create_refresh_token(
        {"sub": str(user.id), "role": user.role, "session_version": user.session_version},
        role=user.role
    )
    csrf_token = generate_csrf_token()
    
    # Phase D.1: Get role-based cookie max_age
    access_max_age = get_cookie_max_age_for_role(user.role, "access")
    refresh_max_age = get_cookie_max_age_for_role(user.role, "refresh")
    
    # Create response with cookies
    response = JSONResponse(content={
        "access_token": access_token,
        "token_type": "bearer"
    })
    
    # Set httpOnly cookies on the response (Phase D.1: role-based max_age)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=access_max_age,
        path="/"
    )
    # PATCH-1: Normalized path = /api/auth
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/api/auth"
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/"
    )
    
    logger.info(f"Login successful for {user.email} (role={user.role}), cookies set with TTL={refresh_max_age}s")
    return response


@router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token from httpOnly cookie.
    Phase D.1: Role-based session TTL
    """
    refresh_token_cookie = request.cookies.get("refresh_token")
    
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )
    
    # Verify refresh token
    token_data = verify_token(refresh_token_cookie, token_type="refresh")
    if not token_data:
        # PATCH-2 rev: Also reject if someone somehow got a pending token here
        # (Pending tokens have type="pending", not "refresh", so verify_token rejects them)
        # Return response that clears cookies — PATCH-1: path=/api/auth
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
    
    # PATCH-6: Validate session_version (for all roles)
    token_session_version = token_data.get("session_version")
    if token_session_version is not None and token_session_version != user.session_version:
        logger.warning(f"[SESSION_REVOKED] Refresh blocked for user {user.id}: token_ver={token_session_version}, db_ver={user.session_version}")
        response = JSONResponse(
            status_code=401,
            content={"detail": "SESSION_REVOKED"}
        )
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/api/auth")
        response.delete_cookie(key="csrf_token", path="/")
        return response
    
    # PATCH-3: Carry forward house_id from the refresh token (no .first() fallback)
    # house_id stays in token from original login; refresh preserves it
    carried_house_id = token_data.get("house_id")
    
    # Phase D.1: Get role-based cookie max_age
    access_max_age = get_cookie_max_age_for_role(user.role, "access")
    refresh_max_age = get_cookie_max_age_for_role(user.role, "refresh")
    
    # PATCH-6: Create new tokens with session_version + carried house_id
    new_token_data = {
        "sub": str(user.id),
        "role": user.role,
        "session_version": user.session_version,
    }
    if user.email:
        new_token_data["email"] = user.email
    if carried_house_id:
        new_token_data["house_id"] = int(carried_house_id)
    
    new_access_token = create_access_token(data=new_token_data)
    new_refresh_token = create_refresh_token(
        {"sub": str(user.id), "role": user.role, "session_version": user.session_version,
         **(({"house_id": int(carried_house_id)}) if carried_house_id else {})},
        role=user.role
    )
    csrf_token = generate_csrf_token()
    
    # Create response with new cookies (Phase D.1: role-based max_age)
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
        max_age=access_max_age,
        path="/"
    )
    # PATCH-1: Normalized path = /api/auth
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/api/auth"
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/"
    )
    
    logger.info(f"Token refreshed for user {user.id} ({user.email}), role={user.role}")
    return response


import os

# PATCH-2 rev: Session TTL for residents via LINE
RESIDENT_LINE_SESSION_DAYS = int(os.getenv("RESIDENT_LINE_SESSION_DAYS", "60"))


class SelectHouseRequest(BaseModel):
    house_id: int


@router.post("/select-house")
async def select_house(
    request: Request,
    body: SelectHouseRequest,
    db: Session = Depends(get_db)
):
    """
    PATCH-2 rev: House selection endpoint for multi-house residents.
    
    Flow:
    1. Validate pending token from cookie
    2. Validate user has ACTIVE membership for selected house
    3. Issue FULL JWT (access + refresh) with house_id
    4. Invalidate pending token by overwriting cookies
    
    Returns normalized user object (PATCH-5 shape).
    """
    from jose import jwt, JWTError
    from app.core.auth import SECRET_KEY, ALGORITHM
    
    # Step 1: Read and validate pending token
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Must be a pending token OR a valid access token (for re-selection)
    token_type = payload.get("type")
    if token_type not in ("pending", "access"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type for house selection"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Step 2: Get user and validate
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    
    # Validate session_version
    token_sv = payload.get("session_version")
    if token_sv is not None and token_sv != user.session_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SESSION_REVOKED")
    
    # Step 3: Validate membership for selected house
    membership = db.query(ResidentMembership).filter(
        ResidentMembership.user_id == user.id,
        ResidentMembership.house_id == body.house_id,
        ResidentMembership.status == ResidentMembershipStatus.ACTIVE
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_HOUSE", "message": "ไม่พบสิทธิ์เข้าถึงบ้านที่เลือก"}
        )
    
    # Resolve house_code
    house = db.query(House).filter(House.id == body.house_id).first()
    house_code = house.house_code if house else None
    
    # Step 4: Issue FULL JWT with house_id
    full_token_data = {
        "sub": str(user.id),
        "role": "resident",
        "session_version": user.session_version,
        "house_id": body.house_id,
    }
    # Carry forward line_user_id if present in original token
    if payload.get("line_user_id"):
        full_token_data["line_user_id"] = payload["line_user_id"]
    
    access_token = create_access_token(
        data=full_token_data,
        expires_delta=timedelta(days=RESIDENT_LINE_SESSION_DAYS)
    )
    refresh_token_value = create_refresh_token(
        data={"sub": str(user.id), "role": "resident",
              "session_version": user.session_version,
              "house_id": body.house_id},
        role="resident"
    )
    csrf_token = generate_csrf_token()
    
    # Step 5: Set full cookies (overwrite pending token)
    from app.core.auth import get_cookie_max_age_for_role as _get_max_age
    access_max_age = int(timedelta(days=RESIDENT_LINE_SESSION_DAYS).total_seconds())
    refresh_max_age = int(timedelta(days=RESIDENT_LINE_SESSION_DAYS).total_seconds())
    
    response = JSONResponse(content={
        "success": True,
        "message": "เลือกบ้านสำเร็จ",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "role": "resident",
            "house_id": body.house_id,
            "house_code": house_code,
            "houses": _get_user_houses_list(db, user.id),
        }
    })
    
    # Access token
    response.set_cookie(
        key="access_token", value=access_token,
        httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
        max_age=access_max_age, path="/", domain=COOKIE_DOMAIN
    )
    # Refresh token (PATCH-1: path=/api/auth)
    response.set_cookie(
        key="refresh_token", value=refresh_token_value,
        httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age, path="/api/auth", domain=COOKIE_DOMAIN
    )
    # CSRF token
    response.set_cookie(
        key="csrf_token", value=csrf_token,
        httponly=False, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
        max_age=refresh_max_age, path="/", domain=COOKIE_DOMAIN
    )
    
    logger.info(f"[SELECT_HOUSE] User {user.id} selected house {body.house_id} ({house_code})")
    return response


def _get_user_houses_list(db: Session, user_id: int) -> list:
    """Get user's active house memberships (reusable helper)"""
    active_memberships = db.query(ResidentMembership).filter(
        ResidentMembership.user_id == user_id,
        ResidentMembership.status == ResidentMembershipStatus.ACTIVE
    ).all()
    houses = []
    for m in active_memberships:
        h = db.query(House).filter(House.id == m.house_id).first()
        if h:
            houses.append({
                "id": h.id,
                "house_code": h.house_code,
                "role": m.role.value if hasattr(m.role, 'value') else m.role,
            })
    return houses


@router.post("/logout")
async def logout():
    """Logout user - clear all auth cookies"""
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="access_token", path="/")
    # PATCH-1: Normalized path = /api/auth
    response.delete_cookie(key="refresh_token", path="/api/auth")
    response.delete_cookie(key="csrf_token", path="/")
    return response


@router.get("/me")
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information.
    
    PATCH-2 rev: Rejects pending tokens (house not yet selected)
    PATCH-3: house_id read from token ONLY (no .first() fallback)
    PATCH-4: Uses ResidentMembership for resident data
    PATCH-5: Returns normalized shape for all login methods
    """
    # PATCH-2 rev: Guard against pending tokens
    token = request.cookies.get("access_token")
    if token:
        from app.core.auth import verify_token as vt_raw
        from jose import jwt
        from app.core.auth import SECRET_KEY, ALGORITHM
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") == "pending":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "HOUSE_NOT_SELECTED", "message": "กรุณาเลือกบ้านก่อนเข้าใช้งาน"}
                )
        except HTTPException:
            raise
        except Exception:
            pass  # Let normal auth flow handle invalid tokens
    
    house_id = None
    house_code = None
    houses = []
    
    if current_user.role == "resident":
        # PATCH-3: Read house_id from token — NOT from DB query
        token = request.cookies.get("access_token")
        if token:
            token_data = verify_token(token, token_type="access")
            if token_data:
                house_id = token_data.get("house_id")
                if house_id:
                    house_id = int(house_id)
        
        # PATCH-4: Use ResidentMembership to get house_code and houses list
        # PATCH-7: Always load active memberships (needed for fallback + houses list)
        active_memberships = db.query(ResidentMembership).filter(
            ResidentMembership.user_id == current_user.id,
            ResidentMembership.status == ResidentMembershipStatus.ACTIVE
        ).all()
        for m in active_memberships:
            h = db.query(House).filter(House.id == m.house_id).first()
            if h:
                houses.append({
                    "id": h.id,
                    "house_code": h.house_code,
                    "role": m.role.value if hasattr(m.role, 'value') else m.role,
                })
        
        # PATCH-7 rev2: If token has no house_id but user has exactly 1 house → auto-select AND reissue JWT
        if not house_id and len(active_memberships) == 1:
            house_id = active_memberships[0].house_id
            h = db.query(House).filter(House.id == house_id).first()
            house_code = h.house_code if h else None
            logger.info(f"[AUTH_ME] Auto-selected single house {house_id} for user {current_user.id} → reissuing JWT")
            
            # Reissue JWT with house_id so old cookie is replaced
            new_token_data = {
                "sub": str(current_user.id),
                "role": "resident",
                "session_version": current_user.session_version,
                "house_id": house_id,
            }
            # Carry forward line_user_id if present
            if token:
                try:
                    old_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    if old_payload.get("line_user_id"):
                        new_token_data["line_user_id"] = old_payload["line_user_id"]
                except Exception:
                    pass
            
            new_access_token = create_access_token(
                data=new_token_data,
                expires_delta=timedelta(days=RESIDENT_LINE_SESSION_DAYS)
            )
            new_refresh_token = create_refresh_token(
                data={"sub": str(current_user.id), "role": "resident",
                      "session_version": current_user.session_version,
                      "house_id": house_id},
                role="resident"
            )
            new_csrf = generate_csrf_token()
            
            resp_data = {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "role": current_user.role,
                "is_active": current_user.is_active,
                "phone": current_user.phone,
                "house_id": house_id,
                "house_code": house_code,
                "houses": houses,
            }
            resp = JSONResponse(content=resp_data)
            access_max_age = int(timedelta(days=RESIDENT_LINE_SESSION_DAYS).total_seconds())
            resp.set_cookie(key="access_token", value=new_access_token,
                            httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
                            max_age=access_max_age, path="/", domain=COOKIE_DOMAIN)
            resp.set_cookie(key="refresh_token", value=new_refresh_token,
                            httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
                            max_age=access_max_age, path="/api/auth", domain=COOKIE_DOMAIN)
            resp.set_cookie(key="csrf_token", value=new_csrf,
                            httponly=False, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE,
                            max_age=access_max_age, path="/", domain=COOKIE_DOMAIN)
            return resp
        elif house_id:
            house = db.query(House).filter(House.id == house_id).first()
            house_code = house.house_code if house else None
    
    # PATCH-5: Normalized response shape (works for admin + resident)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "phone": current_user.phone,
        "house_id": house_id,
        "house_code": house_code,
        "houses": houses,
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for current user (admin/accounting only - residents are OTP-only)"""
    import logging
    
    logger = logging.getLogger(__name__)
    
    # BLOCK: Residents cannot change password - they are OTP-only
    if current_user.role in ["resident", "owner", "tenant"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Password change not allowed for residents",
                "error_th": "ผู้อาศัยไม่สามารถเปลี่ยนรหัสผ่านได้ กรุณาใช้ OTP ในการเข้าสู่ระบบ",
                "error_en": "Residents cannot change password. Please use OTP to login."
            }
        )
    
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
