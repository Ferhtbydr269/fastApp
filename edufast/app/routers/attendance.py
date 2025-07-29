from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List
from datetime import datetime
from uuid import UUID

from ..database import get_db
from ..models import AttendanceSession, AttendanceRecord, Course, User, Enrollment
from ..schemas import (
    AttendanceSessionCreate, AttendanceSessionResponse,
    AttendanceRecordCreate, AttendanceRecordUpdate, AttendanceRecordResponse,
    AttendanceStatusResponse, AttendanceReportResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/courses/{course_id}/session", response_model=AttendanceSessionResponse)
def create_attendance_session(
    course_id: int,
    session_data: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new attendance session for a course (Teacher only)"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create attendance sessions"
        )
    
    # Check if course exists and user is the teacher
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create attendance sessions for your own courses"
        )
    
    # Create attendance session
    db_session = AttendanceSession(
        course_id=course_id,
        date=session_data.date,
        start_time=session_data.start_time,
        end_time=session_data.end_time,
        notes=session_data.notes,
        created_by=current_user.id
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

@router.post("/{session_id}/mark", response_model=AttendanceRecordResponse)
def mark_attendance(
    session_id: int,
    attendance_data: AttendanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark attendance for a student (Teacher only)"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can mark attendance"
        )
    
    # Check if session exists and is active
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )
    
    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark attendance for closed session"
        )
    
    # Check if teacher owns the course
    if session.course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark attendance for your own courses"
        )
    
    # Check if student is enrolled in the course
    enrollment = db.query(Enrollment).filter(
        and_(
            Enrollment.student_id == attendance_data.student_id,
            Enrollment.course_id == session.course_id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not enrolled in this course"
        )
    
    # Check if attendance already marked
    existing_record = db.query(AttendanceRecord).filter(
        and_(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.student_id == attendance_data.student_id
        )
    ).first()
    
    if existing_record:
        # Update existing record
        existing_record.status = attendance_data.status
        existing_record.marked_by = current_user.id
        existing_record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_record)
        return existing_record
    else:
        # Create new record
        db_record = AttendanceRecord(
            session_id=session_id,
            student_id=attendance_data.student_id,
            status=attendance_data.status,
            marked_by=current_user.id
        )
        
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

@router.get("/{session_id}/status")
def get_attendance_status(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance status for a session"""
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )
    
    # Check permissions
    if current_user.role == "teacher" and session.course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view attendance for your own courses"
        )
    
    # Get all enrolled students
    enrolled_students = db.query(User).join(Enrollment).filter(
        Enrollment.course_id == session.course_id
    ).all()
    
    # Get attendance records
    attendance_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session_id
    ).all()
    
    # Calculate summary
    total_students = len(enrolled_students)
    present = len([r for r in attendance_records if r.status == "present"])
    absent = total_students - len(attendance_records) + len([r for r in attendance_records if r.status == "absent"])
    late = len([r for r in attendance_records if r.status == "late"])
    excused = len([r for r in attendance_records if r.status == "excused"])
    
    summary = {
        "total_students": total_students,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused
    }
    
    return {
        "session": session,
        "attendance": attendance_records,
        "summary": summary
    }

@router.put("/{session_id}/close", response_model=AttendanceSessionResponse)
def close_attendance_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Close an attendance session (Teacher only)"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can close attendance sessions"
        )
    
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )
    
    if session.course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only close sessions for your own courses"
        )
    
    session.status = "closed"
    session.closed_at = datetime.utcnow()
    session.closed_by = current_user.id
    
    db.commit()
    db.refresh(session)
    
    return session

@router.get("/courses/{course_id}/sessions")
def get_course_sessions(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all attendance sessions for a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check permissions
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view sessions for your own courses"
        )
    elif current_user.role == "student":
        # Check if student is enrolled
        enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == course_id
            )
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )
    
    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.course_id == course_id
    ).order_by(AttendanceSession.date.desc()).all()
    
    return sessions

@router.get("/student/{student_id}")
def get_student_attendance_history(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete attendance history for a student across all courses"""
    # Check permissions - students can only view their own, teachers can view any
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only view their own attendance history"
        )
    
    # Get student info
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    if student.role != "student":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a student"
        )
    
    # Get all enrollments for the student
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == student_id).all()
    
    attendance_by_course = []
    
    for enrollment in enrollments:
        course = enrollment.course
        
        # If current user is a teacher, only show courses they teach
        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            continue
        
        # Get attendance records for this course
        records = db.query(AttendanceRecord).join(AttendanceSession).filter(
            and_(
                AttendanceRecord.student_id == student_id,
                AttendanceSession.course_id == course.id
            )
        ).order_by(AttendanceSession.date.desc()).all()
        
        # Get total sessions for this course
        total_sessions = db.query(AttendanceSession).filter(
            AttendanceSession.course_id == course.id
        ).count()
        
        # Calculate statistics
        present_count = len([r for r in records if r.status == "present"])
        late_count = len([r for r in records if r.status == "late"])
        absent_count = len([r for r in records if r.status == "absent"])
        excused_count = len([r for r in records if r.status == "excused"])
        
        # Calculate attendance rate (present + late = attended)
        attended_count = present_count + late_count
        attendance_rate = (attended_count / total_sessions * 100) if total_sessions > 0 else 0
        
        # Format attendance history
        attendance_history = []
        for record in records:
            attendance_history.append({
                "session_id": record.session_id,
                "date": record.session.date.isoformat(),
                "start_time": record.session.start_time.strftime("%H:%M"),
                "end_time": record.session.end_time.strftime("%H:%M"),
                "status": record.status,
                "marked_at": record.marked_at.isoformat() if record.marked_at else None,
                "notes": record.session.notes
            })
        
        attendance_by_course.append({
            "course_id": course.id,
            "course_title": course.title,
            "course_description": course.description,
            "teacher_email": course.teacher.email,
            "total_sessions": total_sessions,
            "attended_sessions": attended_count,
            "present_count": present_count,
            "late_count": late_count,
            "absent_count": absent_count,
            "excused_count": excused_count,
            "attendance_rate": round(attendance_rate, 2),
            "attendance_history": attendance_history
        })
    
    # Calculate overall statistics
    total_sessions_all = sum([course["total_sessions"] for course in attendance_by_course])
    total_attended_all = sum([course["attended_sessions"] for course in attendance_by_course])
    overall_attendance_rate = (total_attended_all / total_sessions_all * 100) if total_sessions_all > 0 else 0
    
    return {
        "student_id": str(student_id),
        "student_email": student.email,
        "overall_statistics": {
            "total_courses": len(attendance_by_course),
            "total_sessions": total_sessions_all,
            "total_attended": total_attended_all,
            "overall_attendance_rate": round(overall_attendance_rate, 2)
        },
        "courses": attendance_by_course
    }

