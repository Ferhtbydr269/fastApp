# EduFast - Education Management System

A production-grade FastAPI backend for managing courses, students, and grades with Supabase PostgreSQL integration.

## 🚀 Features

- **User Management**: JWT-based authentication for students and teachers
- **Course Management**: Teachers can create and manage courses
- **Enrollment System**: Students can enroll in available courses
- **Grade Tracking**: Teachers can assign grades, students can view their grades
- **Role-based Access Control**: Different permissions for students and teachers
- **Interactive API Documentation**: Auto-generated Swagger UI

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Database**: Supabase PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: Pydantic
- **Password Hashing**: bcrypt

## 📁 Project Structure

```
edufast/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database connection and session management
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic schemas for request/response validation
│   ├── crud.py              # Database operations
│   ├── auth.py              # JWT authentication and user management
│   └── routers/
│       ├── __init__.py
│       ├── users.py         # Authentication endpoints
│       ├── courses.py       # Course management endpoints
│       └── grades.py        # Grade management endpoints
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── run.py                   # Development server runner
├── init_db.py              # Database initialization script
└── README.md               # This file
```

## 🔧 Setup Instructions

### 1. Environment Setup

1. **Clone and navigate to the project**:
   ```bash
   cd edufast
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Update the `.env` file with your Supabase credentials:
   ```env
   DATABASE_URL=postgresql://username:password@db.supabase.co:5432/postgres
   JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=24
   ```

### 2. Database Setup

1. **Initialize the database with sample data**:
   ```bash
   python init_db.py
   ```

   This creates sample users, courses, enrollments, and grades for testing.

### 3. Run the Application

1. **Start the development server**:
   ```bash
   python run.py
   ```

2. **Access the application**:
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Courses
- `GET /courses/` - Get all courses
- `POST /courses/` - Create a new course (teachers only)
- `GET /courses/my-courses` - Get user's courses
- `GET /courses/{course_id}` - Get specific course
- `POST /courses/enroll` - Enroll in a course (students only)
- `GET /courses/{course_id}/students` - Get course students (teachers only)

### Grades
- `POST /grades/give` - Give a grade (teachers only)
- `GET /grades/me` - Get student's grades (students only)
- `GET /grades/course/{course_id}` - Get course grades (teachers only)
- `GET /grades/student/{student_id}/course/{course_id}` - Get specific grade

## 🔐 Sample Users

After running `init_db.py`, you can use these test accounts:

### Teachers
- **Email**: teacher1@edufast.com | **Password**: teacher123
- **Email**: teacher2@edufast.com | **Password**: teacher123

### Students
- **Email**: student1@edufast.com | **Password**: student123
- **Email**: student2@edufast.com | **Password**: student123
- **Email**: student3@edufast.com | **Password**: student123

## 🧪 Testing the API

1. **Get JWT Token**:
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email": "teacher1@edufast.com", "password": "teacher123"}'
   ```

2. **Use the token in subsequent requests**:
   ```bash
   curl -X GET "http://localhost:8000/courses/my-courses" \
        -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

3. **Or use the interactive Swagger UI**:
   - Go to http://localhost:8000/docs
   - Click "Authorize" and enter your JWT token
   - Test all endpoints interactively

## 🗃️ Database Schema

### Users Table
- `id` (UUID, Primary Key)
- `email` (String, Unique)
- `password` (String, Hashed)
- `role` (String: 'student' or 'teacher')

### Courses Table
- `id` (Integer, Primary Key)
- `title` (String)
- `description` (String)
- `teacher_id` (UUID, Foreign Key)

### Enrollments Table
- `id` (Integer, Primary Key)
- `student_id` (UUID, Foreign Key)
- `course_id` (Integer, Foreign Key)

### Grades Table
- `id` (Integer, Primary Key)
- `student_id` (UUID, Foreign Key)
- `course_id` (Integer, Foreign Key)
- `grade` (Integer, 0-100)

## 🚀 Production Deployment

1. **Update environment variables** for production
2. **Configure CORS** properly in `main.py`
3. **Use a production WSGI server** like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 🔒 Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Role-based access control
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy ORM

## 📝 License

This project is built for educational purposes as part of the EduFast platform.