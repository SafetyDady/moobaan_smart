from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY  # Will add this to config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
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