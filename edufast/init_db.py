#!/usr/bin/env python3
"""
Database initialization script for EduFast
Creates sample users, courses, enrollments, and grades for testing
"""

import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models
from app.auth import get_password_hash

def init_database():
    """Initialize database with sample data"""
    
    # Create all tables
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(models.User).first():
            print("Database already contains data. Skipping initialization.")
            return
        
        # Create sample teachers
        teacher1 = models.User(
            email="teacher1@edufast.com",
            password=get_password_hash("teacher123"),
            role="teacher"
        )
        
        teacher2 = models.User(
            email="teacher2@edufast.com",
            password=get_password_hash("teacher123"),
            role="teacher"
        )
        
        # Create sample students
        student1 = models.User(
            email="student1@edufast.com",
            password=get_password_hash("student123"),
            role="student"
        )
        
        student2 = models.User(
            email="student2@edufast.com",
            password=get_password_hash("student123"),
            role="student"
        )
        
        student3 = models.User(
            email="student3@edufast.com",
            password=get_password_hash("student123"),
            role="student"
        )
        
        # Add users to database
        db.add_all([teacher1, teacher2, student1, student2, student3])
        db.commit()
        
        # Create sample courses
        course1 = models.Course(
            title="Introduction to Python",
            description="Learn the basics of Python programming",
            teacher_id=teacher1.id
        )
        
        course2 = models.Course(
            title="Web Development with FastAPI",
            description="Build modern web APIs with FastAPI",
            teacher_id=teacher1.id
        )
        
        course3 = models.Course(
            title="Database Design",
            description="Learn how to design efficient databases",
            teacher_id=teacher2.id
        )
        
        # Add courses to database
        db.add_all([course1, course2, course3])
        db.commit()
        db.refresh(course1)
        db.refresh(course2)
        db.refresh(course3)
        
        # Create sample enrollments
        enrollments = [
            models.Enrollment(student_id=student1.id, course_id=course1.id),
            models.Enrollment(student_id=student1.id, course_id=course2.id),
            models.Enrollment(student_id=student2.id, course_id=course1.id),
            models.Enrollment(student_id=student2.id, course_id=course3.id),
            models.Enrollment(student_id=student3.id, course_id=course2.id),
            models.Enrollment(student_id=student3.id, course_id=course3.id),
        ]
        
        db.add_all(enrollments)
        db.commit()
        
        # Create sample grades
        grades = [
            models.Grade(student_id=student1.id, course_id=course1.id, grade=85),
            models.Grade(student_id=student1.id, course_id=course2.id, grade=92),
            models.Grade(student_id=student2.id, course_id=course1.id, grade=78),
            models.Grade(student_id=student2.id, course_id=course3.id, grade=88),
            models.Grade(student_id=student3.id, course_id=course2.id, grade=95),
        ]
        
        db.add_all(grades)
        db.commit()
        
        print("✅ Database initialized successfully!")
        print("\n📚 Sample Data Created:")
        print("Teachers:")
        print("  - teacher1@edufast.com (password: teacher123)")
        print("  - teacher2@edufast.com (password: teacher123)")
        print("\nStudents:")
        print("  - student1@edufast.com (password: student123)")
        print("  - student2@edufast.com (password: student123)")
        print("  - student3@edufast.com (password: student123)")
        print("\nCourses:")
        print("  - Introduction to Python")
        print("  - Web Development with FastAPI")
        print("  - Database Design")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()