from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.auth import verify_token
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.house_member import HouseMember

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(token_data["user_id"])).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


def require_roles(allowed_roles: List[str]):
    """Dependency factory to require specific roles"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker


# Common role dependencies
require_user = Depends(get_current_user)
require_resident = Depends(require_roles(["resident"]))
require_accounting = Depends(require_roles(["accounting", "super_admin"]))
require_admin = Depends(require_roles(["super_admin"]))
require_admin_or_accounting = Depends(require_roles(["accounting", "super_admin"]))


def get_user_house_id(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Optional[int]:
    """Get the house_id for the current user if they are a resident"""
    if current_user.role != "resident":
        return None
    
    house_member = db.query(HouseMember).filter(HouseMember.user_id == current_user.id).first()
    return house_member.house_id if house_member else None


def require_resident_of_house(house_id: int):
    """Dependency factory to ensure user is a resident of specific house"""
    def house_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if current_user.role == "super_admin":
            return current_user  # Super admin can access any house
        
        if current_user.role != "resident":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only residents can access house-specific data"
            )
        
        house_member = db.query(HouseMember).filter(
            HouseMember.user_id == current_user.id,
            HouseMember.house_id == house_id
        ).first()
        
        if not house_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this house's data"
            )
        
        return current_user
    return house_checker