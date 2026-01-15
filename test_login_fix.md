# 🧪 Test Script: Login Redirect Loop Fix

**Purpose:** Verify that the login redirect loop is fixed  
**Estimated Time:** 5 minutes  
**Prerequisites:** Backend and frontend running

---

## 🚀 Pre-Test Setup

### 1. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

**Expected Output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

### 3. Open Browser
- Open Chrome/Firefox
- Navigate to: `http://localhost:5173`
- Open DevTools (F12)

---

## ✅ Test Case 1: Fresh Login (No Token)

**Objective:** Verify login works without redirect loop

### Steps:
1. **Clear browser data**
   - F12 → Application → Storage → Clear site data
   - Or: Ctrl+Shift+Delete → Clear browsing data

2. **Navigate to login**
   - URL: `http://localhost:5173/login`
   - Should see login form

3. **Check localStorage (Before Login)**
   - F12 → Application → Local Storage → http://localhost:5173
   - Should be empty (no `auth_token`)

4. **Login as Admin**
   - Email: `admin`
   - Password: `admin123`
   - Click "เข้าสู่ระบบ / Login"

5. **Observe redirect**
   - Should navigate to `/admin/dashboard`
   - Should NOT redirect back to `/login`
   - URL should stay: `http://localhost:5173/admin/dashboard`

6. **Check localStorage (After Login)**
   - F12 → Application → Local Storage
   - Should have `auth_token` with JWT value

7. **Check console**
   - Should NOT see repeated navigation logs
   - Should NOT see "Redirecting to login" messages

### Expected Result:
✅ **PASS:** Lands on dashboard, no redirect loop  
❌ **FAIL:** Redirects back to login repeatedly

---

## ✅ Test Case 2: Page Refresh (Token Exists)

**Objective:** Verify authentication persists after refresh

### Steps:
1. **After successful login** (from Test Case 1)
   - Should be on `/admin/dashboard`

2. **Press F5** (Refresh page)

3. **Observe behavior**
   - Should stay on `/admin/dashboard`
   - Should NOT redirect to `/login`
   - Dashboard data should load

4. **Check localStorage**
   - Should still have `auth_token`

5. **Check network tab**
   - Should see `GET /api/auth/me` (200 OK)
   - Should see `GET /api/dashboard/admin` (200 OK)

### Expected Result:
✅ **PASS:** Stays authenticated, no redirect  
❌ **FAIL:** Redirects to login after refresh

---

## ✅ Test Case 3: Direct URL Access (Token Exists)

**Objective:** Verify protected routes work with existing token

### Steps:
1. **After successful login**
   - Should have token in localStorage

2. **Open new tab**
   - Press Ctrl+T (new tab)

3. **Navigate directly to protected route**
   - URL: `http://localhost:5173/admin/payins`

4. **Observe behavior**
   - Should load Pay-ins page directly
   - Should NOT redirect to login

5. **Try other protected routes**
   - `/admin/houses`
   - `/admin/members`
   - `/admin/expenses`

### Expected Result:
✅ **PASS:** All protected routes load without redirect  
❌ **FAIL:** Redirects to login despite having token

---

## ✅ Test Case 4: Logout

**Objective:** Verify logout clears authentication properly

### Steps:
1. **After successful login**
   - Should be on dashboard

2. **Click logout button**
   - Look for "ออกจากระบบ / Logout" in header
   - Click it

3. **Observe redirect**
   - Should redirect to `/login`

4. **Check localStorage**
   - F12 → Application → Local Storage
   - Should NOT have `auth_token` (cleared)

5. **Try to access protected route**
   - Navigate to: `http://localhost:5173/admin/dashboard`

6. **Observe behavior**
   - Should redirect to `/login`
   - Should NOT be able to access dashboard

### Expected Result:
✅ **PASS:** Logout clears token, redirects to login  
❌ **FAIL:** Token remains or can still access protected routes

---

## ✅ Test Case 5: Invalid Token

**Objective:** Verify invalid tokens are rejected

### Steps:
1. **Logout** (clear existing token)

2. **Manually set invalid token**
   - F12 → Console
   - Run: `localStorage.setItem('auth_token', 'invalid_token_12345')`

3. **Navigate to protected route**
   - URL: `http://localhost:5173/admin/dashboard`

4. **Observe behavior**
   - Should attempt to load
   - Backend should reject token (401 Unauthorized)
   - Should redirect to `/login`

5. **Check console**
   - Should see "Auth check failed" or similar error

