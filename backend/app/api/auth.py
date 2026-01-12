from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Hardcoded users for Phase 1
USERS_DB = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # In production, use hashed passwords
        "role": "super_admin",
        "name": "Super Administrator",
        "house_id": None,
    },
    "accounting": {
        "username": "accounting",
        "password": "acc123",
        "role": "accounting",
        "name": "Accounting Staff",
        "house_id": None,
    },
    "resident": {
        "username": "resident",
        "password": "res123",
        "role": "resident",
        "name": "Resident User",
        "house_id": 1,  # Linked to house A-101
    },
}

# Mock token storage (in-memory for Phase 1)
ACTIVE_TOKENS = {}


class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False


class AuthResponse(BaseModel):
    token: str
    user: dict
    expires_at: str


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login endpoint with hardcoded users.
    Phase 1: Mock authentication
    Phase 2: Replace with real JWT and database lookup
    """
    user = USERS_DB.get(request.username)
    
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Generate mock token
    token = secrets.token_urlsafe(32)
    
    # Set expiration (7 days if remember_me, otherwise 1 day)
    expires_in = timedelta(days=7 if request.remember_me else 1)
    expires_at = datetime.now() + expires_in
    
    # Store token (in-memory for Phase 1)
    ACTIVE_TOKENS[token] = {
        "username": user["username"],
        "role": user["role"],
        "expires_at": expires_at,
    }
    
    # Return user info (without password)
    user_data = {
        "username": user["username"],
        "name": user["name"],
        "role": user["role"],
        "house_id": user.get("house_id"),
    }
    
    return AuthResponse(
        token=token,
        user=user_data,
        expires_at=expires_at.isoformat(),
    )


@router.post("/logout")
async def logout(token: str):
    """
    Logout endpoint - invalidate token.
    """
    if token in ACTIVE_TOKENS:
        del ACTIVE_TOKENS[token]
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/verify")
async def verify_token(token: str):
    """
    Verify if token is still valid.
    Used by frontend to check authentication state.
    """
    token_data = ACTIVE_TOKENS.get(token)
    
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Check if token expired
    if datetime.now() > token_data["expires_at"]:
        del ACTIVE_TOKENS[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    # Get user data
    user = USERS_DB.get(token_data["username"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    user_data = {
        "username": user["username"],
        "name": user["name"],
        "role": user["role"],
        "house_id": user.get("house_id"),
    }
    
    return {"valid": True, "user": user_data}
