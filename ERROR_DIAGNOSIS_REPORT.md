# 🚨 Backend Error Diagnosis Report
**Date:** January 14, 2026  
**Project:** Moobaan Smart (Village Accounting System)  
**Environment:** Local Development (127.0.0.1:5173 → 127.0.0.1:8000)  
**Status:** 🔴 **CRITICAL - Backend Not Operational**

---

## 📋 Executive Summary

The backend server is **completely non-functional** due to a **database configuration mismatch**. All API endpoints return **500 Internal Server Error** because the application cannot start.

**Root Cause:** `.env` file is missing, causing `DATABASE_URL` validation to fail at startup.

**Impact:**
- ❌ Backend server cannot start
- ❌ All API endpoints unavailable (500 errors)
- ❌ Frontend completely broken (CORS + Network errors)
- ❌ Zero functionality available

---

## 🔍 Detailed Error Analysis

### **Error 1: Missing `.env` File** 🔴 CRITICAL

**Location:** `/backend/.env`  
**Status:** File does not exist (only `.env.example` present)

**Error Message:**
```
❌ Configuration validation failed: Invalid DATABASE_URL scheme. 
Got: mysql://A65Pgp7Hx3NjxmG.97ae8a... 
Expected: postgresql+psycopg://user:password@host:port/dbname
```

**Root Cause:**
1. `.env` file was never created from `.env.example`
2. Application is reading `DATABASE_URL` from system environment (Railway MySQL URL)
3. Config validation enforces PostgreSQL but finds MySQL URL

**Code Reference:**
```python
# backend/app/core/config.py:41-46
if not self.DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError(
        f"Invalid DATABASE_URL scheme. Got: {self.DATABASE_URL[:30]}... "
        f"Expected: postgresql+psycopg://user:password@host:port/dbname. "
        f"This enforces PostgreSQL with psycopg v3 driver ONLY."
    )
```

**Impact:**
- Backend cannot initialize
- All imports fail
- No API endpoints available

---

### **Error 2: Database Schema Mismatch** 🔴 CRITICAL

**Issue:** Even if `.env` is created, the database schema is outdated.

**Missing Tables/Columns:**
- `payin_reports` table may not exist
- `house_members` table structure changed
- Invoice-related tables need migration

**Evidence:**
```python
# backend/app/api/dashboard.py:23-25
membership = db.query(HouseMember).filter(
    HouseMember.user_id == current_user.id
).first()
```

This query will fail if:
1. `house_members` table doesn't exist
2. Schema doesn't match model definition

---

### **Error 3: CORS Configuration** ⚠️ SECONDARY

**Status:** CORS config is correct, but appears broken because backend is down

**Current Config:**
```python
# backend/app/main.py:34-44
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://moobaan-smart.vercel.app",
    "*"  # Allow all origins
],
```

**Issue:** `"*"` + `allow_credentials=True` is invalid in CORS spec

**Fix Required:**
```python
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
],
# Remove "*" when using credentials
```

---

### **Error 4: Frontend API Calls** ⚠️ SECONDARY

**Pay-ins Report Error:**
```
GET http://127.0.0.1:8000/api/payin-reports
net::ERR_FAILED 500 (Internal Server Error)
```

**Resident Dashboard Error:**
```
GET http://127.0.0.1:8000/api/payin-reports
net::ERR_FAILED 500 (Internal Server Error)
```

**Root Cause:** Backend is down, so all requests fail

---

## 🛠️ Step-by-Step Fix Instructions

### **Step 1: Create `.env` File** ⚡ IMMEDIATE

```bash
cd backend
cp .env.example .env
```

**Edit `.env` and set:**
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/moobaan_smart
SECRET_KEY=your-secret-key-here-change-in-production
```

**For SQLite (easier for local dev):**
```env
DATABASE_URL=sqlite:///./moobaan_smart.db
```

**⚠️ BUT:** Current code enforces PostgreSQL only! Need to either:
1. Install PostgreSQL locally, OR
2. Modify `config.py` to allow SQLite

---

### **Step 2: Fix Database URL Validation** ⚡ IMMEDIATE

**Option A: Allow SQLite (Recommended for local dev)**

Edit `backend/app/core/config.py`:
```python
def _validate_database_url(self):
    """Allow PostgreSQL OR SQLite for local development"""
    if not self.DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is required.")
    
    allowed_schemes = ["postgresql+psycopg://", "sqlite:///"]
    if not any(self.DATABASE_URL.startswith(scheme) for scheme in allowed_schemes):
        raise RuntimeError(
            f"Invalid DATABASE_URL scheme. Got: {self.DATABASE_URL[:30]}... "
            f"Expected: postgresql+psycopg:// or sqlite:///"
        )
