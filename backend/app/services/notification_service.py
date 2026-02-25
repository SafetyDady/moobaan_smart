"""
Phase 5.1: Notification Service

Purpose:
- Create notifications for various events
- Query notifications for a user
- Mark notifications as read

Usage:
    from app.services.notification_service import NotificationService
    NotificationService.notify_payin_accepted(db, user_id, payin_id, amount)
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.db.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and managing in-app notifications"""

    # ─── Creation Methods ───────────────────────────────────────────────

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
    ) -> Notification:
        """Create a new notification"""
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        db.add(notif)
        db.flush()  # Get ID without committing
        logger.info(f"📬 Notification created: [{type.value}] for user {user_id}")
        return notif

    @staticmethod
    def notify_invoice_created(
        db: Session, user_id: int, invoice_id: int, amount: float, period: str
    ) -> Notification:
        """Notify resident that a new invoice was created"""
        return NotificationService.create(
            db=db,
            user_id=user_id,
            type=NotificationType.INVOICE_CREATED,
            title="ใบแจ้งหนี้ใหม่",
            message=f"คุณมีใบแจ้งหนี้ใหม่ งวด {period} จำนวน ฿{amount:,.0f}",
            reference_type="invoice",
            reference_id=invoice_id,
        )

    @staticmethod
    def notify_payin_submitted(
        db: Session, admin_user_ids: List[int], payin_id: int,
        house_code: str, amount: float
    ) -> List[Notification]:
        """Notify admins that a resident submitted a payin"""
        notifications = []
        for admin_id in admin_user_ids:
            notif = NotificationService.create(
                db=db,
                user_id=admin_id,
                type=NotificationType.PAYIN_SUBMITTED,
                title="แจ้งชำระเงินใหม่",
                message=f"บ้าน {house_code} แจ้งชำระเงิน ฿{amount:,.0f} รอตรวจสอบ",
                reference_type="payin",
                reference_id=payin_id,
            )
            notifications.append(notif)
        return notifications

    @staticmethod
    def notify_payin_accepted(
        db: Session, user_id: int, payin_id: int, amount: float
    ) -> Notification:
        """Notify resident that their payin was accepted"""
        return NotificationService.create(
            db=db,
            user_id=user_id,
            type=NotificationType.PAYIN_ACCEPTED,
            title="ยืนยันการชำระเงิน",
            message=f"การชำระเงิน ฿{amount:,.0f} ได้รับการยืนยันแล้ว",
            reference_type="payin",
            reference_id=payin_id,
        )

    @staticmethod
    def notify_payin_rejected(
        db: Session, user_id: int, payin_id: int, reason: str
    ) -> Notification:
        """Notify resident that their payin was rejected"""
        return NotificationService.create(
            db=db,
            user_id=user_id,
            type=NotificationType.PAYIN_REJECTED,
            title="การชำระเงินถูกปฏิเสธ",
            message=f"การชำระเงินถูกปฏิเสธ: {reason}",
            reference_type="payin",
            reference_id=payin_id,
        )

    @staticmethod
    def notify_system(
        db: Session, user_id: int, title: str, message: str
    ) -> Notification:
        """Create a system notification"""
        return NotificationService.create(
            db=db,
            user_id=user_id,
            type=NotificationType.SYSTEM,
            title=title,
            message=message,
        )

    # ─── Query Methods ──────────────────────────────────────────────────

    @staticmethod
    def get_user_notifications(
        db: Session, user_id: int, unread_only: bool = False,
        limit: int = 50, offset: int = 0
    ) -> tuple:
        """
        Get notifications for a user.
        Returns (notifications, total_count, unread_count)
        """
        base_query = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_deleted == False,
            )
        )

        unread_count = base_query.filter(Notification.is_read == False).count()
        
        if unread_only:
            query = base_query.filter(Notification.is_read == False)
        else:
            query = base_query

        total = query.count()
        notifications = (
            query
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return notifications, total, unread_count

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
        """Mark a single notification as read"""
        notif = db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.is_deleted == False,
            )
        ).first()

        if not notif:
            return False

        notif.is_read = True
        notif.read_at = datetime.utcnow()
        return True

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all notifications as read for a user. Returns count updated."""
        count = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_deleted == False,
            )
        ).update({
            Notification.is_read: True,
            Notification.read_at: datetime.utcnow(),
        })
        return count

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Get unread notification count for a user"""
        return db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_deleted == False,
            )
        ).count()
