"""
Phase 5.1: Notification API Endpoints

Endpoints:
- GET  /api/notifications          — List notifications for current user
- GET  /api/notifications/count    — Get unread count only
- POST /api/notifications/{id}/read — Mark single notification as read
- POST /api/notifications/read-all  — Mark all notifications as read
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.deps import require_user
from app.db.models.user import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    unread_only: bool = Query(False, description="Filter to unread only"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    List notifications for the current user.
    Returns notifications sorted by newest first.
    """
    notifications, total, unread_count = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )

    return {
        "items": [n.to_dict() for n in notifications],
        "total": total,
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset,
    }


@router.get("/count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Get unread notification count for badge display"""
    count = NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Mark a single notification as read"""
    success = NotificationService.mark_as_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.commit()
    return {"success": True}


@router.post("/read-all")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Mark all notifications as read for the current user"""
    count = NotificationService.mark_all_as_read(db, current_user.id)
    db.commit()
    return {"success": True, "count": count}
