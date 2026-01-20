"""
Phase G.1: Period Lock Validation Helper

This module provides helper functions for validating period locks
before allowing changes to historical data.
"""
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import PeriodSnapshot, PeriodStatus


def check_period_locked(db: Session, target_date: date) -> bool:
    """
    Check if the period containing the target date is locked.
    
    Args:
        db: Database session
        target_date: The date to check
        
    Returns:
        True if the period is locked, False otherwise
    """
    if not target_date:
        return False
        
    snapshot = db.query(PeriodSnapshot).filter(
        PeriodSnapshot.period_year == target_date.year,
        PeriodSnapshot.period_month == target_date.month,
        PeriodSnapshot.status == PeriodStatus.LOCKED
    ).first()
    
    return snapshot is not None


def validate_period_not_locked(db: Session, target_date: date, entity_name: str = "record"):
    """
    Validate that the period is not locked. Raises HTTPException if locked.
    
    Args:
        db: Database session
        target_date: The date to check
        entity_name: Name of the entity for error message (e.g., "invoice", "expense")
        
    Raises:
        HTTPException: If the period is locked
    """
    if not target_date:
        return
        
    if check_period_locked(db, target_date):
        period_label = f"{target_date.year}-{str(target_date.month).zfill(2)}"
        raise HTTPException(
            status_code=403,
            detail=f"Cannot modify {entity_name}: Period {period_label} is locked. "
                   f"Contact super_admin to unlock if needed."
        )


def get_period_status(db: Session, year: int, month: int) -> dict:
    """
    Get the status of a period.
    
    Args:
        db: Database session
        year: Year of the period
        month: Month of the period (1-12)
        
    Returns:
        Dict with period status info
    """
    snapshot = db.query(PeriodSnapshot).filter(
        PeriodSnapshot.period_year == year,
        PeriodSnapshot.period_month == month
    ).first()
    
    if not snapshot:
        return {
            "exists": False,
            "is_locked": False,
            "status": None
        }
    
    return {
        "exists": True,
        "is_locked": snapshot.status == PeriodStatus.LOCKED,
        "status": snapshot.status.value
    }
