from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import shutil
from pathlib import Path

from .. import schemas, models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/files", tags=["files"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
    'archive': ['.zip', '.rar', '.7z'],
    'video': ['.mp4', '.avi', '.mov', '.wmv'],
    'audio': ['.mp3', '.wav', '.ogg']
}

def get_file_type(filename: str) -> str:
    """Determine file type based on extension"""
    ext = Path(filename).suffix.lower()
    
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    
    return 'other'

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    ext = Path(filename).suffix.lower()
    all_extensions = []
    for extensions in ALLOWED_EXTENSIONS.values():
        all_extensions.extend(extensions)
    
    return ext in all_extensions

@router.post("/upload", response_model=schemas.FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = "document",
    course_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Upload a file"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed"
        )
    
    # Check file size (10MB limit)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large (max 10MB)"
        )
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create directory structure
    upload_path = UPLOAD_DIR / file_type
    upload_path.mkdir(exist_ok=True)
    
    file_path = upload_path / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Save file info to database
    db_file = models.File(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
        file_type=file_type,
        uploaded_by=current_user.id,
        course_id=course_id
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file

@router.post("/upload-avatar", response_model=schemas.UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Upload user avatar"""
    
    # Validate image file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS['image']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed for avatars"
        )
    
    # Check file size (2MB limit for avatars)
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:  # 2MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar file size too large (max 2MB)"
        )
    
    # Generate unique filename
    unique_filename = f"avatar_{current_user.id}_{uuid.uuid4()}{file_ext}"
    
    # Create avatars directory
    avatar_path = UPLOAD_DIR / "avatars"
    avatar_path.mkdir(exist_ok=True)
    
    file_path = avatar_path / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save avatar: {str(e)}"
        )
    
    # Update user avatar URL
    current_user.avatar_url = f"/files/avatars/{unique_filename}"
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/my-files", response_model=List[schemas.FileResponse])
def get_my_files(
    file_type: str = None,
    course_id: int = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user's uploaded files"""
    query = db.query(models.File).filter(models.File.uploaded_by == current_user.id)
    
    if file_type:
        query = query.filter(models.File.file_type == file_type)
    
    if course_id:
        query = query.filter(models.File.course_id == course_id)
    
    files = query.order_by(models.File.created_at.desc()).offset(skip).limit(limit).all()
    return files

@router.get("/course/{course_id}", response_model=List[schemas.FileResponse])
def get_course_files(
    course_id: int,
    file_type: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get files for a specific course"""
    # Check if user has access to the course
    if current_user.role == "teacher":
        course = db.query(models.Course).filter(
            models.Course.id == course_id,
            models.Course.teacher_id == current_user.id
        ).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view files for your own courses"
            )
    elif current_user.role == "student":
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == current_user.id,
            models.Enrollment.course_id == course_id
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )
    
    query = db.query(models.File).filter(models.File.course_id == course_id)
    
    if file_type:
        query = query.filter(models.File.file_type == file_type)
    
    files = query.order_by(models.File.created_at.desc()).offset(skip).limit(limit).all()
    return files

@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a file"""
    file_record = db.query(models.File).filter(models.File.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check permissions
    if file_record.uploaded_by != current_user.id:
        # Teachers can delete files from their courses
        if current_user.role == "teacher" and file_record.course_id:
            course = db.query(models.Course).filter(
                models.Course.id == file_record.course_id,
                models.Course.teacher_id == current_user.id
            ).first()
            if not course:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete your own files or files from your courses"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own files"
            )
    
    # Delete physical file
    try:
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
    except Exception as e:
        print(f"Warning: Could not delete physical file: {e}")
    
    # Delete database record
    db.delete(file_record)
    db.commit()
    
    return {"message": "File deleted successfully"}