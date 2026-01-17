"""Test API manually"""
import requests

token = requests.post(
    "http://127.0.0.1:8000/api/auth/login",
    json={"email": "admin@moobaan.com", "password": "password"}
).json()["access_token"]

response = requests.get(
    "http://127.0.0.1:8000/api/bank-statements/transactions/unmatched",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
