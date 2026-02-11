# Authentication System - Phase 1.2

## 🔐 Overview

Authentication system สำหรับ Village Accounting System ที่รองรับ 3 roles:
- **Super Admin** - จัดการระบบทั้งหมด
- **Accounting** - จัดการการเงินและบัญชี
- **Resident** - ลูกบ้าน (ส่งสลิป ดูใบแจ้งหนี้)

**Note:** ระบบไม่มีหน้าสมัครสมาชิก - ผู้ใช้ทั้งหมดจะถูกสร้างโดย Admin เท่านั้น

## 🎯 Features

### Backend (FastAPI)
- ✅ POST `/api/auth/login` - เข้าสู่ระบบ
- ✅ POST `/api/auth/logout` - ออกจากระบบ
- ✅ GET `/api/auth/verify` - ตรวจสอบ token
- ✅ Mock JWT token generation
- ✅ Hardcoded users สำหรับ Phase 1

### Frontend (React)
- ✅ Login page (Username/Password + Remember Me)
- ✅ AuthContext - จัดการ authentication state
- ✅ ProtectedRoute - ป้องกัน unauthorized access
- ✅ Role-based navigation
- ✅ Logout functionality
- ✅ Token persistence (localStorage/sessionStorage)

## 👤 Demo Accounts (Phase 1)

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `admin` | `admin123` | Super Admin | ทุกฟีเจอร์ |
| `accounting` | `acc123` | Accounting | การเงิน, บัญชี |
| `resident` | `res123` | Resident | ส่งสลิป, ดูใบแจ้งหนี้ |

## 🚀 Usage

### 1. Login Flow

```javascript
// User เข้าสู่ระบบ
POST /api/auth/login
{
  "username": "admin",
  "password": "admin123",
  "remember_me": true
}

// Response
{
  "token": "mock_jwt_token_...",
  "user": {
    "username": "admin",
    "name": "Admin User",
    "role": "super_admin"
  }
}
```

### 2. Protected Routes

```javascript
// Frontend automatically redirects to /login if not authenticated
// Role-based access control:
// - /admin/* → super_admin, accounting
// - /accounting/* → accounting, super_admin
// - /resident/* → resident only
```

### 3. Logout

```javascript
POST /api/auth/logout?token=xxx

// Clears localStorage/sessionStorage
// Redirects to /login
```

## 🔒 Security (Phase 1 - Mock)

**⚠️ Note:** Phase 1 ใช้ mock authentication เท่านั้น

- Hardcoded users (ไม่มี database)
- Mock JWT tokens (ไม่ได้ sign จริง)
- No password hashing
- No token expiration
- No refresh tokens
- **No user registration** - Admin creates all users

**Phase 2 จะเพิ่ม:**
- Database integration (PostgreSQL)
- Real JWT with signing
- Password hashing (bcrypt)
- Token expiration & refresh
- Admin panel for user management
- Email verification (optional)

## 📱 UI Screenshots

### Login Page
- Dark theme พร้อมสีเขียว
- Username/Password fields
- Remember Me checkbox
- Demo accounts displayed
- Contact admin message (for new accounts/password reset)

### Protected Routes
- Automatic redirect to /login
- Role-based navigation menu
- User info in sidebar
- Logout button

## 🧪 Testing

```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","remember_me":false}'

# Test verify
curl "http://localhost:8000/api/auth/verify?token=mock_jwt_token_admin"

# Test logout
curl -X POST "http://localhost:8000/api/auth/logout?token=mock_jwt_token_admin"
```

## 📝 Implementation Details

### AuthContext
```javascript
// Provides authentication state to entire app
const { user, token, login, logout, isAuthenticated } = useAuth();
```

### ProtectedRoute
```javascript
// Wraps protected pages
<ProtectedRoute allowedRoles={['super_admin', 'accounting']}>
  <AdminDashboard />
</ProtectedRoute>
```

### Token Storage
- **Remember Me = true** → localStorage (persistent)
- **Remember Me = false** → sessionStorage (session only)

### User Management
- **Phase 1:** Hardcoded users only
- **Phase 2:** Admin panel to create/edit/delete users
- **Contact:** Users contact admin via LINE for new accounts or password reset

## 🔄 Next Steps (Phase 2)

1. Database integration
   - User table
   - Password hashing
   - User management CRUD

2. Real JWT
   - Secret key
   - Token signing
   - Expiration
   - Refresh tokens

3. Security enhancements
   - Rate limiting
   - CSRF protection
   - XSS prevention

4. Admin Features
   - User management panel
   - Create/Edit/Delete users
   - Reset passwords
   - View user activity

## 📚 Related Files

- `backend/app/api/auth.py` - Auth API endpoints
- `frontend/src/contexts/AuthContext.jsx` - Auth state management
- `frontend/src/components/ProtectedRoute.jsx` - Route protection
- `frontend/src/pages/auth/Login.jsx` - Login page
- `frontend/src/components/Layout.jsx` - Logout functionality

---

**Status:** ✅ Phase 1.2 Complete (Login/Logout Only)
**Last Updated:** 2025-01-12
**Changes:** Removed registration feature - Admin creates all users
