from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint, DateTime, Date, Time, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    
    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher')", name='check_role'),
    )
    
    # Relationships
    taught_courses = relationship("Course", back_populates="teacher")
    enrollments = relationship("Enrollment", back_populates="student")
    grades = relationship("Grade", back_populates="student")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    teacher = relationship("User", back_populates="taught_courses")
    enrollments = relationship("Enrollment", back_populates="course")
    grades = relationship("Grade", back_populates="course")
    attendance_sessions = relationship("AttendanceSession", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Integer, nullable=False)
    
    __table_args__ = (
        CheckConstraint("grade BETWEEN 0 AND 100", name='check_grade_range'),
    )
    
    # Relationships
    student = relationship("User", back_populates="grades")
    course = relationship("Course", back_populates="grades")

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    notes = Column(Text)
    status = Column(String, default="active", nullable=False)  # active, closed
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'closed')", name='check_session_status'),
    )
    
    # Relationships
    course = relationship("Course", back_populates="attendance_sessions")
    creator = relationship("User", foreign_keys=[created_by])
    closer = relationship("User", foreign_keys=[closed_by])
    attendance_records = relationship("AttendanceRecord", back_populates="session")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False)  # present, absent, late, excused
    marked_at = Column(DateTime(timezone=True), server_default=func.now())
    marked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('present', 'absent', 'late', 'excused')", name='check_attendance_status'),
    )
    
    # Relationships
    session = relationship("AttendanceSession", back_populates="attendance_records")
    student = relationship("User", foreign_keys=[student_id])
    marker = relationship("User", foreign_keys=[marked_by])