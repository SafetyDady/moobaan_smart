# 📋 สรุปการอัปเดตระบบ Moobaan Smart

> **อัปเดตล่าสุด:** 14 กุมภาพันธ์ 2569 | **Latest Commit:** `932fe08`

## 🏗️ Stack
| Component | Technology | Host |
|-----------|-----------|------|
| Frontend | React + Vite | Vercel (`moobaan-smart.vercel.app`) |
| Backend | FastAPI + SQLAlchemy | Railway (`moobaansmart-production.up.railway.app`) |
| Database | PostgreSQL | Railway (managed) |
| Object Storage | Cloudflare R2 | `moobaan-smart-production` bucket |
| Auth | JWT Cookie + CSRF + LINE OAuth | — |

---

## 📅 Production Deployment History

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

### 🔒 Session 3 — Security Hardening (11 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 11 | `4f5b7fb` | **SECRET_KEY fail-fast** — Production crash ถ้าใช้ default key | ✅ |
| 11 | `4f5b7fb` | **Prod seed safety guard** — ⚠️ warning ถ้า `RUN_PROD_SEED` ยังตั้งอยู่ | ✅ |
| 11 | `4f5b7fb` | **Startup log** — `[SECURITY] Production mode detected.` | ✅ |
| — | manual | **SECRET_KEY rotated** — เปลี่ยนเป็น 64-byte hex key บน Railway | ✅ |
| — | manual | **ลบ ENV ชั่วคราว** — `RUN_PROD_SEED`, `PROD_RESET_ADMIN_PASSWORD`, `PROD_ADMIN_PASSWORD` | ✅ |

### 📦 Session 4 — Vendor & Category + Reconciliation (12 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 12 | `e5a3eb3` | **Phase H.1.1 Vendor & Category Foundation** — vendor master, expense categories, DB migration | ✅ |
| 13 | `c92bbf7` | แก้ Vendors route ที่ขาดใน App.jsx | ✅ |
| 14 | `f1f12c9` | Staff User Management API | ✅ |
| 15 | `a0785af` | แก้ EmailStr dependency issue | ✅ |
| 16 | `81258eb` | ลบ duplicate Vendors menu ใน sidebar | ✅ |
| 17 | `c832b8c` | **User Management Dashboard** — Staff + Resident CRUD | ✅ |

### 💰 Session 5 — Expense Reconciliation + Hardening (12 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 18 | `6971a86` | **Expense ↔ Bank Allocation Layer** — M:N junction table, 5 API endpoints, หน้า Reconciliation UI | ✅ |
| 19 | `fbe7c5f` | **Allocation Hardening** — row lock (FOR UPDATE), mark-paid guard | ✅ |

### 📎 Session 6 — R2 Storage + Attachments Evidence Layer (12-13 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 20 | `7e237a7` | **R2 Integration Test** — presigned URL smoke test ผ่าน | ✅ |
| 21 | `c24ab03` | **Attachments Evidence Layer** — table, migration (h13), API (presign/list/delete), business rules | ✅ |
| 22 | `cd842f2` | **Expense Attachments UI** — upload Invoice/Receipt to R2, view/delete modal | ✅ |

