from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

# Password hashing - switch to argon2 to avoid bcrypt issues
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY  # Will add this to config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    try:
        # Truncate password to 72 bytes for bcrypt compatibility
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        
        # DEBUG: Log password verification attempt
        print(f"[DEBUG] Verifying password...")
        print(f"[DEBUG] Plain password length: {len(plain_password)}")
        print(f"[DEBUG] Hash starts with: {hashed_password[:30]}...")
        
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"[DEBUG] Verification result: {result}")
        return result
    except Exception as e:
        # Fallback: simple password comparison for development
        print(f"[ERROR] Password verification error: {e}")
        import traceback
        traceback.print_exc()
        # For testing purposes, check if it's a simple password
        if hashed_password.startswith('$'):  # It's actually hashed
            return False
        return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Truncate password to 72 bytes for bcrypt compatibility
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        token_data = {
            "user_id": user_id,
            "role": payload.get("role"),
            "house_id": payload.get("house_id")
        }
        return token_data
    except JWTError:
        return None


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
    """Create a JWT token for a user"""
    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "email": user.email
    }
    
    # Add house_id for resident users
    if user.role == "resident" and house_id:
        token_data["house_id"] = house_id
    
    return create_access_token(token_data)


def require_role(allowed_roles: list):
    """Dependency function to require specific roles"""
    def role_checker(current_user):
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