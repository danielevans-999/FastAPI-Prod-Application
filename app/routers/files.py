from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import uuid, os, shutil
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, FileUpload
from app.schemas.schemas import FileResponse, MessageResponse

router = APIRouter(prefix="/api/files", tags=["Files"])

UPLOAD_DIR = "uploads"
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/gif", "application/pdf",
                 "text/plain", "application/msword",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=FileResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a file — returns file metadata and URL"""

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")

    # Read and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")

    # Generate unique filename
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = f"{UPLOAD_DIR}/{unique_name}"

    # Save locally (swap with S3 upload in production)
    with open(file_path, "wb") as f:
        f.write(content)

    # Save to database
    file_record = FileUpload(
        user_id       = current_user.id,
        filename      = unique_name,
        original_name = file.filename,
        file_type     = file.content_type,
        file_size     = len(content),
        url           = f"/api/files/{unique_name}"
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


@router.get("/{filename}")
def download_file(filename: str, current_user: User = Depends(get_current_user)):
    """Download a file by filename"""
    file_path = f"{UPLOAD_DIR}/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    def file_stream():
        with open(file_path, "rb") as f:
            yield from f

    return StreamingResponse(file_stream(), media_type="application/octet-stream",
                             headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/", response_model=List[FileResponse])
def list_my_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all files uploaded by current user"""
    return db.query(FileUpload).filter(FileUpload.user_id == current_user.id).all()


@router.delete("/{file_id}", response_model=MessageResponse)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_record = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from disk
    file_path = f"{UPLOAD_DIR}/{file_record.filename}"
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(file_record)
    db.commit()
    return {"message": "File deleted"}