### 🎨 Session 7 — Village Dashboard + Login Redesign (13-14 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 23 | `003b726` | **LINE Login Loop Fix** — Vercel API proxy แก้ cross-origin cookie | ✅ |
| 24 | `caab412` | **Manus AI UI Merge** — 4 safe UI-only changes (tailwind, icons, cards) | ✅ |
| 25 | `5d1c95a` | **Village Dashboard Redesign** — header card, icon badges, stacked bar chart | ✅ |
| 26 | `062e004` | **Chart Fix** — pixel-based bars, "จาก Statement" title, correct bar order | ✅ |
| 27 | `755500e` | **Expense Breakdown** — category × 3-month comparison mini-bars | ✅ |
| 28 | `9c7a2cd` | **ELECTRICITY / WATER** — split UTILITIES into separate categories | ✅ |
| 29 | `7d082b1` | **Migration Endpoint** — admin-only UTILITIES→ELECTRICITY DB migration | ✅ |
| 30 | `eda726b` | **Semantic Category Colors** — emoji icons + fixed colors per category | ✅ |
| 31 | `05e75f7` | **Login Icon Redesign** — Lucide Home + emerald gradient badge | ✅ |
| 32 | `53b92b5` | **Title → English** — "Moobaan Smart" แทน "หมู่บ้านสมาร์ท" | ✅ |
| 33 | `932fe08` | **LineLogin Match** — LINE connecting screen ให้ตรงกับหน้า login ใหม่ | ✅ |

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
- 🏢 Vendors & Categories — จัดการ vendor master + หมวดหมู่ค่าใช้จ่าย (ELECTRICITY/WATER แยกจาก UTILITIES)
- 👥 User Management — จัดการ Staff + Resident
- 💸 Expense Matching — จับคู่ค่าใช้จ่ายกับรายการธนาคาร (M:N allocation)
- 📎 Expense Attachments — แนบไฟล์ Invoice/Receipt ผ่าน Cloudflare R2

### สำหรับ Resident (ลูกบ้าน)
- 📱 LINE Login — เข้าสู่ระบบผ่าน LINE
- 🏡 เลือกบ้าน (Select House)
- 💳 ส่งหลักฐานการชำระเงิน (Pay-in Submit)
- 📋 ดูประวัติการชำระเงิน
- 📊 Village Dashboard — ยอดเงิน, รายรับ/จ่าย, ลูกหนี้ + chart + expense breakdown
- 🏠 Login Page — Lucide Home icon + gradient badge + "Moobaan Smart"

---

## 🔒 Security Status

| รายการ | สถานะ |
|--------|-------|
| SECRET_KEY — 64-byte hex, rotated | ✅ เสร็จแล้ว |
| SECRET_KEY fail-fast guard (production) | ✅ เสร็จแล้ว |
| Debug endpoints removed | ✅ เสร็จแล้ว |
| ENV ชั่วคราว (`RUN_PROD_SEED` etc.) ลบแล้ว | ✅ เสร็จแล้ว |
| CSRF double-submit cookie (warn mode) | ✅ ใช้งาน |
| Cookie: `httpOnly`, `secure`, `SameSite=None` | ✅ ใช้งาน |

---

## ⚠️ สิ่งที่ควรทำต่อ

| รายการ | ความสำคัญ | สถานะ |
|--------|----------|-------|
| ตั้ง R2_PUBLIC_URL บน Railway | 🟡 กลาง | ❌ ยังไม่ทำ |
| ~~ทดสอบ Resident LINE Login flow จริง~~ | 🟡 กลาง | ✅ เสร็จแล้ว |
| ตั้ง Vercel Git Integration ให้ auto-deploy เมื่อ push | 🟢 ต่ำ | ❌ ยังไม่ทำ |
| เปิด CSRF enforcement (เปลี่ยนจาก warn → block) | 🟢 ต่ำ | ❌ ยังไม่ทำ |

---

## 📝 หมายเหตุ Vercel Deploy

- Vercel **ไม่ได้ auto-deploy** จาก GitHub push (Git Integration อาจยังไม่ได้ตั้ง)
- Deploy ด้วย CLI: `cd moobaan_smart && vercel link --project moobaan-smart && vercel --prod --force`
- หรือไปตั้งค่า Git Integration ที่ [Vercel Dashboard → moobaan-smart → Settings → Git](https://vercel.com/sss-group/moobaan-smart/settings/git)
- Root Directory ใน Vercel ตั้งเป็น `frontend`
- ⚠️ **ห้าม** deploy จาก `frontend/` folder โดยตรง (จะสร้าง project ซ้ำ) — deploy จาก root เท่านั้น
