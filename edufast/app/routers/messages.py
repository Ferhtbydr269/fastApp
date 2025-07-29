from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List
from uuid import UUID

from .. import schemas, models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/send", response_model=schemas.MessageResponse)
def send_message(
    message_data: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Send a message to another user"""
    
    # Check if recipient exists
    recipient = db.query(models.User).filter(models.User.id == message_data.recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    # Create message
    db_message = models.Message(
        sender_id=current_user.id,
        recipient_id=message_data.recipient_id,
        subject=message_data.subject,
        content=message_data.content
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

@router.get("/inbox", response_model=List[schemas.MessageResponse])
def get_inbox(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user's inbox messages"""
    query = db.query(models.Message).filter(models.Message.recipient_id == current_user.id)
    
    if unread_only:
        query = query.filter(models.Message.is_read == "false")
    
    messages = query.order_by(models.Message.created_at.desc()).offset(skip).limit(limit).all()
    return messages

@router.get("/sent", response_model=List[schemas.MessageResponse])
def get_sent_messages(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user's sent messages"""
    messages = db.query(models.Message).filter(
        models.Message.sender_id == current_user.id
    ).order_by(models.Message.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages

@router.get("/conversation/{user_id}", response_model=List[schemas.MessageResponse])
def get_conversation(
    user_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get conversation between current user and another user"""
    
    # Check if other user exists
    other_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get messages between the two users
    messages = db.query(models.Message).filter(
        or_(
            and_(
                models.Message.sender_id == current_user.id,
                models.Message.recipient_id == user_id
            ),
            and_(
                models.Message.sender_id == user_id,
                models.Message.recipient_id == current_user.id
            )
        )
    ).order_by(models.Message.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages

@router.put("/{message_id}/read")
def mark_message_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark a message as read"""
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Only recipient can mark message as read
    if message.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark your own messages as read"
        )
    
    message.is_read = "true"
    db.commit()
    
    return {"message": "Message marked as read"}

@router.delete("/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a message"""
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Only sender or recipient can delete message
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )
    
    db.delete(message)
    db.commit()
    
    return {"message": "Message deleted successfully"}

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get count of unread messages"""
    count = db.query(models.Message).filter(
        models.Message.recipient_id == current_user.id,
        models.Message.is_read == "false"
    ).count()
    
    return {"unread_count": count}

# Announcements
@router.post("/announcements", response_model=schemas.AnnouncementResponse)
def create_announcement(
    announcement_data: schemas.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_user)
):
    """Create course announcement (teachers only)"""
    if current_teacher.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create announcements"
        )
    
    # Check if teacher owns the course
    course = db.query(models.Course).filter(
        models.Course.id == announcement_data.course_id,
        models.Course.teacher_id == current_teacher.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create announcements for your own courses"
        )
    
    # Create announcement
    db_announcement = models.Announcement(
        course_id=announcement_data.course_id,
        title=announcement_data.title,
        content=announcement_data.content,
        created_by=current_teacher.id
    )
    
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    
    return db_announcement

@router.get("/announcements/course/{course_id}", response_model=List[schemas.AnnouncementResponse])
def get_course_announcements(
    course_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get announcements for a course"""
    
    # Check if user has access to the course
    if current_user.role == "teacher":
        course = db.query(models.Course).filter(
            models.Course.id == course_id,
            models.Course.teacher_id == current_user.id
        ).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view announcements for your own courses"
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
    
    announcements = db.query(models.Announcement).filter(
        models.Announcement.course_id == course_id
    ).order_by(models.Announcement.created_at.desc()).offset(skip).limit(limit).all()
    
    return announcements

@router.get("/announcements/my", response_model=List[schemas.AnnouncementResponse])
def get_my_announcements(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get announcements from user's courses"""
    
    if current_user.role == "student":
        # Get announcements from enrolled courses
        announcements = db.query(models.Announcement).join(models.Course).join(models.Enrollment).filter(
            models.Enrollment.student_id == current_user.id
        ).order_by(models.Announcement.created_at.desc()).offset(skip).limit(limit).all()
    else:
        # Get announcements from taught courses
        announcements = db.query(models.Announcement).filter(
            models.Announcement.created_by == current_user.id
        ).order_by(models.Announcement.created_at.desc()).offset(skip).limit(limit).all()
    
    return announcements

@router.delete("/announcements/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_user)
):
    """Delete an announcement (teachers only)"""
    if current_teacher.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can delete announcements"
        )
    
    announcement = db.query(models.Announcement).filter(
        models.Announcement.id == announcement_id
    ).first()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    
    if announcement.created_by != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own announcements"
        )
    
    db.delete(announcement)
    db.commit()
    
    return {"message": "Announcement deleted successfully"}