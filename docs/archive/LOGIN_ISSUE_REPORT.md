# 🚨 Login Authentication Issue - CRITICAL

**Date**: January 17, 2026  
**Status**: ❌ UNSOLVED - Need Team Investigation  
**Priority**: CRITICAL - System Unusable  
**Affected Feature**: User Authentication (POST /api/auth/login)

---

## Executive Summary

Login authentication fails with **401 Unauthorized** despite:
- ✅ Correct password (verified via direct test)
- ✅ Valid password hash in database (argon2id format)
- ✅ Password verification function works correctly in isolation
- ✅ Database connection working
- ✅ User exists and is active

**Hypothesis**: Issue lies in HTTP request layer - something between frontend/HTTP client and backend authentication logic is failing.

---

## Problem Description

### Symptom
User attempts to login at http://127.0.0.1:5173 with valid credentials:
- **Email**: admin@moobaan.com
- **Password**: Admin123!

**Result**: 401 Unauthorized

### Backend Logs (Before Debug Logging)
```
INFO:     127.0.0.1:62051 - "POST /api/auth/login HTTP/1.1" 401 Unauthorized
INFO:sqlalchemy.engine.Engine SELECT users.id, users.email, ... WHERE users.email = %(email_1)s
INFO:sqlalchemy.engine.Engine ROLLBACK
```

**Observation**: Query executes, but then immediate ROLLBACK and 401 response.

---

## Investigation Steps Completed

### 1. Database Verification ✅
```bash
python backend/check_db.py
```

**Result**:
- 6 users found in database
- Admin user exists (ID: 15, email: admin@moobaan.com)
- Role: super_admin
- is_active: True
- Password hash: $argon2id$v=19$m=65536,t=3,p=4$aA0hRGhtbc251xrj3JtTSg$ga2YCKPYuCzdyJE0ms6qkvmM1ALURCCm8JotTt4d1WQ

### 2. Password Reset ✅
```bash
python backend/quick_reset_password.py
```

**Result**:
- Password reset to "Admin123!" successful
- New hash written to database
- Hash verified correct format (argon2id)

### 3. Direct Authentication Logic Test ✅
```bash
python backend/test_direct_login.py
```

**Result**: ✅ **ALL TESTS PASSED**
```
1. Getting user from database...
   ✅ User found: admin@moobaan.com
   - ID: 15
   - Role: super_admin
   - Active: True
   - Hash: $argon2id$v=19$m=65536,t=3,p=4$aA0hRGhtbc251xrj3Jt...

2. Testing direct password verification...
   Testing password: 'Admin123!'
   [DEBUG] Verifying password...
   [DEBUG] Plain password length: 9
   [DEBUG] Hash starts with: $argon2id$v=19$m=65536,t=3,p=4...
   [DEBUG] Verification result: True
   Result: True
   ✅ Password verification PASSED

3. Testing authenticate_user() function...
   [DEBUG] Verifying password...
   [DEBUG] Plain password length: 9
   [DEBUG] Hash starts with: $argon2id$v=19$m=65536,t=3,p=4...
   [DEBUG] Verification result: True
   ✅ authenticate_user() PASSED
   - User: admin@moobaan.com
   - Role: super_admin

4. Testing with wrong password...
   [DEBUG] Verifying password...
   [DEBUG] Plain password length: 13
   [DEBUG] Hash starts with: $argon2id$v=19$m=65536,t=3,p=4...
   [DEBUG] Verification result: False
   ✅ Wrong password REJECTED (correct)
```

**Conclusion**: Authentication logic is **100% correct** when tested directly.

### 4. HTTP Layer Testing ❌

**Problem**: Unable to complete HTTP test due to backend server shutdown issue.

**Attempted**:
- curl requests → Backend shuts down on receiving request
- Python http.client test → Same issue
- PowerShell Invoke-WebRequest → Same issue

**Observation**: Backend server unexpectedly shuts down when receiving ANY HTTP request, making it impossible to capture debug logs from actual login attempts.

---

## Debug Logging Added

### Files Modified with Debug Logging

#### 1. `backend/app/core/auth.py` - verify_password()
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        print(f"[DEBUG] Verifying password...")
        print(f"[DEBUG] Plain password length: {len(plain_password)}")
        print(f"[DEBUG] Hash starts with: {hashed_password[:30]}...")
        
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"[DEBUG] Verification result: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] Password verification error: {e}")
        traceback.print_exc()
        return False
```

#### 2. `backend/app/api/auth.py` - login()
```python
@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    print(f"[LOGIN] Received login request")
    print(f"[LOGIN] Email: {login_data.email}")
    print(f"[LOGIN] Password length: {len(login_data.password)}")
    print(f"[LOGIN] Password type: {type(login_data.password)}")
    
    user = authenticate_user(login_data.email, login_data.password, db)
    print(f"[LOGIN] authenticate_user result: {user}")
    
    if not user:
        print(f"[LOGIN] Authentication FAILED - user is False/None")
        raise HTTPException(...)
