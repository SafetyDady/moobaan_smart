#!/usr/bin/env python
"""
Test script for JWT authentication and RBAC system
"""
import requests
import json
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000/api"

def test_login(email, password):
    """Test login and return token"""
    print(f"🔑 Testing login for {email}...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful! Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_me_endpoint(token):
    """Test /auth/me endpoint"""
    print("👤 Testing /auth/me endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        print("✅ /auth/me successful:")
        pprint(response.json())
    else:
        print(f"❌ /auth/me failed: {response.status_code} - {response.text}")

def test_protected_endpoint(token, endpoint, method="GET", data=None):
    """Test a protected endpoint with token"""
    print(f"🔒 Testing {method} {endpoint}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if method == "GET":
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    elif method == "POST":
        response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json=data)
    
    print(f"   Status: {response.status_code}")
    if response.status_code < 400:
        print(f"   ✅ Success")
    else:
        print(f"   ❌ Failed: {response.text}")
    
    return response.status_code

def test_no_token(endpoint):
    """Test endpoint without token (should fail)"""
    print(f"🚫 Testing {endpoint} without token...")
    
    response = requests.get(f"{BASE_URL}{endpoint}")
    
    if response.status_code == 401:
        print("   ✅ Correctly rejected (401 Unauthorized)")
    else:
        print(f"   ❌ Unexpected response: {response.status_code}")

def main():
    print("🚀 Testing JWT Authentication and RBAC System")
    print("=" * 60)
    
    # Test 1: Login with different users
    print("\n📋 Test 1: User Authentication")
    admin_token = test_login("admin@moobaan.com", "admin123")
    accounting_token = test_login("accounting@moobaan.com", "acc123")
    resident_token = test_login("resident@moobaan.com", "res123")
    
    # Test 2: Invalid login
    print("\n📋 Test 2: Invalid Credentials")
    test_login("admin@moobaan.com", "wrongpassword")
    
    if not admin_token or not accounting_token or not resident_token:
        print("❌ Authentication failed. Cannot continue tests.")
        return
    
    # Test 3: /auth/me for each user
    print("\n📋 Test 3: User Info Endpoint")
    for name, token in [("Admin", admin_token), ("Accounting", accounting_token), ("Resident", resident_token)]:
        print(f"\n--- {name} ---")
        test_me_endpoint(token)
    
    # Test 4: Test protected endpoints without token
    print("\n📋 Test 4: No Token Protection")
    test_no_token("/houses")
    test_no_token("/members") 
    test_no_token("/payin-reports")
    
    # Test 5: RBAC on houses endpoint
    print("\n📋 Test 5: Houses Endpoint RBAC")
    print("Admin (should work):")
    test_protected_endpoint(admin_token, "/houses")
    print("Accounting (should work):")
    test_protected_endpoint(accounting_token, "/houses")
    print("Resident (should fail - 403):")
    test_protected_endpoint(resident_token, "/houses")
    
    # Test 6: RBAC on members endpoint
    print("\n📋 Test 6: Members Endpoint RBAC")
    print("Admin (should work):")
    test_protected_endpoint(admin_token, "/members")
    print("Resident (should fail - 403):")
    test_protected_endpoint(resident_token, "/members")
    
    # Test 7: PayIn reports with role filtering
    print("\n📋 Test 7: PayIn Reports RBAC")
    print("Admin (should see all):")
    test_protected_endpoint(admin_token, "/payin-reports")
    print("Resident (should see only their house):")
    test_protected_endpoint(resident_token, "/payin-reports")
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()