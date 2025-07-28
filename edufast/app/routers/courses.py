from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, crud
from ..database import get_db
from ..auth import get_current_user, get_current_teacher, get_current_student

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/", response_model=List[schemas.CourseResponse])
def get_all_courses(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all available courses"""
    courses = crud.get_courses(db, skip=skip, limit=limit)
    return courses

@router.post("/", response_model=schemas.CourseResponse)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher)
):
    """Create a new course (teachers only)"""
    return crud.create_course(db=db, course=course, teacher_id=current_teacher.id)

@router.get("/my-courses", response_model=List[schemas.CourseResponse])
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get courses based on user role - taught courses for teachers, enrolled courses for students"""
    if current_user.role == "teacher":
        return crud.get_courses_by_teacher(db, current_user.id)
    else:  # student
        enrollments = crud.get_student_enrollments(db, current_user.id)
        return [enrollment.course for enrollment in enrollments]

@router.get("/{course_id}", response_model=schemas.CourseResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific course by ID"""
    course = crud.get_course(db, course_id=course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/enroll", response_model=schemas.EnrollmentResponse)
def enroll_in_course(
    enrollment: schemas.EnrollmentCreate,
    db: Session = Depends(get_db),
    current_student: models.User = Depends(get_current_student)
):
    """Enroll student in a course (students only)"""
    return crud.enroll_student(
        db=db, 
        student_id=current_student.id, 
        course_id=enrollment.course_id
    )

@router.get("/{course_id}/students", response_model=List[schemas.EnrollmentResponse])
def get_course_students(
    course_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher)
):
    """Get all students enrolled in a course (teachers only)"""
    # Verify teacher owns this course
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view students for your own courses"
        )
    
    return crud.get_course_enrollments(db, course_id)