"""
Test uvicorn startup to see errors
"""
import sys
import os
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

print("🔍 Loading FastAPI app...")

try:
    from app.main import app
    print("✅ App loaded successfully")
    print(f"   Routes: {len(app.routes)}")
    
    # Test one request
    print("\n🔍 Testing app...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    response = client.get("/")
    print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
    
    print("\n🎯 App working correctly!")
    
except Exception as e:
    print(f"❌ Error loading app: {e}")
    import traceback
    traceback.print_exc()
