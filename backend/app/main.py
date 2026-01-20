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
from app.api.expenses import router as expenses_router
from app.api.bank_accounts import router as bank_accounts_router
from app.api.bank_statements import router as bank_statements_router
from app.api.bank_reconciliation import router as bank_reconciliation_router
from app.api.auth import router as auth_router
from app.api.accounting import router as accounting_router
from app.api.users import router as users_router

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
        "x-requested-with"
    ],
    expose_headers=["*"],
    max_age=86400,
)

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