"""
Phase D.1: Health and Readiness Endpoints

/health - Basic liveness check (no DB, fast)
/ready - Readiness check with DB connectivity (optional)
"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

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