from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from . import models, schemas

# Course CRUD operations
def create_course(db: Session, course: schemas.CourseCreate, teacher_id):
    db_course = models.Course(**course.dict(), teacher_id=teacher_id)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def get_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Course).offset(skip).limit(limit).all()

def get_course(db: Session, course_id: int):
    return db.query(models.Course).filter(models.Course.id == course_id).first()

def get_courses_by_teacher(db: Session, teacher_id):
    return db.query(models.Course).filter(models.Course.teacher_id == teacher_id).all()

# Enrollment CRUD operations
def enroll_student(db: Session, student_id, course_id: int):
    # Check if course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if already enrolled
    existing_enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id,
        models.Enrollment.course_id == course_id
    ).first()
    
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already enrolled in this course"
        )
    
    db_enrollment = models.Enrollment(student_id=student_id, course_id=course_id)
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment

def get_student_enrollments(db: Session, student_id):
    return db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id
    ).all()

def get_course_enrollments(db: Session, course_id: int):
    return db.query(models.Enrollment).filter(
        models.Enrollment.course_id == course_id
    ).all()

# Grade CRUD operations
def create_grade(db: Session, grade_data: schemas.GradeCreate):
    # Check if student is enrolled in the course
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == grade_data.student_id,
        models.Enrollment.course_id == grade_data.course_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not enrolled in this course"
        )
    
    # Check if grade already exists, update if it does
    existing_grade = db.query(models.Grade).filter(
        models.Grade.student_id == grade_data.student_id,
        models.Grade.course_id == grade_data.course_id
    ).first()
    
    if existing_grade:
        existing_grade.grade = grade_data.grade
        db.commit()
        db.refresh(existing_grade)
        return existing_grade
    
    # Create new grade
    db_grade = models.Grade(**grade_data.dict())
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

def get_student_grades(db: Session, student_id):
    return db.query(models.Grade).filter(
        models.Grade.student_id == student_id
    ).all()

def get_course_grades(db: Session, course_id: int):
    return db.query(models.Grade).filter(
        models.Grade.course_id == course_id
    ).all()

def get_grade(db: Session, student_id, course_id: int):
    return db.query(models.Grade).filter(
        models.Grade.student_id == student_id,
        models.Grade.course_id == course_id
    ).first()

# User CRUD operations
def get_user(db: Session, user_id):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()