"""
Phase 5.3: Audit Log API

Purpose:
- Provide API endpoints for viewing audit logs in admin UI
- Combines export audit logs and resident house audit logs
- READ ONLY — no data mutation

Endpoints:
- GET /api/audit-logs/exports      — Export audit logs
- GET /api/audit-logs/house-events — Resident house selection/switch logs
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.core.deps import require_admin_or_accounting
from app.db.models import User
from app.db.models.export_audit_log import ExportAuditLog
from app.db.models.resident_house_audit import ResidentHouseAuditLog

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("/exports")
async def list_export_logs(
    page: Optional[int] = Query(None, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting),
):
    """List export audit logs with pagination"""
    query = db.query(ExportAuditLog).order_by(desc(ExportAuditLog.exported_at))

    total = query.count()

    if page is not None:
        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()
    else:
        logs = query.all()

    return {
        "items": [log.to_dict() for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/house-events")
async def list_house_audit_logs(
    page: Optional[int] = Query(None, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    days: int = Query(30, ge=1, le=365, description="Show logs from last N days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting),
):
    """List resident house selection/switch audit logs"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = db.query(ResidentHouseAuditLog).filter(
        ResidentHouseAuditLog.created_at >= cutoff
    )

    if event_type:
        query = query.filter(ResidentHouseAuditLog.event_type == event_type)

    query = query.order_by(desc(ResidentHouseAuditLog.created_at))
    total = query.count()

    if page is not None:
        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()
    else:
        logs = query.all()

    return {
        "items": [log.to_dict() for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
