"""
Phase 4 — Task 4.1: Server-side Pagination Utility

Provides reusable pagination helpers for all API endpoints.

Usage:
    from app.core.pagination import PaginationParams, paginate_query, PaginatedResponse

    @router.get("/items")
    async def list_items(
        page: int = Query(None, ge=1, description="Page number (1-indexed). Omit for all results."),
        page_size: int = Query(25, ge=1, le=100, description="Items per page"),
        db: Session = Depends(get_db),
    ):
        query = db.query(Item)
        # ... apply filters ...
        return paginate_query(query, page, page_size)

Backward Compatibility:
    - If `page` is None (not provided), returns ALL items (same as before Phase 4)
    - If `page` is provided, returns paginated response with metadata
"""
from typing import Optional, Any, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query


class PaginatedResponse(BaseModel):
    """Standard paginated response format"""
    items: List[Any]
    total: int = Field(..., description="Total number of items matching the query")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


def paginate_query(
    query: Query,
    page: Optional[int] = None,
    page_size: int = 25,
    transform_fn=None,
) -> dict:
    """
    Apply pagination to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object (with filters/ordering already applied)
        page: Page number (1-indexed). None = return all items (backward compatible)
        page_size: Items per page (default 25, max 100)
        transform_fn: Optional function to transform each item (e.g., item.to_dict())
    
    Returns:
        If page is None: List of all items (backward compatible)
        If page is provided: Dict with {items, total, page, page_size, total_pages}
    """
    # Backward compatible: no pagination requested → return all
    if page is None:
        items = query.all()
        if transform_fn:
            return [transform_fn(item) for item in items]
        return items
    
    # Clamp page_size
    page_size = max(1, min(page_size, 100))
    
    # Get total count (before pagination)
    total = query.count()
    
    # Calculate total pages
    total_pages = max(1, (total + page_size - 1) // page_size)
    
    # Clamp page number
    page = max(1, min(page, total_pages))
    
    # Apply offset/limit
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    # Transform items if function provided
    if transform_fn:
        items = [transform_fn(item) for item in items]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def paginate_list(
    data: list,
    page: Optional[int] = None,
    page_size: int = 25,
) -> Any:
    """
    Apply pagination to an in-memory list.
    Useful when items need complex transformation before pagination
    (e.g., invoices with calculated fields).
    
    Args:
        data: List of items (already transformed)
        page: Page number (1-indexed). None = return all items
        page_size: Items per page (default 25, max 100)
    
    Returns:
        If page is None: The original list (backward compatible)
        If page is provided: Dict with {items, total, page, page_size, total_pages}
    """
    if page is None:
        return data
    
    # Clamp page_size
    page_size = max(1, min(page_size, 100))
    
    total = len(data)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    
    offset = (page - 1) * page_size
    items = data[offset:offset + page_size]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
