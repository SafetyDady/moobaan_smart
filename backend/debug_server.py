#!/usr/bin/env python3
"""Simple test server to debug issues"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("STARTING DEBUG SERVER")
print("=" * 80)

try:
    from app.main import app
    print("✅ App imported successfully")
    
    import uvicorn
    print("✅ Starting uvicorn...")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="debug"
    )
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
