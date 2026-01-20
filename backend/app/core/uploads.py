"""
File upload utility for slip images.
Saves files to local disk in uploads/ folder and serves via /uploads endpoint.
For production, consider using S3 or similar cloud storage.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import UploadFile

# Upload directory relative to project root
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"

# Ensure uploads directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


async def save_slip_file(file, house_id: int) -> str:
    """
    Save uploaded slip file to disk.
    Returns relative URL path (e.g., /uploads/slips/123_20240115_abc123.jpg)
    
    Args:
        file: The uploaded file
        house_id: The house ID for filename prefix
        
    Returns:
        URL path to access the file
    """
    if not file:
        return None
    
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Create slips subdirectory
    slips_dir = UPLOAD_DIR / "slips"
    slips_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename: {house_id}_{timestamp}_{uuid}.{ext}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{house_id}_{timestamp}_{unique_id}{ext}"
    
    file_path = slips_dir / safe_filename
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Return URL path (relative to /uploads mount point)
    return f"/uploads/slips/{safe_filename}"


def delete_slip_file(file_url: str) -> bool:
    """
    Delete slip file from disk.
    
    Args:
        file_url: The URL path returned by save_slip_file
        
    Returns:
        True if file was deleted, False otherwise
    """
    if not file_url or not file_url.startswith("/uploads/"):
        return False
    
    # Convert URL to file path
    relative_path = file_url.replace("/uploads/", "")
    file_path = UPLOAD_DIR / relative_path
    
    try:
        if file_path.exists():
            os.remove(file_path)
            return True
    except Exception:
        pass
    
    return False


def get_upload_dir() -> Path:
    """Get the uploads directory path for StaticFiles mount."""
    return UPLOAD_DIR
