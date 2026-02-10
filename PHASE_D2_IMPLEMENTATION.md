# Phase D.2: Admin Revoke Resident Session - Implementation Summary

## Overview
This phase implements the ability for admins to force-logout resident users by incrementing their `session_version` in the database, which invalidates all existing JWT tokens.

## Implementation Details

### 1. Database Migration
**File:** `backend/alembic/versions/d2_session_version.py`
- Added `session_version` column to `users` table
- Type: Integer, NOT NULL, default=1
- Purpose: Track session version for token validation

### 2. User Model Update
**File:** `backend/app/db/models/user.py`
- Added `session_version = Column(Integer, nullable=False, default=1)`

### 3. JWT Token Update
**File:** `backend/app/api/resident_auth.py` (verify-otp endpoint)
- Include `session_version` in resident JWT payload:
```python
token_data = {
    "sub": str(user.id),
    "role": "resident",
    "session_version": user.session_version,
}
```

### 4. Token Verification Update
**File:** `backend/app/core/auth.py`
- `verify_token()` now returns `session_version` from payload

### 5. Session Validation Middleware
**File:** `backend/app/core/deps.py`
- `get_current_user()` validates session_version for residents:
```python
if user.role == "resident":
    token_session_version = token_data.get("session_version")
    if token_session_version is not None and token_session_version != user.session_version:
        raise HTTPException(status_code=401, detail="SESSION_REVOKED")
```

### 6. Resident Endpoint Protection
**File:** `backend/app/api/resident_auth.py`
- Updated `get_resident_token_payload()` helper to accept `db` parameter
- Added session_version validation to all resident endpoints:
  - `/api/resident/me`
  - `/api/resident/houses`
  - `/api/resident/select-house`
  - `/api/resident/switch-house`
  - `/api/resident/me/context`
  - `require_active_house` dependency

### 7. Admin Revoke Endpoint
**File:** `backend/app/api/users.py`
- New endpoint: `POST /api/users/residents/{user_id}/revoke-session`
- Requires admin/accounting role
- Only works for resident users
- Increments `session_version` to invalidate all tokens
- Audit log with masked phone number

### 8. Frontend Implementation
**Files:**
- `frontend/src/api/client.js` - Added `revokeResidentSession(id)` method
- `frontend/src/pages/admin/Members.jsx` - Added "Force Logout" button with confirmation modal

## API Reference

### Revoke Session Endpoint
```
POST /api/users/residents/{user_id}/revoke-session
Authorization: Admin or Accounting role required

Response (200):
{
  "success": true,
  "message": "All sessions revoked successfully",
  "message_th": "บังคับออกจากระบบสำเร็จ",
  "user_id": 50,
  "new_session_version": 2
}

Errors:
- 404: User not found
- 400: NOT_RESIDENT - Can only force logout resident users
- 401: Unauthorized
```

## How It Works

1. **Token Creation**: When resident logs in via OTP, their current `session_version` is embedded in the JWT token.

2. **Token Validation**: On every authenticated request, the middleware compares:
   - Token's `session_version` vs Database `user.session_version`
   - If mismatch → 401 SESSION_REVOKED

3. **Session Revocation**: Admin calls revoke endpoint → `session_version` incremented → All existing tokens become invalid.

4. **Re-login**: Resident must request new OTP and login again to get a new token with the updated `session_version`.

## Audit Logging
Session revocation events are logged:
```
[RESIDENT_SESSION_REVOKED] user_id=50 phone=092****222 old_version=1 new_version=2 revoked_by=21
```

## Testing
Run the test flow:
1. Login as resident via OTP
2. Verify `/api/resident/me` works
3. Login as admin
4. Call revoke endpoint for resident
5. Verify resident's token is now rejected with SESSION_REVOKED

## Notes
- No Redis or token blacklist required
- Session revocation is instant (on next API call)
- Multiple devices/sessions are all invalidated simultaneously
- Admin users are not affected (session_version only checked for residents)
