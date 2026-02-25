"""
Phase D.1 + Phase 4.2: Health, Readiness, and System Status Endpoints

/health - Basic liveness check (no DB, fast)
/ready - Readiness check with DB connectivity
/api/system/status - Full system status for Dashboard (Phase 4.2)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import time
import platform

from app.core.deps import require_admin_or_accounting
from app.db.models.user import User

logger = logging.getLogger(__name__)

# Track app start time for uptime calculation
_APP_START_TIME = time.time()

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check - NO database connection.
    Used by Railway/K8s for liveness probe.
    Must always respond quickly.
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check():
    """
    Phase D.1: Readiness check with DB connectivity.
    Used to verify the app is ready to serve traffic.
    
    Checks:
    - Database connectivity (light query)
    
    Returns 200 if ready, 503 if not.
    """
    from fastapi import HTTPException, status
    
    checks = {
        "database": "unknown"
    }
    
    try:
        # Lightweight DB check - just verify connection
        from app.db.session import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            # Simple query - SELECT 1
            result = db.execute(text("SELECT 1")).scalar()
            checks["database"] = "ok" if result == 1 else "error"
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"[READY] Database check failed: {e}")
        checks["database"] = "error"
    
    # Overall status
    all_ok = all(v == "ok" for v in checks.values())
    
    if not all_ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": checks}
        )
    
    return {"status": "ready", "checks": checks}


@router.get("/api/system/status")
async def system_status(
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Phase 4.2: Full system status for Admin Dashboard.
    Requires admin or accounting role.
    
    Returns real-time status of:
    - Backend API (always ok if this responds)
    - Database connectivity + response time
    - App uptime
    - Version info
    """
    from app.core.config import settings
    
    result = {
        "backend_api": {
            "status": "online",
            "app_name": settings.APP_NAME,
            "environment": settings.ENV,
            "python_version": platform.python_version(),
        },
        "database": {
            "status": "unknown",
            "response_time_ms": None,
        },
        "uptime": {
            "seconds": round(time.time() - _APP_START_TIME),
            "started_at": datetime.utcfromtimestamp(_APP_START_TIME).isoformat() + "Z",
            "human": _format_uptime(time.time() - _APP_START_TIME),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    # Database check with timing
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            start = time.time()
            db_result = db.execute(text("SELECT 1")).scalar()
            elapsed_ms = round((time.time() - start) * 1000, 1)
            
            result["database"]["status"] = "connected" if db_result == 1 else "error"
            result["database"]["response_time_ms"] = elapsed_ms
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"[SYSTEM_STATUS] Database check failed: {e}")
        result["database"]["status"] = "disconnected"
        result["database"]["error"] = "Connection failed"
    
    return result


def _format_uptime(seconds: float) -> str:
    """Format uptime seconds into human-readable string"""
    seconds = int(seconds)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)
