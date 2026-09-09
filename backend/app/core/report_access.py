"""House-scoped report access using the resident's selected-house session."""
from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.deps import get_current_user, get_db, get_house_id_from_token
from app.db.models import User
from app.db.models.resident_membership import ResidentMembership, ResidentMembershipStatus


def require_report_house_access(
    house_id: int,
    current_user: User = Depends(get_current_user),
    token_house_id: Optional[int] = Depends(get_house_id_from_token),
    db: Session = Depends(get_db),
) -> User:
    """Recheck active membership; never infer the selected house from the DB."""
    if current_user.role in ('super_admin', 'accounting'):
        return current_user
    if current_user.role != 'resident':
        raise HTTPException(403, 'Access denied')
    if token_house_id is None:
        raise HTTPException(403, {'code': 'HOUSE_NOT_SELECTED', 'message': 'กรุณาเลือกบ้านก่อนใช้งาน'})
    if token_house_id != house_id:
        raise HTTPException(403, 'Access denied to this house')
    membership = db.query(ResidentMembership).options(joinedload(ResidentMembership.house)).filter(
        ResidentMembership.user_id == current_user.id,
        ResidentMembership.house_id == house_id,
        ResidentMembership.status == ResidentMembershipStatus.ACTIVE,
    ).first()
    if not membership or not membership.house or not membership.house.can_resident_access():
        raise HTTPException(403, 'Access denied to this house')
    return current_user
