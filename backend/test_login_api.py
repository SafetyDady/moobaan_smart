"""Test login API endpoint"""
import sys
sys.path.insert(0, 'c:/web_project/moobaan_smart/backend')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("Testing Login API")
print("=" * 60)

# Test login
payload = {
    "email": "admin@moobaan.com",
    "password": "Admin123!"
}

print(f"\nSending POST /api/auth/login")
print(f"Payload: {payload}")
print("-" * 60)

response = client.post("/api/auth/login", json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
print("=" * 60)

if response.status_code == 200:
    print("\n✓ Login successful!")
    print(f"Access token received: {response.json()['access_token'][:50]}...")
else:
    print("\n✗ Login failed!")
    print(f"Error: {response.json().get('detail', 'Unknown error')}")
