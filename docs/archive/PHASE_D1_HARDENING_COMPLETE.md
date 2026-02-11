# Phase D.1 Hardening - OTP + Session Security

**สถานะ**: ✅ เสร็จสมบูรณ์  
**วันที่**: 2026-02-04

---

## 1. Design Decisions สรุป

### Rate Limit State Storage
**เลือก**: In-Memory (Python dict + threading.Lock)

**เหตุผล**:
1. ไม่เพิ่ม dependency ใหม่ (ไม่ใช้ Redis)
2. เหมาะกับ single-instance deployment (Railway)
3. ง่ายต่อการ maintain
4. Trade-off: state จะหายเมื่อ restart (acceptable สำหรับ rate limit)

**หมายเหตุ**: หากอนาคตต้อง scale horizontally ให้ migrate ไป Redis

---

## 2. ไฟล์ที่แก้ไข

### A) OTP Rate Limiting
| ไฟล์ | การเปลี่ยนแปลง |
|------|---------------|
| `app/services/otp_service.py` | เพิ่ม rate limit 3 req/10 min, verify lockout 5 fail/10 min, security logging |
| `app/api/resident_auth.py` | เพิ่ม HTTP 429 response สำหรับ lockout |

### B) Session TTL แยก Role
| ไฟล์ | การเปลี่ยนแปลง |
|------|---------------|
| `app/core/auth.py` | เพิ่ม `get_token_expiry_for_role()`, `get_cookie_max_age_for_role()` |
| `app/api/auth.py` | ใช้ role-based TTL ใน login/refresh |
| `app/api/resident_auth.py` | ใช้ role-based TTL สำหรับ resident |

### C) Environment Guard
| ไฟล์ | การเปลี่ยนแปลง |
|------|---------------|
| `app/services/otp_service.py` | Enhanced warning logging เมื่อ mock OTP ใน production |
| `app/main.py` | Validate OTP config at startup พร้อม log summary |

### D) Health/Readiness
| ไฟล์ | การเปลี่ยนแปลง |
|------|---------------|
| `app/api/health.py` | เพิ่ม `/ready` endpoint พร้อม DB check |

---

## 3. Configuration สรุป

### Session TTL ตาม Role

| Role | Access Token | Refresh Token | Cookie Max-Age |
|------|--------------|---------------|----------------|
| Admin/Accounting | 15 min | 8 hours | 8 hours |
| Resident | 60 min | 7 days | 7 days |

### OTP Rate Limits

| Policy | ค่า Default | ENV Variable |
|--------|-------------|--------------|
| Request OTP limit | 3 ครั้ง / 10 นาที | `OTP_RATE_LIMIT_MAX`, `OTP_RATE_LIMIT_WINDOW` |
| Verify lockout | 5 ผิด → lock 10 นาที | `OTP_VERIFY_LOCKOUT_ATTEMPTS`, `OTP_VERIFY_LOCKOUT_MINUTES` |
| OTP expiry | 5 นาที | `OTP_EXPIRY_SECONDS` |

---

## 4. ENV Variables สำหรับ Railway

```bash
# Required (มีอยู่แล้ว)
ENV=production
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=your-secret-key

# OTP Mock Override (จำเป็นช่วง dev/test)
ALLOW_MOCK_OTP_IN_PROD=true

# Optional: Customize Session TTL
# ADMIN_ACCESS_TOKEN_MINUTES=15
# ADMIN_REFRESH_TOKEN_HOURS=8
# RESIDENT_ACCESS_TOKEN_MINUTES=60
# RESIDENT_REFRESH_TOKEN_DAYS=7

# Optional: Customize OTP Limits
# OTP_RATE_LIMIT_MAX=3
# OTP_RATE_LIMIT_WINDOW=10
# OTP_VERIFY_LOCKOUT_ATTEMPTS=5
# OTP_VERIFY_LOCKOUT_MINUTES=10
```

---

## 5. Acceptance Tests (PowerShell)

### ตั้งค่าตัวแปร
```powershell
$API_BASE = "https://moobaansmart-production.up.railway.app"
# หรือ local: $API_BASE = "http://localhost:8000"
```

### Test 1: Health Check (ต้องยังทำงาน)
```powershell
Invoke-RestMethod -Uri "$API_BASE/health" -Method GET
# Expected: { "status": "ok" }
```

### Test 2: Ready Check (ใหม่)
```powershell
Invoke-RestMethod -Uri "$API_BASE/ready" -Method GET
# Expected: { "status": "ready", "checks": { "database": "ok" } }
```

### Test 3: OTP Request Rate Limit
```powershell
# ขอ OTP 4 ครั้งติดต่อกัน (ครั้งที่ 4 ควร fail)
$phone = "0812345678"
1..4 | ForEach-Object {
    Write-Host "Request $_"
    try {
        $result = Invoke-RestMethod -Uri "$API_BASE/api/resident/login/request-otp" `
            -Method POST `
            -ContentType "application/json" `
            -Body (@{phone=$phone} | ConvertTo-Json)
        Write-Host "Success: $($result.message)"
    } catch {
        Write-Host "Error: $($_.Exception.Response.StatusCode) - $($_.ErrorDetails.Message)"
    }
    Start-Sleep -Seconds 1
}
# Expected: 3 success, 1 fail with HTTP 429
```

### Test 4: OTP Verify Lockout
```powershell
# ขอ OTP ก่อน
$phone = "0899999999"
Invoke-RestMethod -Uri "$API_BASE/api/resident/login/request-otp" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{phone=$phone} | ConvertTo-Json)