@router.get("/{session_id}/marks")
def get_session_attendance_marks(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all attendance marks for a specific session"""
    # Check if session exists
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )
    
    # Check permissions
    if current_user.role == "teacher" and session.course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view attendance marks for your own courses"
        )
    elif current_user.role == "student":
        # Check if student is enrolled in the course
        enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == session.course_id
            )
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )
    
    # Get all enrolled students for the course
    enrolled_students = db.query(User).join(Enrollment).filter(
        and_(
            Enrollment.course_id == session.course_id,
            User.role == "student"
        )
    ).all()
    
    # Get attendance records for this session
    attendance_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session_id
    ).all()
    
    # Create a dictionary for quick lookup
    records_dict = {str(record.student_id): record for record in attendance_records}
    
    # Build the response with all students
    student_marks = []
    for student in enrolled_students:
        record = records_dict.get(str(student.id))
        
        # If student is viewing, only show their own record
        if current_user.role == "student" and student.id != current_user.id:
            continue
        
        student_mark = {
            "student_id": str(student.id),
            "student_email": student.email,
            "status": record.status if record else "absent",
            "marked_at": record.marked_at.isoformat() if record and record.marked_at else None,
            "marked_by": str(record.marked_by) if record else None,
            "updated_at": record.updated_at.isoformat() if record and record.updated_at else None
        }
        student_marks.append(student_mark)
    
    # Calculate summary statistics
    total_students = len(enrolled_students)
    present_count = len([r for r in attendance_records if r.status == "present"])
    absent_count = total_students - len(attendance_records) + len([r for r in attendance_records if r.status == "absent"])
    late_count = len([r for r in attendance_records if r.status == "late"])
    excused_count = len([r for r in attendance_records if r.status == "excused"])
    
    return {
        "session": {
            "id": session.id,
            "course_id": session.course_id,
            "course_title": session.course.title,
            "date": session.date.isoformat(),
            "start_time": session.start_time.strftime("%H:%M"),
            "end_time": session.end_time.strftime("%H:%M"),
            "notes": session.notes,
            "status": session.status,
            "created_by": str(session.created_by),
            "created_at": session.created_at.isoformat()
        },
        "marks": student_marks,
        "summary": {
            "total_students": total_students,
            "present": present_count,
            "absent": absent_count,
            "late": late_count,
            "excused": excused_count,
            "attendance_rate": round((present_count + late_count) / total_students * 100, 2) if total_students > 0 else 0
        }
    }