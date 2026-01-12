from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.dashboard import router as dashboard_router
from app.api.houses import router as houses_router
from app.api.members import router as members_router
from app.api.invoices import router as invoices_router
from app.api.payins import router as payins_router
from app.api.expenses import router as expenses_router
from app.api.bank_statements import router as bank_statements_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)

# CORS middleware for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://moobaan-smart.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(houses_router)
app.include_router(members_router)
app.include_router(invoices_router)
app.include_router(payins_router)
app.include_router(expenses_router)
app.include_router(bank_statements_router)


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "status": "running"}