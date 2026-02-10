"""
D.4.1 Hardening Patch — Level 2 API Test
Tests all 6 patches: PATCH-1 through PATCH-6
"""
import requests
import json

base = 'http://localhost:8000'
results = []

def test(name, actual, expected, ok):
    results.append((name, actual, expected, ok))

# Test 1: Login endpoint alive
r = requests.post(f'{base}/api/auth/login', json={})
test('POST /api/auth/login (empty body)', r.status_code, 422, r.status_code == 422)

# Test 2: /me requires auth
r = requests.get(f'{base}/api/auth/me')
test('GET  /api/auth/me (no auth)', r.status_code, 401, r.status_code == 401)

# Test 3: Refresh requires cookie
r = requests.post(f'{base}/api/auth/refresh')
test('POST /api/auth/refresh (no cookie)', r.status_code, 401, r.status_code == 401)

# Test 4: LINE config
r = requests.get(f'{base}/api/auth/line/config?redirect_uri=http://localhost:5173/login')
test('GET  /api/auth/line/config', r.status_code, '200|503', r.status_code in [200, 503])

# Test 5: LINE login with bad code
r = requests.post(f'{base}/api/auth/line/login', json={'code': 'test', 'redirect_uri': 'http://localhost:5173/login'})
test('POST /api/auth/line/login (bad code)', r.status_code, 400, r.status_code == 400)

# Test 6: Admin login full flow
s = requests.Session()
r = s.post(f'{base}/api/auth/login', json={'email': 'admin@moobaan.com', 'password': 'admin123'})
login_ok = r.status_code == 200
test('POST /api/auth/login (admin creds)', r.status_code, 200, login_ok)

if login_ok:
    # PATCH-1: Check cookie paths
    for c in s.cookies:
        if c.name == 'refresh_token':
            test('PATCH-1: refresh_token path', c.path, '/api/auth', c.path == '/api/auth')
        if c.name == 'access_token':
            test('PATCH-1: access_token path', c.path, '/', c.path == '/')

    # PATCH-5: Check /me response shape
    r2 = s.get(f'{base}/api/auth/me')
    me_ok = r2.status_code == 200
    test('GET /api/auth/me (authed admin)', r2.status_code, 200, me_ok)
    
    if me_ok:
        data = r2.json()
        keys = sorted(data.keys())
        required = {'id', 'role', 'house_id', 'house_code', 'houses'}
        has_all = required.issubset(set(data.keys()))
        test('PATCH-5: /me has required keys', str(required), 'subset of response', has_all)
        test('PATCH-5: houses is list', type(data.get('houses')).__name__, 'list', isinstance(data.get('houses'), list))
        test('PATCH-5: admin houses=[]', str(data.get('houses')), '[]', data.get('houses') == [])
        print(f"  /me response: {json.dumps(data, indent=2, default=str)}")

    # PATCH-6: Test refresh works (session_version in tokens)
    r3 = s.post(f'{base}/api/auth/refresh')
    test('POST /api/auth/refresh (admin)', r3.status_code, 200, r3.status_code == 200)
    
    # After refresh, /me should still work
    if r3.status_code == 200:
        r4 = s.get(f'{base}/api/auth/me')
        test('GET /api/auth/me (after refresh)', r4.status_code, 200, r4.status_code == 200)

    # Test logout
    r5 = s.post(f'{base}/api/auth/logout')
    test('POST /api/auth/logout', r5.status_code, 200, r5.status_code == 200)
else:
    print(f"  Login failed: {r.status_code} - {r.text}")

# Print results
print()
print('=' * 65)
print('D.4.1 HARDENING PATCH — Level 2 API Test Results')
print('=' * 65)
all_pass = True
for name, actual, expected, ok in results:
    status = '✅' if ok else '❌'
    if not ok:
        all_pass = False
    print(f'  {status} {name}: got={actual} expect={expected}')
print('=' * 65)
passed = sum(1 for _, _, _, o in results if o)
print(f'Overall: {"ALL PASS ✅" if all_pass else "SOME FAILED ❌"} ({passed}/{len(results)})')
