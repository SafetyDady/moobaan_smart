from fastapi import APIRouter
from app.models import DashboardSummary
from app.mock_data import MOCK_DASHBOARD_SUMMARY

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """Get dashboard summary statistics"""
    return MOCK_DASHBOARD_SUMMARY
