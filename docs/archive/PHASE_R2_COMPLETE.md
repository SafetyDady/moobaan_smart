# Phase R.2: Resident OTP Login (Mock Mode) - COMPLETED ✅

## Summary

Implemented OTP-based authentication for residents using phone numbers. This phase includes:

1. **OTP Service** (`app/services/otp_service.py`) - Mock mode OTP generation and verification
2. **Resident Auth API** (`app/api/resident_auth.py`) - Login endpoints for residents
3. **User Model Updates** - Support phone-only authentication (nullable email/password)
4. **Database Migration** - `r2_user_phone_auth.py`

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/otp_service.py` | OTP generation, verification, rate limiting |
| `backend/app/api/resident_auth.py` | Resident login API endpoints |
| `backend/alembic/versions/r2_user_phone_auth.py` | DB migration for phone-only auth |
| `backend/tests/test_r2_otp_login.py` | Unit & integration tests |

### Modified Files

| File | Changes |
|------|---------|
| `backend/app/main.py` | Register resident_auth router, CSRF exemptions |
| `backend/app/db/models/user.py` | Make email/password nullable, add username |

## API Endpoints

### POST `/api/resident/login/request-otp`

Request OTP for phone number.

**Request:**
```json
{
  "phone": "0812345678"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "ส่ง OTP ไปยังเบอร์โทรศัพท์แล้ว",
  "phone_masked": "081****678",
  "otp_hint": "123456"  // Only in mock mode
}
```

**Response (429 - Rate Limited):**
```json
{
  "detail": "กรุณารอสักครู่ ขอ OTP ได้ไม่เกิน 3 ครั้งต่อนาที"
}
```

### POST `/api/resident/login/verify-otp`

Verify OTP and create session.

**Request:**
```json
{
  "phone": "0812345678",
  "otp": "123456"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "เข้าสู่ระบบสำเร็จ",
  "user_id": 42,
  "phone": "081****678",
  "memberships": [
    {
      "house_id": 1,
      "house_number": "23/45",
      "role": "OWNER",
      "status": "ACTIVE"
    }
  ]
}
```

**Cookies Set:**
- `access_token` (httpOnly)
- `refresh_token` (httpOnly)
- `csrf_token`

**Response (401 - Invalid OTP):**
```json
{
  "detail": "OTP ไม่ถูกต้อง (เหลือ 4 ครั้ง)"
}
```

### GET `/api/resident/me`

Get current resident info and memberships.

**Requires:** Valid `access_token` cookie with `role=resident`

**Response (200):**
```json
{
  "user_id": 42,
  "phone": "081****678",
  "memberships": [...]
}
```

### POST `/api/resident/logout`

Clear session cookies.

**Response (200):**
```json
{
  "success": true,
  "message": "ออกจากระบบสำเร็จ"
}
```

## OTP Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OTP_MODE` | `mock` | Mode: `mock` or `production` |
| `OTP_MOCK_CODE` | `123456` | Fixed OTP code in mock mode |
| `OTP_EXPIRY_SECONDS` | `300` | OTP expiry (5 minutes) |
| `OTP_MAX_ATTEMPTS` | `5` | Max verification attempts |
| `OTP_RATE_LIMIT` | `3` | Max requests per minute |

## Security Guards

### Production Guard ⚠️

```python
# In OTPConfig.validate()
if ENV in ["production", "prod"] and OTP_MODE == "mock":
    raise RuntimeError("❌ Mock OTP not allowed in production!")
```

### Rate Limiting

- Max 3 OTP requests per phone per minute
- Returns 429 HTTP status when exceeded

### Attempt Limiting

- Max 5 verification attempts per OTP
- Record deleted after max attempts reached

### OTP Expiry

- OTP expires after 5 minutes
- Expired records cleaned up on next access

## Database Changes

Migration `r2_user_phone_auth`:

1. `users.email` → nullable (for phone-only residents)
2. `users.hashed_password` → nullable (for OTP-only residents)
3. Added `users.username` column
4. Added unique partial index on `users.phone`

## Test Results

```
tests/test_r2_otp_login.py - 18 passed ✅

TestOTPConfig - 4 tests ✅
TestOTPStore - 10 tests ✅
TestRequestOTP - 2 tests ✅
TestVerifyOTP - 2 tests ✅
```

## Token Structure

Resident token payload:
```json
{
  "sub": "42",        // User ID
  "role": "resident", // Role
  // NO house_id - will be added in Phase R.3
}
```

## What's NOT Included (by design)

Per Phase R.2 requirements:
- ❌ SMS integration (mock only)
- ❌ House selection (Phase R.3)
- ❌ Resident UI (Phase R.4)
- ❌ Password migration
- ❌ Changes to accounting

## Next Steps → Phase R.3

"Step 3 — Select House to Operate"
- Add house_id to token after selection
- `/api/resident/select-house` endpoint
- Multi-house switching

---

**Phase R.2 COMPLETE** ✅  
Ready for Phase R.3 implementation.
