"""Test if cookies are being set by login endpoint"""
import requests

r = requests.post(
    'http://127.0.0.1:8001/api/auth/login',
    json={'email': 'admin@moobaan.com', 'password': 'Admin123!'}
)

print(f"Status: {r.status_code}")
print(f"\nResponse cookies: {dict(r.cookies)}")
print(f"\nSet-Cookie headers:")
for header, value in r.headers.items():
    if header.lower() == 'set-cookie':
        print(f"  {value}")

print(f"\nAll headers:")
for header, value in r.headers.items():
    print(f"  {header}: {value[:80]}...")
