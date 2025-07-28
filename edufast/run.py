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
        host="0.0.0.0",  # Listen on all interfaces for Railway
        port=port,
        reload=False,  # Disable auto-reload for production
        log_level="info"
    )