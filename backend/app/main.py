from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

# Configure logging EARLY
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import and validate config FIRST - FAIL FAST
try:
    from app.core.config import settings
    from app.core.uploads import get_upload_dir
    logger.info(f"✅ Configuration loaded successfully for {settings.APP_NAME}")
except Exception as e:
    logger.error(f"❌ Configuration validation failed: {e}")
    raise

from app.api.health import router as health_router
from app.api.dashboard import router as dashboard_router
from app.api.houses import router as houses_router
from app.api.members import router as members_router
from app.api.invoices import router as invoices_router
from app.api.payins import router as payins_router
from app.api.payin_state import router as payin_state_router
from app.api.expenses_v2 import router as expenses_router  # Phase F.1: Expense Core
from app.api.bank_accounts import router as bank_accounts_router
from app.api.bank_statements import router as bank_statements_router
from app.api.bank_reconciliation import router as bank_reconciliation_router
from app.api.auth import router as auth_router
from app.api.accounting import router as accounting_router
from app.api.users import router as users_router
from app.api.credit_notes import router as credit_notes_router
from app.api.promotions import router as promotions_router
from app.api.reports import router as reports_router
from app.api.accounts import router as accounts_router  # Phase F.2: Chart of Accounts
from app.api.periods import router as periods_router  # Phase G.1: Period Closing
from app.api.export import router as export_router  # Phase G.2: Accounting Export
from app.api.resident_auth import router as resident_auth_router  # Phase R.2: Resident OTP Login

app = FastAPI(title=settings.APP_NAME)

# CORS middleware for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://127.0.0.1:5173",
        "http://localhost:5174",
        "https://localhost:5174", 
        "http://127.0.0.1:5174",
        "https://127.0.0.1:5174",
        "http://localhost:5175",
        "https://localhost:5175", 
        "http://127.0.0.1:5175",
        "https://127.0.0.1:5175",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://moobaan-smart.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "accept",
        "accept-encoding",
        "authorization",
        "content-type",
        "dnt",
        "origin",
        "user-agent",
        "x-csrftoken",
        "x-csrf-token",  # Our custom CSRF header
        "x-requested-with"
    ],
    expose_headers=["*"],
    max_age=86400,
)


# CSRF Protection Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse

class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection using double-submit cookie pattern.
    For POST/PUT/DELETE/PATCH requests:
    - Check that X-CSRF-Token header matches csrf_token cookie
    - Skip for auth login endpoint (no token yet) and logout
    """
    EXEMPT_PATHS = [
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/refresh",
        "/api/resident/login",  # Phase R.2: Resident OTP login
        "/api/resident/logout",  # Phase R.2: Resident logout
        "/docs",
        "/openapi.json",
        "/",
    ]
    
    async def dispatch(self, request: StarletteRequest, call_next):
        # Only check CSRF for state-changing methods
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Skip exempt paths
            if not any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
                csrf_cookie = request.cookies.get("csrf_token")
                csrf_header = request.headers.get("X-CSRF-Token")
                
                # Only enforce if user has a CSRF cookie (logged in via cookie)
                if csrf_cookie and csrf_cookie != csrf_header:
                    # Log warning but don't block yet (for backward compatibility)
                    logger.warning(f"CSRF token mismatch: cookie={csrf_cookie[:8]}..., header={csrf_header[:8] if csrf_header else 'None'}...")
                    # Uncomment below to enforce CSRF (after testing):
                    # return JSONResponse(
                    #     status_code=403,
                    #     content={"detail": "CSRF token mismatch"}
                    # )
        
        response = await call_next(request)
        return response

# Add CSRF middleware (after CORS)
app.add_middleware(CSRFMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(houses_router)
app.include_router(members_router)
app.include_router(invoices_router)
app.include_router(payins_router)
app.include_router(payin_state_router)
app.include_router(expenses_router)
app.include_router(bank_accounts_router)
app.include_router(bank_statements_router)
app.include_router(bank_reconciliation_router)
app.include_router(accounting_router)
app.include_router(users_router)
app.include_router(credit_notes_router)
app.include_router(promotions_router)
app.include_router(reports_router)
app.include_router(accounts_router)
app.include_router(periods_router)
app.include_router(export_router)  # Phase G.2: Accounting Export
app.include_router(resident_auth_router)  # Phase R.2: Resident OTP Login

# Mount static files for uploaded slips
# This serves files at /uploads/* from the uploads/ directory
uploads_dir = get_upload_dir()
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
    logger.info(f"📁 Static files mounted at /uploads from {uploads_dir}")
else:
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
    logger.info(f"📁 Created uploads directory and mounted at /uploads")


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "status": "running"}