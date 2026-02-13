"""
R2 Integration Test Endpoint (Temporary)

Generates a presigned PUT URL for Cloudflare R2 to verify connectivity.
Uses boto3 S3-compatible API with signature_version s3v4.

Env vars required on Railway:
  R2_ENDPOINT        = https://xxxx.r2.cloudflarestorage.com
  R2_ACCESS_KEY_ID   = (from Cloudflare R2 API Token)
  R2_SECRET_ACCESS_KEY = (from Cloudflare R2 API Token)
  R2_BUCKET_NAME     = moobaan-smart-production
  R2_PUBLIC_URL      = https://pub-xxxx.r2.dev
"""
import os
import logging
from fastapi import APIRouter, HTTPException
import boto3
from botocore.config import Config as BotoConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/r2", tags=["r2-test"])


def _get_r2_client():
    """Create boto3 S3 client configured for Cloudflare R2."""
    endpoint = os.getenv("R2_ENDPOINT")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")

    if not all([endpoint, access_key, secret_key]):
        raise HTTPException(
            status_code=500,
            detail="R2 not configured. Set R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY env vars."
        )

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=BotoConfig(signature_version="s3v4"),
    )


@router.get("/test")
async def r2_test():
    """
    Generate a presigned PUT URL for R2 to verify connectivity.
    Key: test/test.txt, ContentType: text/plain, Expires: 60s

    Usage:
      1. Call this endpoint → get upload_url
      2. PUT a file to upload_url with Content-Type: text/plain
      3. Open object_url → see the file
    """
    bucket = os.getenv("R2_BUCKET_NAME", "moobaan-smart-production")
    public_url = os.getenv("R2_PUBLIC_URL", "")
    key = "test/test.txt"

    try:
        client = _get_r2_client()

        upload_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": "text/plain",
            },
            ExpiresIn=60,
        )

        object_url = f"{public_url.rstrip('/')}/{key}" if public_url else f"(set R2_PUBLIC_URL to get public link)"

        return {
            "upload_url": upload_url,
            "object_url": object_url,
            "bucket": bucket,
            "key": key,
            "expires_in": 60,
            "instructions": "PUT the file to upload_url with header Content-Type: text/plain, then open object_url",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"R2 presigned URL generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"R2 error: {str(e)}")
