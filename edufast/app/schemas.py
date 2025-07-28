from pydantic import BaseModel, EmailStr
from typing import Literal, Optional, List
from datetime import datetime
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