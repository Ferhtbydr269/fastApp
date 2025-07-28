from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from .. import schemas, models, crud
from ..database import get_db
from ..auth import get_current_user, get_current_teacher, get_current_student

router = APIRouter(prefix="/grades", tags=["grades"])

@router.post("/give", response_model=schemas.GradeResponse)
def give_grade(
    grade_data: schemas.GradeCreate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher)
):
    """Give a grade to a student (teachers only)"""
    # Verify teacher owns the course
    course = crud.get_course(db, grade_data.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only give grades for your own courses"
        )
    
    # Validate grade range
    if not (0 <= grade_data.grade <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grade must be between 0 and 100"
        )
    
    return crud.create_grade(db=db, grade_data=grade_data)

@router.get("/me", response_model=List[schemas.GradeResponse])
def get_my_grades(
    db: Session = Depends(get_db),
    current_student: models.User = Depends(get_current_student)
):
    """Get all grades for the current student (students only)"""
    return crud.get_student_grades(db, current_student.id)

@router.get("/course/{course_id}", response_model=List[schemas.GradeResponse])
def get_course_grades(
    course_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher)
):
    """Get all grades for a specific course (teachers only)"""
    # Verify teacher owns the course
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view grades for your own courses"
        )
    
    return crud.get_course_grades(db, course_id)

@router.get("/student/{student_id}/course/{course_id}", response_model=schemas.GradeResponse)
def get_student_course_grade(
    student_id: UUID,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific grade for a student in a course"""
    # Students can only view their own grades
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only view their own grades"
        )
    
    # Teachers can only view grades for their courses
    if current_user.role == "teacher":
        course = crud.get_course(db, course_id)
        if not course or course.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view grades for your own courses"
            )
    
    grade = crud.get_grade(db, student_id, course_id)
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    
    return grade