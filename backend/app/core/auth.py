from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request
from app.core.config import settings
import logging
import secrets
import os

logger = logging.getLogger(__name__)

# Password hashing - switch to argon2 to avoid bcrypt issues
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY  # Will add this to config
ALGORITHM = "HS256"

# --- Phase D.1: Role-based Session TTL ---
# Admin/Accounting: Short-lived (8 hours) - high privilege = tighter security
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ADMIN_ACCESS_TOKEN_MINUTES", "15"))
ADMIN_REFRESH_TOKEN_EXPIRE_HOURS = int(os.getenv("ADMIN_REFRESH_TOKEN_HOURS", "8"))

# Resident: Long-lived (7 days) - mobile-first UX, lower privilege
RESIDENT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESIDENT_ACCESS_TOKEN_MINUTES", "60"))
RESIDENT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("RESIDENT_REFRESH_TOKEN_DAYS", "7"))

# Legacy defaults (backward compat)
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access token
REFRESH_TOKEN_EXPIRE_DAYS = 7    # Long-lived refresh token

# Cookie settings (from config)
COOKIE_SECURE = settings.COOKIE_SECURE  # True in production (HTTPS)
# SameSite=None required for cross-origin cookies (Vercel frontend → Railway backend)
# SameSite=lax for same-origin (local development)
COOKIE_SAMESITE = "none" if settings.ENV in ["production", "prod"] else "lax"
COOKIE_DOMAIN = None  # None = current domain only


def get_token_expiry_for_role(role: str, token_type: str = "access") -> timedelta:
    """
    Phase D.1: Get token expiry based on role.
    
    Admin/Accounting: Short sessions (security-focused)
    - Access: 15 min
    - Refresh: 8 hours
    
    Resident: Long sessions (UX-focused for mobile)
    - Access: 60 min
    - Refresh: 7 days
    """
    if role in ["super_admin", "admin", "accounting"]:
        if token_type == "access":
            return timedelta(minutes=ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            return timedelta(hours=ADMIN_REFRESH_TOKEN_EXPIRE_HOURS)
    else:  # resident or others
        if token_type == "access":
            return timedelta(minutes=RESIDENT_ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            return timedelta(days=RESIDENT_REFRESH_TOKEN_EXPIRE_DAYS)


def get_cookie_max_age_for_role(role: str, token_type: str = "access") -> int:
    """Phase D.1: Get cookie max_age in seconds based on role"""
    expiry = get_token_expiry_for_role(role, token_type)
    return int(expiry.total_seconds())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    try:
        # Truncate password to 72 bytes for bcrypt compatibility
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        
        logger.info(f"Verifying password: len={len(plain_password)}, hash_prefix={hashed_password[:20]}")
        result = pwd_context.verify(plain_password, hashed_password)
        logger.info(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Truncate password to 72 bytes for bcrypt compatibility
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, role: str = None):
    """
    Create a JWT access token.
    Phase D.1: Role-aware expiry
    """
    to_encode = data.copy()
    
    # Determine expiry based on role or use provided delta
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Phase D.1: Use role-based expiry
        effective_role = role or data.get("role", "resident")
        expire = datetime.now(timezone.utc) + get_token_expiry_for_role(effective_role, "access")
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, role: str = None) -> str:
    """
    Create a JWT refresh token (longer-lived).
    Phase D.1: Role-aware expiry
    """
    to_encode = data.copy()
    
    # Phase D.1: Use role-based expiry
    effective_role = role or data.get("role", "resident")
    expire = datetime.now(timezone.utc) + get_token_expiry_for_role(effective_role, "refresh")
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    PATCH-2 rev: Also accepts token_type="pending" for house-selection flow.
    Returns token_type in dict so callers can guard against pending tokens.
    
    FIX: Pending tokens with purpose="link_account" may NOT have a 'sub' field
    (user doesn't exist yet). Return the full payload for pending tokens.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        actual_type = payload.get("type")
        # Verify token type matches expected
        if actual_type != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {actual_type}")
            return None
        
        user_id = payload.get("sub")
        
        # For pending tokens, sub may be absent (e.g. link_account flow)
        if user_id is None and token_type != "pending":
            return None
        
        token_data = {
            "user_id": user_id,
            "role": payload.get("role"),
            "house_id": payload.get("house_id"),
            "session_version": payload.get("session_version"),  # Phase D.2
            "token_type": actual_type,  # PATCH-2 rev: expose for pending guard
            "purpose": payload.get("purpose"),  # FIX: expose purpose for link_account
        }
        return token_data
    except JWTError as e:
        logger.debug(f"JWT verification failed: {e}")
        return None


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token"""
    return secrets.token_urlsafe(32)


def authenticate_user(email: str, password: str, db) -> Union[object, bool]:
    """Authenticate a user by email and password"""
    from app.db.models.user import User
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    if not user.is_active:
        return False
    return user


def create_user_token(user, house_id: Optional[int] = None) -> str:
    """Create a JWT token for a user. PATCH-6: includes session_version."""
    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "email": user.email,
        "session_version": user.session_version,  # PATCH-6
    }
    
    # Add house_id for resident users
    if user.role == "resident" and house_id:
        token_data["house_id"] = house_id
    
    return create_access_token(token_data)


def require_role(allowed_roles: list):
    """Dependency function to require specific roles"""
    from app.core.deps import get_current_user
    from fastapi import Depends as _Depends
    def role_checker(current_user=_Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


async def require_house_access(house_id: int, current_user, db):
    """Check if user can access house data"""
    from app.db.models import House, HouseMember
    
    # Super admin and accounting can access any house
    if current_user.role in ["super_admin", "accounting"]:
        return True
    
    # For residents, check house access and status
    if current_user.role == "resident":
        # Check if user is member of this house
        house_member = db.query(HouseMember).filter(
            HouseMember.user_id == current_user.id,
            HouseMember.house_id == house_id
        ).first()
        
        if not house_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not a member of this house."
            )
        
        # Check if house status allows resident access
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="House not found"
            )
        
        if not house.can_resident_access():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. House status does not allow resident access."
            )
        
        return True
    
    # Deny access for any other role
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )