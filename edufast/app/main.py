from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine, get_db
from . import models
from .routers import users, courses, grades, attendance

# Create database tables with error handling
try:
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
except Exception as e:
    print(f"⚠️ Database connection warning: {e}")
    print("📝 Note: Database tables will be created on first request")

app = FastAPI(
    title="EduFast - Education Management System",
    description="A FastAPI backend for managing courses, students, and grades",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Railway will handle HTTPS
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(grades.router)
app.include_router(attendance.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to EduFast API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    """Health check endpoint to verify database connection"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e), "message": "Database connection failed"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)