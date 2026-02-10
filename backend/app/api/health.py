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


@router.get("/debug/db-check")
async def debug_db_check():
    """
    TEMPORARY debug endpoint to verify DB connectivity and user existence.
    REMOVE after debugging is complete.
    """
    import os
    result = {
        "env": os.getenv("ENV", "not-set"),
        "database_url_prefix": "",
        "db_connection": "unknown",
        "tables_exist": False,
        "user_count": 0,
        "admin_users": [],
        "run_prod_seed": os.getenv("RUN_PROD_SEED", "not-set"),
        "prod_reset_pw": os.getenv("PROD_RESET_ADMIN_PASSWORD", "not-set"),
    }
    
    try:
        from app.core.config import settings
        # Show only prefix for safety
        db_url = settings.DATABASE_URL
        result["database_url_prefix"] = db_url[:50] + "..." if len(db_url) > 50 else db_url
        
        from app.db.session import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            # Test connection
            db.execute(text("SELECT 1"))
            result["db_connection"] = "ok"
            
            # Check if users table exists
            table_check = db.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
            )).scalar()
            result["tables_exist"] = bool(table_check)
            
            if table_check:
                # Count users
                count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
                result["user_count"] = count
                
                # List admin users (email + role only, no passwords)
                admins = db.execute(text(
                    "SELECT id, email, role, is_active, LEFT(hashed_password, 15) as hash_prefix "
                    "FROM users WHERE role IN ('super_admin', 'admin', 'accounting') "
                    "ORDER BY id"
                )).fetchall()
                
                result["admin_users"] = [
                    {
                        "id": row[0],
                        "email": row[1],
                        "role": row[2],
                        "is_active": row[3],
                        "hash_prefix": row[4],
                    }
                    for row in admins
                ]
                
                # Also check if admin@moobaan.com exists specifically  
                target = db.execute(text(
                    "SELECT id, email, role, is_active, LEFT(hashed_password, 20) as hash_prefix "
                    "FROM users WHERE email = 'admin@moobaan.com'"
                )).fetchone()
                
                if target:
                    result["target_admin"] = {
                        "id": target[0],
                        "email": target[1],
                        "role": target[2],
                        "is_active": target[3],
                        "hash_prefix": target[4],
                    }
                else:
                    result["target_admin"] = "NOT FOUND"
        finally:
            db.close()
    except Exception as e:
        result["error"] = str(e)
    
    return result


@router.post("/debug/fix-admin")
async def debug_fix_admin():
    """
    TEMPORARY: One-time fix to update admin email and password.
    REMOVE after admin login is working.
    """
    import os
    try:
        from app.db.session import SessionLocal
        from app.db.models.user import User
        from app.core.auth import get_password_hash
        
        target_email = os.getenv("PROD_ADMIN_EMAIL", "admin@moobaan.com")
        target_password = os.getenv("PROD_ADMIN_PASSWORD", "")
        
        if not target_password:
            return {"error": "PROD_ADMIN_PASSWORD not set"}
        
        db = SessionLocal()
        try:
            # Find existing super_admin (any email)
            admin = db.query(User).filter(User.role == "super_admin").first()
            
            if not admin:
                # No admin exists, create one
                admin = User(
                    email=target_email,
                    full_name="System Administrator",
                    hashed_password=get_password_hash(target_password),
                    role="super_admin",
                    is_active=True,
                    phone="0800000000",
                )
                db.add(admin)
                db.commit()
                return {
                    "action": "created",
                    "email": target_email,
                    "id": admin.id,
                }
            
            # Admin exists - update email and password
            old_email = admin.email
            admin.email = target_email
            admin.hashed_password = get_password_hash(target_password)
            admin.is_active = True
            db.commit()
            
            return {
                "action": "updated",
                "old_email": old_email,
                "new_email": target_email,
                "id": admin.id,
                "password_hash_prefix": admin.hashed_password[:20],
            }
        finally:
            db.close()
    except Exception as e:
        return {"error": str(e)}