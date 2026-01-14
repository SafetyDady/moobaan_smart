#!/usr/bin/env python
"""
Test script to call the residents API endpoint directly
"""
import requests
import json

# First login to get a token
login_data = {
    "email": "admin@moobaan.com",
    "password": "admin123"
}

try:
    # Login
    print("🔑 Logging in...")
    login_response = requests.post("http://127.0.0.1:8000/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        exit(1)
    
    token = login_response.json()["access_token"]
    print("✅ Login successful")
    
    # Call residents endpoint
    print("\n📋 Fetching residents...")
    headers = {"Authorization": f"Bearer {token}"}
    residents_response = requests.get("http://127.0.0.1:8000/api/users/residents", headers=headers)
    
    print(f"Status: {residents_response.status_code}")
    print(f"Response: {json.dumps(residents_response.json(), indent=2)}")
    
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend. Is it running on port 8000?")
except Exception as e:
    print(f"❌ Error: {e}")