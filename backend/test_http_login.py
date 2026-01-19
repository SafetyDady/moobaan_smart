#!/usr/bin/env python3
"""Test login endpoint with simple HTTP requests - NO APP IMPORTS"""
import http.client
import json
import time

print("=" * 80)
print("TESTING LOGIN HTTP ENDPOINT")
print("=" * 80)

# Wait a moment for server to be ready
print("\n⏳ Waiting for server...")
time.sleep(1)

# Create connection
conn = http.client.HTTPConnection("127.0.0.1", 8000)

# Prepare request data
login_data = {
    "email": "admin@moobaan.com",
    "password": "Admin123!"
}
body = json.dumps(login_data)
headers = {"Content-Type": "application/json"}

print(f"\n📤 Sending POST /api/auth/login")
print(f"   Body: {login_data}")

try:
    # Send POST request
    conn.request("POST", "/api/auth/login", body, headers)
    
    # Get response
    response = conn.getresponse()
    
    print(f"\n📥 Response:")
    print(f"   Status: {response.status} {response.reason}")
    print(f"   Headers: {response.getheaders()}")
    
    # Read response body
    response_body = response.read()
    print(f"   Body: {response_body.decode('utf-8')}")
    
    if response.status == 200:
        print("\n✅ LOGIN SUCCESSFUL!")
        data = json.loads(response_body)
        print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
    else:
        print("\n❌ LOGIN FAILED!")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

print("\n" + "=" * 80)