```

#### 3. `backend/app/main.py` - Request Logging Middleware
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"🔵 {request.method} {request.url.path}")
    
    if request.method == "POST" and "/login" in str(request.url.path):
        logger.info(f"   Content-Type: {request.headers.get('content-type')}")
        logger.info(f"   Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    logger.info(f"   Response: {response.status_code}")
    return response
```

**Status**: Debug logging added but **unable to capture output** due to server shutdown issue.

---

## Technical Details

### Stack
- **Backend**: FastAPI 0.100+ with Uvicorn
- **Database**: PostgreSQL in Docker (container "docker-db-1" - RUNNING)
- **Password Hashing**: passlib with argon2id (CryptContext)
- **Frontend**: React 18 + Vite (port 5173)
- **OS**: Windows

### Password Hash Details
```
Algorithm: argon2id
Version: 19
Memory: 65536 KB
Time: 3 iterations
Parallelism: 4 threads
Hash: $argon2id$v=19$m=65536,t=3,p=4$aA0hRGhtbc251xrj3JtTSg$ga2YCKPYuCzdyJE0ms6qkvmM1ALURCCm8JotTt4d1WQ
```

### Authentication Flow
```
Frontend (Login.jsx)
  ↓ POST /api/auth/login { email, password }
AuthContext.jsx (api.post)
  ↓ axios request
Backend Middleware (log_requests)
  ↓
FastAPI Route (auth.py::login)
  ↓
authenticate_user(email, password, db)
  ↓ Query user by email
  ↓ verify_password(password, user.hashed_password)
  ↓ Check user.is_active
  ↓ Return user object
Return 401 if False
```

---

## Test Files Created

### 1. `backend/test_direct_login.py` ✅
Direct test of authentication logic without HTTP layer.
**Status**: All tests passing

### 2. `backend/test_http_login.py` ❌
HTTP test using http.client to call login endpoint.
**Status**: Unable to complete - server shutdown issue

### 3. `backend/test_login_api.py` ❌
Test using FastAPI TestClient.
**Status**: Unable to run - venv dependency issues

### 4. `backend/quick_reset_password.py` ✅
Standalone password reset script.
**Status**: Successfully reset admin password

### 5. `backend/debug_server.py` ✅
Debug server with detailed logging.
**Status**: Starts successfully but shuts down on receiving HTTP requests

---

## Evidence: Direct Test vs HTTP Request

### Direct Test (WORKS) ✅
```python
# Direct function call
from app.core.auth import authenticate_user
db = SessionLocal()
result = authenticate_user("admin@moobaan.com", "Admin123!", db)
# Result: <User object> (SUCCESS)
```

### HTTP Request (FAILS) ❌
```http
POST /api/auth/login HTTP/1.1
Content-Type: application/json

{
  "email": "admin@moobaan.com",
  "password": "Admin123!"
}

Response: 401 Unauthorized
```

**Gap**: Something between HTTP request parsing and authentication function execution causes failure.

---

## Hypotheses for Team Investigation

### Hypothesis 1: Request Body Parsing Issue
**Theory**: Password might be getting corrupted/modified during request body parsing.

**Evidence**:
- Direct test with string literal works
- HTTP request fails with same string
- Need to capture actual password received by login endpoint

**Action Needed**: 
- Successfully start backend server
- Capture debug output from actual login attempt
- Compare password string received vs expected

### Hypothesis 2: Middleware Interference
**Theory**: CORS or other middleware might be modifying request.

**Evidence**:
- Backend has CORS middleware enabled
- Request logging middleware added
- No evidence of middleware errors in logs

**Action Needed**:
- Check if middleware modifies request body
- Test with minimal middleware config

### Hypothesis 3: Encoding/Character Set Issue
**Theory**: Password encoding differs between direct call and HTTP.

**Evidence**:
- Debug logging shows password length = 9 in direct test
- Need to verify length in HTTP request
- Special characters in password: "Admin123!"

**Action Needed**:
- Log raw bytes of password received
- Compare encoding (UTF-8, ASCII, etc.)

### Hypothesis 4: Database Transaction Issue
**Theory**: ROLLBACK after query suggests transaction problem.

**Evidence**:
- Logs show: SELECT → ROLLBACK → 401
- Direct test commits successfully
- HTTP request triggers rollback

**Action Needed**:
- Check if exception occurs during authentication
- Verify database session handling in HTTP context

### Hypothesis 5: Server Stability Issue
**Theory**: Backend server has critical bug causing crashes on HTTP requests.

**Evidence**:
- Server starts successfully
- Shuts down immediately on receiving ANY HTTP request
- curl, Python http.client, PowerShell all trigger shutdown
- No error messages in shutdown logs

