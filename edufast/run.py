#!/usr/bin/env python3
"""
EduFast FastAPI Application Runner
Run this script to start the development server
"""

import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Railway provides PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",  # Use localhost for Windows development
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )