"""Quick test for login API"""
import urllib.request
import urllib.error
import json

url = "http://127.0.0.1:8000/api/auth/login"
data = {
    "email": "admin@moobaan.com",
    "password": "Admin123!"
}

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("✅ LOGIN SUCCESSFUL!")
        print(f"Token: {result.get('access_token', 'N/A')[:50]}...")
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code}")
    print(f"Response: {e.read().decode('utf-8')}")
except urllib.error.URLError as e:
    print(f"❌ Connection Error: {e.reason}")
except Exception as e:
    print(f"❌ Error: {e}")
