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
    from app.main import app
    
    # Use app object directly for better Windows compatibility
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=settings.PORT, 
        log_level="info"
    )