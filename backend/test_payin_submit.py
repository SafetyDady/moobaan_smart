#!/usr/bin/env python3
"""Test payin submission with real authentication"""
import requests
import datetime
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

# Step 1: Login as resident
print("=" * 50)
print("STEP 1: Login as resident")
print("=" * 50)
login_resp = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "resident@moobaan.com", "password": "res123"}
)
print(f"Login status: {login_resp.status_code}")
if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.text}")
    exit(1)

token = login_resp.json()["access_token"]
print(f"✅ Got token: {token[:20]}...")

# Step 2: Submit payin with FormData
print("\n" + "=" * 50)
print("STEP 2: Submit payin report")
print("=" * 50)

headers = {"Authorization": f"Bearer {token}"}
paid_at = datetime.datetime.now().isoformat()

# Create test file
test_file = Path("test_slip.jpg")
test_file.write_bytes(b"FAKE_IMAGE_DATA")

with open(test_file, 'rb') as f:
    files = {
        'slip': ('test_slip.jpg', f, 'image/jpeg')
    }
    data = {
        'amount': '1200.50',
        'paid_at': paid_at,
        'note': 'Test payment submission'
    }

    print(f"Sending data: {data}")
    print(f"Sending file: test_slip.jpg")

    submit_resp = requests.post(
        f"{BASE_URL}/api/payin-reports",
        headers=headers,
        files=files,
        data=data
    )

# Cleanup
test_file.unlink()

print(f"\nResponse status: {submit_resp.status_code}")
print(f"Response body:")
print(submit_resp.text)

if submit_resp.status_code == 201:
    print("\n✅ SUCCESS: Payin submitted!")
else:
    print(f"\n❌ FAILED: Status {submit_resp.status_code}")
    if submit_resp.status_code == 422:
        import json
        detail = submit_resp.json().get('detail', [])
        if isinstance(detail, list):
            print("\nValidation errors:")
            for err in detail:
                print(f"  • {err.get('loc')}: {err.get('msg')}")
