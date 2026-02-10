# Phase D.3: SMSMKT OTP Provider + Production-safe Mock Whitelist

## Summary

เพิ่ม OTP Provider abstraction รองรับทั้ง Mock และ SMSMKT พร้อม Sandbox Whitelist สำหรับทดสอบใน Production

## Features

### 1. OTP Provider Abstraction

- **Mock Provider**: Fixed OTP code (default: 123456) สำหรับ dev/test
- **SMSMKT Provider**: Production OTP via SMSMKT.com API

### 2. Production-safe Mock Whitelist (Sandbox Mode)

ใน Production environment สามารถใช้ Mock OTP ได้ แต่ต้อง:
- Set `ALLOW_MOCK_OTP_IN_PROD=true`
- Set `OTP_SANDBOX_WHITELIST=081xxx,082xxx,083xxx` (comma-separated phone numbers)

**Security Behavior:**
- Phone ที่อยู่ใน whitelist → ใช้ Mock OTP ได้ (123456)
- Phone ที่ไม่อยู่ใน whitelist → HTTP 403 Forbidden

### 3. SMSMKT API Integration

SMSMKT.com Official API:
- **Send OTP**: `POST https://portal-otp.smsmkt.com/api/otp-send`
- **Validate OTP**: `POST https://portal-otp.smsmkt.com/api/otp-validate`

---

## Environment Variables

### Required for SMSMKT (Production)

```env
# Provider selection
OTP_PROVIDER=smsmkt

# SMSMKT credentials
SMSMKT_API_KEY=your_api_key
SMSMKT_SECRET_KEY=your_secret_key
SMSMKT_PROJECT_KEY=your_project_key
```

### Optional: Mock in Production (Sandbox Mode)

```env
# Enable mock OTP in production for specific phones
ALLOW_MOCK_OTP_IN_PROD=true
OTP_SANDBOX_WHITELIST=0812345678,0823456789,0834567890
```

### Rate Limiting (defaults shown)

```env
OTP_RATE_LIMIT_MAX=3            # Max requests per window
OTP_RATE_LIMIT_WINDOW=10        # Window in minutes
OTP_VERIFY_LOCKOUT_ATTEMPTS=5   # Wrong attempts before lockout
OTP_VERIFY_LOCKOUT_MINUTES=10   # Lockout duration
OTP_EXPIRY_SECONDS=300          # OTP expiry (5 minutes)
OTP_MAX_ATTEMPTS=5              # Max verify attempts per OTP
```

---

## Phone Normalization

Thai phone numbers are normalized to 10-digit format starting with `0`:

| Input | Normalized |
|-------|-----------|
| `+66812345678` | `0812345678` |
| `66812345678` | `0812345678` |
| `0812345678` | `0812345678` |
| `081-234-5678` | `0812345678` |

Valid prefixes: `06`, `08`, `09`

---

## HTTP Error Codes

| Code | Condition |
|------|-----------|
| 200 | OTP sent successfully |
| 401 | Wrong OTP code |
| 403 | Phone not in sandbox whitelist |
| 429 | Rate limited or verify lockout |

---

## Files Changed/Added

### New Files

```
backend/app/services/
├── phone_utils.py                    # Thai phone normalization
└── otp_providers/
    ├── __init__.py                   # Package exports
    ├── base.py                       # OTPProvider ABC
    ├── mock_provider.py              # Mock implementation
    ├── smsmkt_provider.py            # SMSMKT API implementation
    └── factory.py                    # Provider factory + guards
```

### Modified Files

```
backend/app/services/otp_service.py   # Integrated provider abstraction
backend/app/api/resident_auth.py      # Added 403 error handling
```

---

## Switch from Mock to SMSMKT

### Step 1: Get SMSMKT Credentials

1. Register at https://portal-otp.smsmkt.com
2. Create a project and get credentials

### Step 2: Set Railway Environment Variables

```bash
railway variables set OTP_PROVIDER=smsmkt
railway variables set SMSMKT_API_KEY=your_api_key
railway variables set SMSMKT_SECRET_KEY=your_secret_key
railway variables set SMSMKT_PROJECT_KEY=your_project_key
```

### Step 3: Remove Mock Override (if set)

```bash
railway variables delete ALLOW_MOCK_OTP_IN_PROD
railway variables delete OTP_SANDBOX_WHITELIST
```

### Step 4: Redeploy

```bash
railway up
```

---

## Testing

### Test Mock Mode (Local)

```bash
# Set environment
export OTP_PROVIDER=mock

# Request OTP
curl -X POST http://localhost:8000/api/v1/resident/login/request-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "0812345678"}'

# Response includes otp_hint: "123456"
```

### Test Sandbox Mode (Production)

```bash
# Set environment (Railway)
OTP_PROVIDER=mock
ALLOW_MOCK_OTP_IN_PROD=true
OTP_SANDBOX_WHITELIST=0812345678

# Whitelisted phone → 200 OK
curl -X POST https://your-api.up.railway.app/api/v1/resident/login/request-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "0812345678"}'

# Non-whitelisted phone → 403 Forbidden
curl -X POST https://your-api.up.railway.app/api/v1/resident/login/request-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "0899999999"}'
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     resident_auth.py                         │
│                    /login/request-otp                        │
│                    /login/verify-otp                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     otp_service.py                           │
│  - request_otp() → check whitelist → send via provider       │
│  - verify_otp()  → check whitelist → validate via provider   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  otp_providers/factory.py                    │
│  get_otp_provider() → returns singleton provider instance    │
│  - Local dev: Mock                                           │
│  - Prod + SMSMKT: SMSMKTProvider                             │
│  - Prod + Mock + Whitelist: Mock (sandbox mode)              │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐
│   MockOTPProvider     │   │   SMSMKTProvider      │
│   - Fixed code        │   │   - HTTP API calls    │
│   - In-memory storage │   │   - portal-otp.smsmkt │
└───────────────────────┘   └───────────────────────┘
```

---

## Security Notes

1. **Never expose SMSMKT credentials** in client-side code or logs
2. **Sandbox whitelist** should only contain test phones
3. **Remove ALLOW_MOCK_OTP_IN_PROD** before full production launch
4. **Rate limiting** protects against abuse (3 req/10 min, 5 wrong = 10 min lock)

---

## Next Steps

- [ ] Register SMSMKT account and get credentials
- [ ] Set Railway env vars for SMSMKT
- [ ] Test with whitelisted sandbox phones
- [ ] Remove mock override for full production

---

**Phase D.3 Complete** ✅
