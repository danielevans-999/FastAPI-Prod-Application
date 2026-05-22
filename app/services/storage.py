import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from ..config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES  = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOC_TYPES    = {"application/pdf", "application/msword",
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_FILE_SIZE        = 10 * 1024 * 1024  # 10MB


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        region_name           = settings.AWS_REGION
    )


async def upload_file_to_s3(
    file:    UploadFile,
    folder:  str = "uploads",
    allowed_types: set = None
) -> dict:
    """
    Upload file to S3 and return file info
    folder: "avatars", "documents", "uploads"
    """

    # validate file type
    if allowed_types and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed"
        )

    # read file content
    content = await file.read()

    # validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB"
        )

    # generate unique filename
    extension  = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_key = f"{folder}/{uuid.uuid4()}.{extension}"

    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket      = settings.AWS_BUCKET_NAME,
            Key         = unique_key,
            Body        = content,
            ContentType = file.content_type,
        )

        url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_key}"

        logger.info(f"File uploaded to S3: {unique_key}")

        return {
            "s3_key":       unique_key,
            "url":          url,
            "filename":     unique_key.split("/")[-1],
            "original_name": file.filename,
            "file_size":    len(content),
            "content_type": file.content_type,
        }

    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


def delete_file_from_s3(s3_key: str) -> bool:
    """Delete a file from S3"""
    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=s3_key)
        logger.info(f"File deleted from S3: {s3_key}")
        return True
    except ClientError as e:
        logger.error(f"S3 delete failed: {e}")
        return False


def generate_presigned_url(s3_key: str, expiry: int = 3600) -> str:
    """Generate a temporary pre-signed URL for private files"""
    try:
        s3  = get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params     = {"Bucket": settings.AWS_BUCKET_NAME, "Key": s3_key},
            ExpiresIn  = expiry
        )
        return url
    except ClientError as e:
        logger.error(f"Pre-signed URL generation failed: {e}")
        raise HTTPException(status_code=500, detail="Could not generate download URL")
