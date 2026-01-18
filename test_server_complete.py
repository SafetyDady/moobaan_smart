"""Run backend server and test login in same script"""
import subprocess
import time
import urllib.request
import urllib.error
import json
import sys
import os

print("=" * 60)
print("BACKEND SERVER TEST")
print("=" * 60)

# Start backend server as subprocess
backend_dir = r"c:\web_project\moobaan_smart\backend"
server_proc = subprocess.Popen(
    [sys.executable, "run_server.py"],
    cwd=backend_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print("\n[1] Starting backend server...")
time.sleep(3)  # Wait for server to start

# Check if server is running
if server_proc.poll() is not None:
    print("❌ Server failed to start!")
    output = server_proc.stdout.read()
    print(f"Output: {output}")
    sys.exit(1)

print("✅ Server started (PID: {})".format(server_proc.pid))

# Test login API
print("\n[2] Testing login API...")
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
        print(f"   Token: {result.get('access_token', 'N/A')[:60]}...")
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code}")
    error_body = e.read().decode('utf-8')
    print(f"   Response: {error_body}")
except urllib.error.URLError as e:
    print(f"❌ Connection Error: {e.reason}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test health endpoint  
print("\n[3] Testing health endpoint...")
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=5) as response:
        print(f"✅ Health check: {response.read().decode('utf-8')}")
except Exception as e:
    print(f"❌ Health check failed: {e}")

# Clean up
print("\n[4] Stopping server...")
server_proc.terminate()
try:
    server_proc.wait(timeout=5)
    print("✅ Server stopped")
except:
    server_proc.kill()
    print("⚠️ Server killed forcefully")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
