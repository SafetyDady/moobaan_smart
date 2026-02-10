"""
Phase D.4.1 - LINE Auth API Tests (Level 2)
Tests backend LINE endpoints without LINE env vars set.
"""
import requests
import json
import sys

BASE = "http://127.0.0.1:8000"
results = []

def test(name, expected_status, actual_status, body):
    passed = expected_status == actual_status
    status = "PASS ✅" if passed else "FAIL ❌"
    results.append(passed)
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
    test("GET /config — no LINE env → 503", 503, r.status_code, r.json())
except Exception as e:
    print(f"ERROR: {e}")
    results.append(False)

# Test 2b-1: POST /api/auth/line/login (fake code → 400)
try:
    r = requests.post(f"{BASE}/api/auth/line/login", json={"code": "fake_code_12345", "redirect_uri": "http://localhost:5173/login"}, timeout=5)
    test("POST /login — fake code → 400", 400, r.status_code, r.json())
except Exception as e:
    print(f"ERROR: {e}")
    results.append(False)

# Summary
print(f"\n{'='*60}")
print(f"SUMMARY: {sum(results)}/{len(results)} passed")
if all(results):
    print("ALL TESTS PASSED ✅")
else:
    print("SOME TESTS FAILED ❌")
    sys.exit(1)