6. **Check localStorage**
   - Token should be cleared after failed validation

### Expected Result:
✅ **PASS:** Invalid token rejected, redirects to login  
❌ **FAIL:** Invalid token accepted or no redirect

---

## 🎯 Test Matrix

| Test Case | Scenario | Expected Behavior | Status |
|-----------|----------|-------------------|--------|
| 1 | Fresh login (no token) | Navigate to dashboard, no loop | ⬜ |
| 2 | Page refresh (has token) | Stay authenticated | ⬜ |
| 3 | Direct URL (has token) | Load protected route | ⬜ |
| 4 | Logout | Clear token, redirect to login | ⬜ |
| 5 | Invalid token | Reject and redirect to login | ⬜ |

**Legend:**
- ⬜ Not tested
- ✅ Passed
- ❌ Failed

---

## 🐛 Debugging Failed Tests

### If Test 1 Fails (Redirect Loop)

**Check:**
1. Is the fix applied? (Line 90 in AuthContext.jsx)
   ```javascript
   isAuthenticated: !!token || !!localStorage.getItem('auth_token'),
   ```

2. Is localStorage being set?
   - F12 → Application → Local Storage
   - Should have `auth_token` after login

3. Check console for errors
   - Look for "Auth check failed"
   - Look for CORS errors

**Common Issues:**
- Fix not applied correctly
- Backend not running
- CORS misconfiguration

---

### If Test 2 Fails (Refresh Loses Auth)

**Check:**
1. Is `checkAuth()` being called on mount?
   - Should see `GET /api/auth/me` in Network tab

2. Is token in localStorage?
   - F12 → Application → Local Storage

3. Is backend validating token correctly?
   - Check backend logs for `/api/auth/me` requests

**Common Issues:**
- Token not persisted in localStorage
- Backend token validation failing
- CORS issues on `/api/auth/me`

---

### If Test 4 Fails (Logout Doesn't Work)

**Check:**
1. Is `clearAuth()` being called?
   - Add console.log in `clearAuth()` function

2. Is localStorage being cleared?
   - F12 → Application → Local Storage
   - Should be empty after logout

3. Is Authorization header being removed?
   - Check Network tab → Headers
   - Should NOT have `Authorization: Bearer ...`

**Common Issues:**
- `clearAuth()` not called in logout
- localStorage not cleared
- Authorization header still set

---

## 📊 Test Results Template

**Date:** ___________  
**Tester:** ___________  
**Environment:** Local Development

| Test | Result | Notes |
|------|--------|-------|
| Test 1: Fresh Login | ⬜ Pass / ❌ Fail | |
| Test 2: Page Refresh | ⬜ Pass / ❌ Fail | |
| Test 3: Direct URL | ⬜ Pass / ❌ Fail | |
| Test 4: Logout | ⬜ Pass / ❌ Fail | |
| Test 5: Invalid Token | ⬜ Pass / ❌ Fail | |

**Overall Status:** ⬜ All Pass / ❌ Some Failed

**Issues Found:**
- 
- 

**Next Steps:**
- 
- 

---

## 🎉 Success Criteria

**Fix is verified if:**
- ✅ All 5 test cases pass
- ✅ No console errors during normal flow
- ✅ localStorage properly managed
- ✅ Backend receives valid tokens
- ✅ No redirect loops observed

**Ready for:**
- ✅ Commit to Git
- ✅ Push to GitHub
- ✅ Mark as complete in TODO

---

## 📝 Post-Test Actions

### If All Tests Pass:

1. **Commit the fix**
   ```bash
   git add frontend/src/contexts/AuthContext.jsx
   git commit -m "fix: resolve login redirect loop by using localStorage check"
   ```

2. **Push to GitHub**
   ```bash
   git push origin master
   ```

3. **Update TODO**
   - Mark login fix as complete
   - Add test results

4. **Document in changelog**
   - Add to CHANGELOG.md or release notes

### If Tests Fail:

1. **Document failures**
   - Which tests failed
   - Error messages
   - Screenshots

2. **Debug using guides above**

3. **Re-test after fixes**

4. **Report to team if stuck**

---

## 🔗 Related Documentation

- `LOGIN_REDIRECT_LOOP_ANALYSIS.md` - Full technical analysis
- `QUICK_FIX_LOGIN_REDIRECT.md` - Quick fix guide
- `login_race_condition.md` - Visual diagrams

---

**Status:** 📋 Ready to test  
**Complexity:** Low (5 minutes)  
**Automation:** Can be automated with Playwright/Cypress later
