"""
File upload utility for slip images.

Production: Uploads to Cloudflare R2 via boto3 (S3-compatible).
Local dev:  Falls back to local disk if R2 env vars not set.

R2 env vars (same as attachments):
  R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME
  R2_PUBLIC_URL (optional — for direct public URLs)
"""
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Upload directory relative to project root (local fallback)
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def _r2_configured() -> bool:
    """Check if R2 environment variables are set."""
    return all([
        os.getenv("R2_ENDPOINT"),
        os.getenv("R2_ACCESS_KEY_ID"),
        os.getenv("R2_SECRET_ACCESS_KEY"),
    ])


def _get_r2_client():
    """Create boto3 S3 client configured for Cloudflare R2."""
    import boto3
    from botocore.config import Config as BotoConfig
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
        config=BotoConfig(signature_version="s3v4"),
    )


async def save_slip_file(file, house_id: int) -> str:
    """
    Save uploaded slip file.

    Production (R2 configured):
        Uploads to R2 bucket under key ``slips/{house}_{ts}_{uuid}.ext``.
        Returns the object key (NOT a full URL).

    Local dev (R2 not configured):
        Saves to ``uploads/slips/`` and returns ``/uploads/slips/…`` path.

    Args:
        file: The uploaded file (FastAPI UploadFile)
        house_id: The house ID for filename prefix

    Returns:
        R2 object key **or** local ``/uploads/slips/…`` path.
    """
    if not file:
        return None

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{house_id}_{timestamp}_{unique_id}{ext}"

    content = await file.read()

    # ── R2 path ──
    if _r2_configured():
        object_key = f"slips/{safe_filename}"
        bucket = os.getenv("R2_BUCKET_NAME", "moobaan-smart-production")
        try:
            client = _get_r2_client()
            # Determine content type
            content_type = "image/jpeg"
            ct_map = {".png": "image/png", ".gif": "image/gif",
                      ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
            content_type = ct_map.get(ext, "image/jpeg")

            client.put_object(
                Bucket=bucket,
                Key=object_key,
                Body=content,
                ContentType=content_type,
            )
            logger.info(f"✅ Slip uploaded to R2: {object_key} ({len(content)} bytes)")
            return object_key  # store key, not full URL
        except Exception as e:
            logger.error(f"❌ R2 upload failed, falling back to local: {e}")
            # Fall through to local save

    # ── Local fallback ──
    slips_dir = UPLOAD_DIR / "slips"
    slips_dir.mkdir(parents=True, exist_ok=True)
    file_path = slips_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)
    logger.info(f"📁 Slip saved locally: {file_path}")
    return f"/uploads/slips/{safe_filename}"


def get_slip_download_url(slip_url: str, expires_in: int = 3600) -> Optional[str]:
    """
    Generate a download URL for a stored slip.

    - If ``slip_url`` starts with ``/uploads/`` → old local path, return as-is.
    - If ``slip_url`` starts with ``http`` → already a full URL, return as-is.
    - Otherwise → treat as R2 object key, generate presigned GET URL.

    Args:
        slip_url: Value stored in ``payin.slip_url``
        expires_in: Presigned URL lifetime in seconds (default 1 hour)

    Returns:
        A URL the browser can open to view the slip, or None.
    """
    if not slip_url:
        return None

    # Already a full URL (legacy or R2 public)
    if slip_url.startswith("http"):
        return slip_url

    # Old local path
    if slip_url.startswith("/uploads/"):
        return slip_url

    # Treat as R2 object key
    if not _r2_configured():
        logger.warning(f"Slip is R2 key but R2 not configured: {slip_url}")
        return None

    # Prefer R2_PUBLIC_URL if set (permanent, no expiry)
    public_url = os.getenv("R2_PUBLIC_URL", "").strip()
    if public_url:
        return f"{public_url.rstrip('/')}/{slip_url}"

    # Generate presigned GET URL
    bucket = os.getenv("R2_BUCKET_NAME", "moobaan-smart-production")
    try:
        client = _get_r2_client()
        url = client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": slip_url},
            ExpiresIn=expires_in,
        )
        return url
    except Exception as e:
        logger.error(f"❌ Failed to generate presigned URL for {slip_url}: {e}")
        return None


def delete_slip_file(file_url: str) -> bool:
    """
    Delete slip file from local disk (legacy).
    R2 objects are not deleted (soft-delete at DB level is sufficient).
    """
    if not file_url or not file_url.startswith("/uploads/"):
        return False

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
