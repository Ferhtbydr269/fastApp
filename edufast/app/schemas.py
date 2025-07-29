from pydantic import BaseModel, EmailStr
from typing import Literal, Optional, List
from datetime import datetime, date, time
from uuid import UUID

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    role: Literal["student", "teacher"]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    is_active: str
    
    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

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
    code: Optional[str] = None
    credits: Optional[int] = 3
    semester: Optional[str] = None
    max_students: Optional[int] = 50
    category: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    credits: Optional[int] = None
    semester: Optional[str] = None
    max_students: Optional[int] = None
    category: Optional[str] = None

class CourseResponse(CourseBase):
    id: int
    teacher_id: UUID
    teacher: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime
    is_active: str
    
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

# File schemas
class FileResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_type: str
    uploaded_by: UUID
    course_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Message schemas
class MessageCreate(BaseModel):
    recipient_id: UUID
    subject: str
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_id: UUID
    recipient_id: UUID
    subject: str
    content: str
    is_read: str
    created_at: datetime
    sender: Optional[UserResponse] = None
    recipient: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# Announcement schemas
class AnnouncementCreate(BaseModel):
    course_id: int
    title: str
    content: str

class AnnouncementResponse(BaseModel):
    id: int
    course_id: int
    title: str
    content: str
    created_by: UUID
    created_at: datetime
    creator: Optional[UserResponse] = None
    course: Optional[CourseResponse] = None
    
    class Config:
        from_attributes = True