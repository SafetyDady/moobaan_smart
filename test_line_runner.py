"""
Start backend + run LINE API tests in sequence.
Self-contained test runner.
"""
import subprocess
import time
import sys
import requests
import json

# Start backend
print("Starting backend...")
proc = subprocess.Popen(
    [r"C:\web_project\moobaan_smart\.venv\Scripts\python.exe", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--workers", "2"],
    cwd=r"C:\web_project\moobaan_smart\backend",
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Wait for startup
BASE = "http://127.0.0.1:8000"
for i in range(15):
    time.sleep(1)
    try:
        r = requests.get(f"{BASE}/docs", timeout=2)
        if r.status_code == 200:
            print(f"Backend ready after {i+1}s")
            break
    except:
        pass
else:
    print("Backend failed to start!")
    proc.kill()
    sys.exit(1)

results = []

def test(name, expected_status, actual_status, body):
    passed = expected_status == actual_status
    status = "PASS ✅" if passed else "FAIL ❌"
    results.append((name, passed))
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"Expected: {expected_status}")
    print(f"Got:      {actual_status}")
    print(f"Body:     {json.dumps(body, indent=2, ensure_ascii=False)}")
    print(f"Result:   {status}")
    print(f"{'='*60}")

# Test 2a-1: GET /api/auth/line/config (no LINE_CHANNEL_ID → 503)
try:
    r = requests.get(f"{BASE}/api/auth/line/config", params={"redirect_uri": "http://localhost:5173/login"}, timeout=5)
    test("2a-1: GET /config — no LINE env → 503", 503, r.status_code, r.json())
except Exception as e:
    print(f"ERROR in 2a-1: {e}")
    results.append(("2a-1", False))

# Test 2b-1: POST /api/auth/line/login (fake code → should be 400 or 503)
try:
    r = requests.post(f"{BASE}/api/auth/line/login", json={"code": "fake_code_12345", "redirect_uri": "http://localhost:5173/login"}, timeout=10)
    # Without LINE env, the service should fail → 400 LINE_AUTH_FAILED
    test("2b-1: POST /login — fake code → 400", 400, r.status_code, r.json())
except Exception as e:
    print(f"ERROR in 2b-1: {e}")
    results.append(("2b-1", False))

# Test 2c: Existing admin login still works (POST /api/auth/login)
try:
    r = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@moobaan.com", "password": "Admin123!"}, timeout=15)
    test("2c: Admin login still works → 200", 200, r.status_code, r.json())
except Exception as e:
    print(f"ERROR in 2c: {e}")
    results.append(("2c", False))

# Test 2d: GET /api/auth/me after admin login (verify session)
try:
    session = requests.Session()
    login_r = session.post(f"{BASE}/api/auth/login", json={"email": "admin@moobaan.com", "password": "Admin123!"}, timeout=15)
    me_r = session.get(f"{BASE}/api/auth/me", timeout=15)
    test("2d: GET /me after admin login → 200", 200, me_r.status_code, me_r.json())
except Exception as e:
    print(f"ERROR in 2d: {e}")
    results.append(("2d", False))

# Summary
print(f"\n{'='*60}")
print("SUMMARY:")
for name, passed in results:
    print(f"  {'✅' if passed else '❌'} {name}")
passed_count = sum(1 for _, p in results if p)
print(f"\n{passed_count}/{len(results)} passed")
if all(p for _, p in results):
    print("ALL TESTS PASSED ✅")
print(f"{'='*60}")

# Cleanup
proc.terminate()
proc.wait(timeout=5)
print("Backend stopped.")
