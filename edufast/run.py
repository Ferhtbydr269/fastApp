#!/usr/bin/env python3
"""
EduFast FastAPI Application Runner
Run this script to start the development server
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",  # localhost for Windows
        port=8001,
        reload=False,  # Disable auto-reload for stability
        log_level="info"
    )