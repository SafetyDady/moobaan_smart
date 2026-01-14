#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    # Force use of single worker on Windows for Python 3.13
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=settings.PORT, 
        reload=False,  # Disable reload for now to avoid issues
        workers=1,
        log_level="info"
    )