#!/usr/bin/env python3
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
if __name__ == "__main__":
    import uvicorn
    from app.main import app
    from app.core.config import settings
    
    uvicorn.run(
        app, 
        host="localhost", 
        port=settings.PORT, 
        reload=True if settings.ENV == "local" else False
    )