# กรอกผิด 6 ครั้ง (ครั้งที่ 6 ควร lock)
1..6 | ForEach-Object {
    Write-Host "Attempt $_"
    try {
        $result = Invoke-RestMethod -Uri "$API_BASE/api/resident/login/verify-otp" `
            -Method POST `
            -ContentType "application/json" `
            -Body (@{phone=$phone; otp="000000"} | ConvertTo-Json)
    } catch {
        Write-Host "Error: $($_.Exception.Response.StatusCode)"
    }
}
# Expected: หลังจาก 5 ครั้ง จะได้ HTTP 429 (locked)
```

### Test 5: Admin Login (Regression)
```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$result = Invoke-WebRequest -Uri "$API_BASE/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{email="admin@village.com"; password="your-password"} | ConvertTo-Json) `
    -WebSession $session

Write-Host "Status: $($result.StatusCode)"
Write-Host "Cookies: $($session.Cookies.GetCookies($API_BASE) | ForEach-Object { $_.Name })"
# Expected: Status 200, Cookies: access_token, refresh_token, csrf_token
```

### Test 6: Resident Login (Mock OTP)
```powershell
$phone = "0812345678"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Request OTP
$otp_result = Invoke-RestMethod -Uri "$API_BASE/api/resident/login/request-otp" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{phone=$phone} | ConvertTo-Json)
Write-Host "OTP Hint: $($otp_result.otp_hint)"

# Verify OTP (ใช้ mock OTP = 123456)
$verify_result = Invoke-WebRequest -Uri "$API_BASE/api/resident/login/verify-otp" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{phone=$phone; otp="123456"} | ConvertTo-Json) `
    -WebSession $session

Write-Host "Status: $($verify_result.StatusCode)"
# Expected: Status 200
```

### Test 7: ตรวจสอบ Token Expiry (JWT Decode)
```powershell
# หลัง login แล้ว decode JWT เพื่อดู exp
$token = $session.Cookies.GetCookies($API_BASE) | Where-Object { $_.Name -eq "access_token" } | Select-Object -ExpandProperty Value
$parts = $token.Split('.')
$payload = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($parts[1] + '=='))
$payload | ConvertFrom-Json | Select-Object exp, role

# สำหรับ Resident: exp ควรห่างจากตอนนี้ประมาณ 60 นาที
# สำหรับ Admin: exp ควรห่างจากตอนนี้ประมาณ 15 นาที
```

---

## 6. Production Go-Live Checklist

เมื่อพร้อม Go-Live และมี SMS Gateway แล้ว:

- [ ] ลบ `ALLOW_MOCK_OTP_IN_PROD=true` ออกจาก Railway ENV
- [ ] ตั้ง `OTP_MODE=production`
- [ ] Configure SMS Gateway credentials
- [ ] ทดสอบ OTP จริงกับเบอร์ทดสอบ
- [ ] Monitor logs สำหรับ OTP_AUDIT events

---

## 7. Security Audit Log Format

ทุก OTP event จะถูก log ในรูปแบบ:
```
[OTP_AUDIT] request_otp: sent | phone=081****678
[OTP_AUDIT] verify_otp: success | phone=081****678
[OTP_AUDIT] verify_otp: rate_limited | phone=081****678 | {'wait_minutes': 8}
[OTP_AUDIT] verify_otp: lockout_triggered | phone=081****678 | {'fail_count': 5, 'locked_minutes': 10}
```

---

## 8. สรุปผลการทดสอบ (Local Test)

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Health check | `{"status":"ok"}` | `{"status":"ok"}` | ✅ Pass |
| Ready check | `{"status":"ready"}` | `{"status":"ready","checks":{"database":"ok"}}` | ✅ Pass |
| OTP rate limit | 429 after 3 req | Request 4 → HTTP 429 | ✅ Pass |
| OTP verify lockout | 429 after 5 fail | Attempt 6 → HTTP 429 | ✅ Pass |
| Admin login | 200 | Status 200 | ✅ Pass |
| Admin session TTL | 8 hours | `TTL=28800s`, csrf expires +8h | ✅ Pass |
| Resident login | 200 | Status 200 | ✅ Pass |
| Resident session TTL | 7 days | access +60min, csrf +7days | ✅ Pass |
| Security logging | Masked phone | `phone=081****111` | ✅ Pass |

---

## 9. Known Limitations

1. **In-memory rate limit**: จะ reset เมื่อ server restart
2. **Single instance**: ไม่เหมาะกับ horizontal scaling (ต้องใช้ Redis)
3. **Mock OTP ยังเปิด**: ต้องปิดก่อน go-live

---

**Created by**: Claude (Phase D.1 Hardening)  
**Scope**: Minimal security hardening without feature expansion
