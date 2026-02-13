"""
Attachments API — operational evidence storage.

Endpoints:
- POST /api/attachments/presign   — get presigned PUT URL + create attachment record
- POST /api/attachments/confirm   — mark upload as confirmed (optional)
- GET  /api/attachments           — list attachments for an entity
- DELETE /api/attachments/{id}    — soft delete

Business Rules:
- PAYIN  → file_type must be SLIP
- EXPENSE → INVOICE only when status=PENDING, RECEIPT only when status=PAID
- Backend never proxies uploads — presigned URLs only
- Soft delete (is_deleted=true), never physical delete
- Immutable after reconcile: matched payin attachments cannot be deleted

RBAC: super_admin, accounting (list/presign/delete)
       resident can upload SLIP for their own payin (future)
"""
import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import boto3
from botocore.config import Config as BotoConfig

from app.db.session import get_db
from app.core.deps import require_role
from app.db.models.user import User
from app.db.models.expense import Expense, ExpenseStatus
from app.db.models.payin_report import PayinReport
from app.db.models.attachment import Attachment
from app.db.models.expense_bank_allocation import ExpenseBankAllocation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

# ===== Allowed combinations =====
VALID_FILE_TYPES = {
    "PAYIN": ["SLIP"],
    "EXPENSE": ["INVOICE", "RECEIPT"],
}

ALLOWED_CONTENT_TYPES = [
    "image/jpeg", "image/png", "image/webp", "image/heic",
    "application/pdf",
]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ===== R2 Client =====

def _get_r2_client():
    endpoint = os.getenv("R2_ENDPOINT")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    if not all([endpoint, access_key, secret_key]):
        raise HTTPException(status_code=500, detail="R2 storage not configured")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=BotoConfig(signature_version="s3v4"),
    )


def _get_public_url(object_key: str) -> str:
    public_url = os.getenv("R2_PUBLIC_URL", "")
    if public_url:
        return f"{public_url.rstrip('/')}/{object_key}"
    return ""


# ===== Schemas =====

class PresignRequest(BaseModel):
    entity_type: str = Field(..., description="PAYIN or EXPENSE")
    entity_id: int = Field(..., gt=0)
    file_type: str = Field(..., description="SLIP, INVOICE, or RECEIPT")
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type: image/jpeg, application/pdf, etc.")


class PresignResponse(BaseModel):
    attachment_id: str
    upload_url: str
    object_key: str
    public_url: str
    expires_in: int


class AttachmentOut(BaseModel):
    id: str
    entity_type: str
    entity_id: int
    file_type: str
    original_filename: Optional[str]
    content_type: Optional[str]
    object_key: str
    file_size: Optional[int]
    public_url: str
    created_at: Optional[str]


# ===== POST /api/attachments/presign =====

@router.post("/presign", response_model=PresignResponse)
async def get_presigned_upload_url(
    data: PresignRequest,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Validate business rules, create attachment record, return presigned PUT URL.
    Client uploads directly to R2 — backend never touches the file.
    """
    entity_type = data.entity_type.upper()
    file_type = data.file_type.upper()
    content_type = data.content_type.lower()

    # Validate entity_type + file_type combination
    if entity_type not in VALID_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid entity_type: {entity_type}. Must be PAYIN or EXPENSE")
    if file_type not in VALID_FILE_TYPES[entity_type]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file_type '{file_type}' for {entity_type}. Allowed: {VALID_FILE_TYPES[entity_type]}"
        )

    # Validate content type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}. Allowed: {ALLOWED_CONTENT_TYPES}")

    # Validate entity exists + business rules
    if entity_type == "EXPENSE":
        expense = db.query(Expense).filter(Expense.id == data.entity_id).first()
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        if expense.status == ExpenseStatus.CANCELLED:
            raise HTTPException(status_code=400, detail="Cannot attach files to cancelled expenses")
        if file_type == "INVOICE" and expense.status != ExpenseStatus.PENDING:
            raise HTTPException(status_code=400, detail="INVOICE can only be attached to PENDING expenses")
        if file_type == "RECEIPT" and expense.status != ExpenseStatus.PAID:
            raise HTTPException(status_code=400, detail="RECEIPT can only be attached to PAID expenses")

    elif entity_type == "PAYIN":
        payin = db.query(PayinReport).filter(PayinReport.id == data.entity_id).first()
        if not payin:
            raise HTTPException(status_code=404, detail="Pay-in report not found")

    # Generate R2 object key
    ext = data.filename.rsplit(".", 1)[-1] if "." in data.filename else "bin"
    unique_id = uuid.uuid4().hex[:12]
    object_key = f"attachments/{entity_type.lower()}/{data.entity_id}/{file_type.lower()}_{unique_id}.{ext}"

    # Create attachment record
    attachment = Attachment(
        entity_type=entity_type,
        entity_id=data.entity_id,
        file_type=file_type,
        original_filename=data.filename,
        content_type=content_type,
        object_key=object_key,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    # Generate presigned URL
    bucket = os.getenv("R2_BUCKET_NAME", "moobaan-smart-production")
    client = _get_r2_client()
    upload_url = client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=300,  # 5 minutes
    )

    return PresignResponse(
        attachment_id=str(attachment.id),
        upload_url=upload_url,
        object_key=object_key,
        public_url=_get_public_url(object_key),
        expires_in=300,
    )


# ===== GET /api/attachments =====

@router.get("/")
async def list_attachments(
    entity_type: str = Query(..., description="PAYIN or EXPENSE"),
    entity_id: int = Query(..., gt=0),
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """List non-deleted attachments for an entity."""
    rows = (
        db.query(Attachment)
        .filter(
            Attachment.entity_type == entity_type.upper(),
            Attachment.entity_id == entity_id,
            Attachment.is_deleted == False,
        )
        .order_by(Attachment.created_at.desc())
        .all()
    )

    result = []
    for a in rows:
        d = a.to_dict()
        d["public_url"] = _get_public_url(a.object_key)
        result.append(d)

    return result


# ===== DELETE /api/attachments/{id} =====

@router.delete("/{attachment_id}")
async def soft_delete_attachment(
    attachment_id: str,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Soft delete an attachment.
    Cannot delete if payin is already matched (immutable after reconcile).
    Cannot delete if expense has bank allocations (immutable after reconcile).
    """
    try:
        att_uuid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid attachment ID")

    att = db.query(Attachment).filter(Attachment.id == att_uuid, Attachment.is_deleted == False).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Immutability check: PAYIN — if matched, block delete
    if att.entity_type == "PAYIN":
        from app.db.models.bank_transaction import BankTransaction
        matched = db.query(BankTransaction).filter(
            BankTransaction.matched_payin_id == att.entity_id
        ).first()
        if matched:
            raise HTTPException(status_code=400, detail="Cannot delete attachment — pay-in is already matched with a bank transaction")

    # Immutability check: EXPENSE — if has allocation, block delete for RECEIPT
    if att.entity_type == "EXPENSE" and att.file_type == "RECEIPT":
        alloc_count = db.query(ExpenseBankAllocation).filter(
            ExpenseBankAllocation.expense_id == att.entity_id
        ).count()
        if alloc_count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete receipt — expense has bank allocations")

    att.is_deleted = True
    db.commit()

    return {"success": True, "message": "Attachment deleted"}