**Action Needed**:
- Investigate why server shuts down on HTTP requests
- Check for critical exceptions or signal handling
- May need to run in different environment (Docker, Linux, etc.)

---

## Files Modified (Debug Version)

1. ✅ `backend/app/core/auth.py` - Added verification debug logs
2. ✅ `backend/app/api/auth.py` - Added login endpoint debug logs
3. ✅ `backend/app/main.py` - Added request logging middleware
4. ✅ `frontend/src/contexts/AuthContext.jsx` - Fixed token storage order

---

## How to Reproduce

### Setup
1. Ensure Docker database is running
2. Start backend: `python backend/debug_server.py`
3. Start frontend: `npm run dev` (in frontend/)

### Test 1: Direct Authentication (Works) ✅
```bash
cd backend
python test_direct_login.py
```

**Expected**: All 4 tests pass
**Actual**: ✅ PASS

### Test 2: HTTP Login (Fails) ❌
1. Open browser to http://127.0.0.1:5173
2. Enter credentials:
   - Email: admin@moobaan.com
   - Password: Admin123!
3. Click "Login"

**Expected**: Successful login and redirect
**Actual**: ❌ 401 Unauthorized

**Unable to capture debug output**: Backend server shuts down on receiving HTTP request.

### Test 3: Manual HTTP Request (Fails) ❌
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@moobaan.com","password":"Admin123!"}'
```

**Expected**: 200 OK with token or debug output
**Actual**: Backend server shuts down immediately, no response

---

## What We Know

### ✅ Working (Confirmed)
1. Database connection and queries
2. User exists with correct data
3. Password hash is valid (argon2id format)
4. Password verification function (pwd_context.verify)
5. authenticate_user() function logic
6. Direct Python function calls

### ❌ Not Working (Confirmed)
1. HTTP POST /api/auth/login (401 Unauthorized)
2. Backend server stability (shuts down on HTTP requests)
3. Actual login via frontend UI
4. Actual login via curl/http.client

### ❓ Unknown (Need Investigation)
1. Why backend server shuts down on HTTP requests
2. What password string is received in login endpoint
3. Whether request body is parsed correctly
4. Whether any exceptions occur during HTTP request handling
5. Root cause of authenticate_user() returning False in HTTP context

---

## Next Steps for Team

### Immediate Actions
1. **Investigate Server Shutdown**
   - Why does backend shut down on receiving HTTP requests?
   - Check for critical bugs in middleware or route handlers
   - Try running backend in Docker instead of Windows directly

2. **Capture Debug Output**
   - Successfully start backend and keep it running
   - Trigger login from frontend or curl
   - Capture and analyze debug logs

3. **Compare Request Data**
   - Log raw request body in middleware
   - Log parsed LoginRequest in endpoint
   - Compare with direct test data

4. **Test in Different Environment**
   - Try running on Linux VM
   - Try running in Docker container
   - Check if Windows-specific issue

### Medium-term Actions
1. Add comprehensive error handling
2. Add request/response logging at all layers
3. Create integration test suite with TestClient
4. Document authentication flow thoroughly

---

## Files for Reference

### Test Scripts
- `backend/test_direct_login.py` - Direct authentication test (WORKING)
- `backend/test_http_login.py` - HTTP client test (SERVER CRASHES)
- `backend/quick_reset_password.py` - Password reset utility (WORKING)
- `backend/debug_server.py` - Debug server launcher (STARTS BUT CRASHES)

### Modified Source Files (Debug Logging)
- `backend/app/core/auth.py` - Password verification debug
- `backend/app/api/auth.py` - Login endpoint debug
- `backend/app/main.py` - Request middleware debug

### Frontend
- `frontend/src/contexts/AuthContext.jsx` - Login function
- `frontend/src/pages/auth/Login.jsx` - Login form

---

## Environment Details

```
OS: Windows
Python: 3.13
FastAPI: 0.100+
Database: PostgreSQL 15 (Docker)
Frontend: React 18 + Vite

Docker Containers:
- docker-db-1 (PostgreSQL) - RUNNING

Ports:
- Backend: 8000
- Frontend: 5173
- Database: 5432
```

---

## Contact Information

**Developer**: GitHub Copilot (AI Assistant)  
**User**: [Project Owner]  
**Report Date**: January 17, 2026  
**Last Update**: January 17, 2026 15:30 ICT

---

## Summary

✅ **What Works**: Direct authentication logic is 100% correct  
❌ **What Fails**: HTTP login requests return 401 Unauthorized  
🚨 **Critical Issue**: Backend server shuts down on receiving HTTP requests  
🔍 **Need**: Team investigation to identify HTTP layer issue  
⏰ **Impact**: System completely unusable - no users can login

**Please investigate server shutdown issue and capture actual debug output from HTTP login attempt.**

---

**END OF REPORT**
