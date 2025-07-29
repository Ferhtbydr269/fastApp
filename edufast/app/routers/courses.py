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

@router.put("/{course_id}", response_model=schemas.CourseResponse)
def update_course(
    course_id: int,
    course_data: schemas.CourseUpdate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher)
):
    """Update a course (teachers only)"""
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own courses"
        )
    
    # Update only provided fields
    update_data = course_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    return course

@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher)
):
    """Delete a course (teachers only)"""
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own courses"
        )
    
    # Soft delete - mark as inactive
    course.is_active = "false"
    db.commit()
    
    return {"message": "Course deleted successfully"}

@router.get("/search")
def search_courses(
    q: str = "",
    category: str = None,
    semester: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Search courses with filters"""
    query = db.query(models.Course).filter(models.Course.is_active == "true")
    
    if q:
        query = query.filter(
            models.Course.title.ilike(f"%{q}%") | 
            models.Course.description.ilike(f"%{q}%") |
            models.Course.code.ilike(f"%{q}%")
        )
    
    if category:
        query = query.filter(models.Course.category == category)
    
    if semester:
        query = query.filter(models.Course.semester == semester)
    
    courses = query.offset(skip).limit(limit).all()
    return courses

@router.get("/{course_id}/students/simple")
def get_course_students_simple(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get simple list of students enrolled in a course"""
    # Check if course exists
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check permissions
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view students for your own courses"
        )
    elif current_user.role == "student":
        # Check if student is enrolled
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == current_user.id,
            models.Enrollment.course_id == course_id
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )
    
    # Get enrolled students
    students = db.query(models.User).join(models.Enrollment).filter(
        models.Enrollment.course_id == course_id,
        models.User.role == "student"
    ).all()
    
    return [
        {
            "id": str(student.id),
            "email": student.email,
            "role": student.role
        }
        for student in students
    ]