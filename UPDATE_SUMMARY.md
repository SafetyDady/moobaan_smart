# 📋 สรุปการอัปเดตระบบ Moobaan Smart

## 🏗️ Stack
| Component | Technology | Host |
|-----------|-----------|------|
| Frontend | React + Vite | Vercel (`moobaan-smart.vercel.app`) |
| Backend | FastAPI + SQLAlchemy | Railway (`moobaansmart-production.up.railway.app`) |
| Database | PostgreSQL | Railway (managed) |
| Auth | JWT Cookie + CSRF + LINE OAuth | — |

---

## 📅 Production Deployment (10-11 ก.พ. 2569)

### 🔐 Session 1 — Deploy & Fix Login (10 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 1 | `7e124e0` | แก้ Frontend ให้ใช้ `VITE_API_BASE_URL` เรียก API ไปที่ Railway | ✅ |
| 2 | `a0b3f61` | OTP validation ไม่บังคับ — app boot ได้แม้ไม่มี OTP config | ✅ |
| 3 | `4957578` | LINE OAuth: สร้าง random state parameter (LINE API บังคับ) | ✅ |
| 4 | `d1ed115` | LINE OAuth: ใช้ `VITE_APP_URL` สำหรับ redirect_uri ที่คงที่ | ✅ |
| 5 | `33c5a6e` | **Login Landing Page ใหม่** — 2 ปุ่ม: LINE Login (ลูกบ้าน) / Admin Login (modal) | ✅ |
| 6 | `520ae1f` | เพิ่ม `PROD_RESET_ADMIN_PASSWORD` option ใน prod_seed | ✅ |
| 7 | `2028d07` | แก้ admin email จาก `admin@yourcompany.com` → `admin@moobaan.com` | ✅ |
| 8 | `a66a9eb` | ลบ debug endpoints ออก (security) | ✅ |

### 🏠 Session 2 — Import Data & Fix Edit (11 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 9 | `ecf7cbb` | **Import 157 บ้าน** จาก HomeList.xlsx เข้า Production DB | ✅ |
| 10 | `67e7553` | **แก้ House Edit** — เพิ่ม Edit Modal + แก้ Backend Enum conversion | ✅ |

---

## 🔑 Credentials

| รายการ | ค่า |
|--------|-----|
| Admin Email | `admin@moobaan.com` |
| Admin Password | `Admin123!` |
| LINE Channel ID | `2007133150` |

---

## ✅ ฟีเจอร์ที่ใช้งานได้แล้ว

### สำหรับ Admin (`/admin/*`)
- 🔑 Admin Login ผ่าน Email/Password (modal)
- 🏠 Houses Management — ดู / เพิ่ม / **แก้ไข** / ลบ บ้าน (157 หลัง)
- 👤 Add Resident — เพิ่มลูกบ้านและผูกกับบ้าน
- 📊 Dashboard — สรุปภาพรวมหมู่บ้าน
- 💰 Invoice / Pay-in / Ledger — ระบบบัญชี
- 📄 Financial Reports — Invoice Aging, Cash Flow
- 🔒 Period Closing — ปิดงวดบัญชี

### สำหรับ Resident (ลูกบ้าน)
- 📱 LINE Login — เข้าสู่ระบบผ่าน LINE
- 🏡 เลือกบ้าน (Select House)
- 💳 ส่งหลักฐานการชำระเงิน (Pay-in Submit)
- 📋 ดูประวัติการชำระเงิน

---

## ⚠️ สิ่งที่ควรทำต่อ (Security)

| รายการ | ความสำคัญ | สถานะ |
|--------|----------|-------|
| เปลี่ยน `SECRET_KEY` บน Railway จาก default เป็น random string | 🔴 สูง | ❌ ยังไม่ทำ |
| ลบ ENV: `RUN_PROD_SEED`, `PROD_RESET_ADMIN_PASSWORD`, `PROD_ADMIN_PASSWORD` | 🟡 กลาง | ❌ ยังไม่ทำ |
| ทดสอบ Resident LINE Login flow จริง (admin ผูก line_user_id → resident ใช้ LINE) | 🟡 กลาง | ❌ ยังไม่ทำ |
| ตั้ง Vercel Git Integration ให้ auto-deploy เมื่อ push | 🟢 ต่ำ | ❌ ยังไม่ทำ |

---

## 📝 หมายเหตุ Vercel Deploy

- Vercel **ไม่ได้ auto-deploy** จาก GitHub push (Git Integration อาจยังไม่ได้ตั้ง)
- ต้อง deploy ด้วย CLI: `cd frontend && vercel link --project moobaan-smart && vercel --prod`
- หรือไปตั้งค่า Git Integration ที่ [Vercel Dashboard → moobaan-smart → Settings → Git](https://vercel.com/sss-group/moobaan-smart/settings/git)
- Root Directory ใน Vercel ตั้งเป็น `frontend`