```

**Option B: Install PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb moobaan_smart
```

---

### **Step 3: Run Database Migrations** ⚡ IMMEDIATE

```bash
cd backend

# Initialize Alembic (if not done)
alembic upgrade head

# OR run seed script
python3 simple_seed.py
```

**Expected Output:**
```
✅ Database initialized
✅ Tables created
✅ Seed data inserted
```

---

### **Step 4: Fix CORS Config** 🔧 IMPORTANT

Edit `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        # Remove "*" - it conflicts with allow_credentials=True
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### **Step 5: Start Backend Server** 🚀

```bash
cd backend
python3 run_server.py

# OR
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
✅ Configuration loaded successfully for moobaan_smart_backend
```

---

### **Step 6: Verify API Endpoints** ✅

**Test in browser or curl:**
```bash
# Health check
curl http://127.0.0.1:8000/

# Dashboard (requires auth)
curl http://127.0.0.1:8000/api/dashboard/summary

# Pay-ins (requires auth)
curl http://127.0.0.1:8000/api/payin-reports
```

---

## 📊 Error Priority Matrix

| Error | Severity | Impact | Fix Time | Blocking |
|-------|----------|--------|----------|----------|
| Missing `.env` | 🔴 CRITICAL | 100% | 2 min | YES |
| DB URL Validation | 🔴 CRITICAL | 100% | 5 min | YES |
| Database Schema | 🔴 CRITICAL | 100% | 10 min | YES |
| CORS Config | 🟡 MEDIUM | 50% | 2 min | NO |
| Frontend API | 🟢 LOW | 0% | 0 min | NO |

---

## 🎯 Recommended Action Plan

### **Phase 1: Emergency Fix (15 minutes)**
1. ✅ Create `.env` file
2. ✅ Modify `config.py` to allow SQLite
3. ✅ Run `simple_seed.py`
4. ✅ Start backend server
5. ✅ Test basic endpoints

### **Phase 2: CORS Fix (5 minutes)**
1. ✅ Remove `"*"` from `allow_origins`
2. ✅ Restart backend
3. ✅ Test frontend connectivity

### **Phase 3: Verification (10 minutes)**
1. ✅ Test Pay-ins Report page
2. ✅ Test Resident Dashboard
3. ✅ Test Submit Payment
4. ✅ Verify no console errors

---

## 🔬 Testing Checklist

### **Backend Tests**
- [ ] Backend starts without errors
- [ ] `/` returns `{"name": "moobaan_smart_backend", "status": "running"}`
- [ ] `/api/dashboard/summary` returns data (with auth)
- [ ] `/api/payin-reports` returns data (with auth)
- [ ] No database connection errors in logs

### **Frontend Tests**
- [ ] Login works (admin/admin123)
- [ ] Dashboard loads without errors
- [ ] Pay-ins page loads without errors
- [ ] Resident dashboard loads (resident/res123)
- [ ] No CORS errors in console
- [ ] No 500 errors in network tab

---

## 📝 Additional Notes

### **Why PostgreSQL Enforcement?**
The code enforces PostgreSQL because:
1. Production uses PostgreSQL (Railway)
2. SQLAlchemy dialect differences between SQLite/PostgreSQL
3. Prevent production bugs from dev/prod parity issues

**Recommendation:** Use PostgreSQL locally to match production

### **Alternative: Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: moobaan_smart
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
```

```bash
docker-compose up -d
```

---

## 🚀 Quick Start Commands (Copy-Paste)

```bash
# 1. Create .env
cd backend
echo 'DATABASE_URL=sqlite:///./moobaan_smart.db' > .env
echo 'SECRET_KEY=dev-secret-key-change-in-production' >> .env

# 2. Modify config.py to allow SQLite
# (Manual edit required - see Step 2 above)

# 3. Initialize database
python3 simple_seed.py

# 4. Start server
python3 run_server.py

# 5. Test (in another terminal)
curl http://127.0.0.1:8000/
```

---

## 📞 Support Information

**For Local Dev AI:**
- This report contains all information needed to fix the backend
- Follow steps 1-6 in order
- Each step is independent and can be verified
- Total fix time: ~30 minutes

**Critical Files to Modify:**
1. `backend/.env` (create new)
2. `backend/app/core/config.py` (allow SQLite)
3. `backend/app/main.py` (fix CORS)

**No Frontend Changes Required** - all issues are backend-only

---

**Report Generated By:** Manus AI Assistant  
**For:** Local Development Team  
**Next Action:** Follow Phase 1 (Emergency Fix)
