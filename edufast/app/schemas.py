from pydantic import BaseModel, EmailStr
from typing import Literal, Optional, List
from datetime import datetime, date, time
from uuid import UUID

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    role: Literal["student", "teacher"]

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Course schemas
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    teacher_id: UUID
    teacher: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# Enrollment schemas
class EnrollmentCreate(BaseModel):
    course_id: int

class EnrollmentResponse(BaseModel):
    id: int
    student_id: UUID
    course_id: int
    course: Optional[CourseResponse] = None
    
    class Config:
        from_attributes = True

# Grade schemas
class GradeCreate(BaseModel):
    student_id: UUID
    course_id: int
    grade: int

class GradeResponse(BaseModel):
    id: int
    student_id: UUID
    course_id: int
    grade: int
    student: Optional[UserResponse] = None
    course: Optional[CourseResponse] = None
    
    class Config:
        from_attributes = True

# Attendance schemas
class AttendanceSessionCreate(BaseModel):
    date: date
    start_time: time
    end_time: time
    notes: Optional[str] = None

class AttendanceSessionResponse(BaseModel):
    id: int
    course_id: int
    date: date
    start_time: time
    end_time: time
    notes: Optional[str] = None
    status: str
    created_by: UUID
    created_at: datetime
    closed_at: Optional[datetime] = None
    closed_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True

class AttendanceRecordCreate(BaseModel):
    student_id: UUID
    status: Literal["present", "absent", "late", "excused"]

class AttendanceRecordUpdate(BaseModel):
    status: Literal["present", "absent", "late", "excused"]

class AttendanceRecordResponse(BaseModel):
    id: int
    session_id: int
    student_id: UUID
    status: str
    marked_at: datetime
    marked_by: UUID
    updated_at: datetime
    student: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

class AttendanceStatusResponse(BaseModel):
    session: AttendanceSessionResponse
    attendance: List[AttendanceRecordResponse]
    summary: dict

class AttendanceReportResponse(BaseModel):
    course_id: int
    course_title: str
    total_sessions: int
    attendance_rate: float
    student_reports: List[dict]
    session_reports: List[dict]