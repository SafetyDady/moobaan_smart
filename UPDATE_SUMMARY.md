# 📋 สรุปการอัปเดตระบบ Moobaan Smart

> **อัปเดตล่าสุด:** 22 กุมภาพันธ์ 2569 | **Latest Commit:** `2a313b6`

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
| 34 | `cdf7ce2` | **Docs Update** — README, UPDATE_SUMMARY, UI_UX docs | ✅ |

### 📱 Session 8 — Resident Dashboard Overhaul (14 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 35 | `4d91a07` | **Invoice Table View** — เปลี่ยนจาก card → table format, compact hero, ลบ Quick Stats | ✅ |
| 36 | `e5d0143` | **Remove Payment History** — ลบ section ประวัติส่งสลิปออกจาก Dashboard (ย้ายไป `/resident/payments`) | ✅ |

### 🌏 Session 9 — Custom Domain + Admin UI + Pay-in Lifecycle (14-17 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 37 | `ea26934` | docs: update status summary | ✅ |
| 38 | `b05a4d5` | **LINE redirect fix** — trim `VITE_APP_URL` ป้องกัน CRLF ใน redirect_uri | ✅ |
| 39 | `7907167` | **Custom domain support** — ใช้ `VITE_APP_URL` สำหรับ LINE redirect_uri (app.moobaan.app) | ✅ |
| 40 | `58746dc` | **Slip upload UX** — เปลี่ยนจาก camera capture เป็น file picker | ✅ |
| 41 | `c5ad87f` | **Admin sidebar redesign** — grouped sections + Lucide icons, dashboard stat cards | ✅ |
| 42 | `cda0d85` | **Slip → R2** — fix upload to Cloudflare R2 + proper slip viewing | ✅ |
| 43 | `ccfa705` | **Resident delete pay-in** — อนุญาตลบ pay-in ที่ยังไม่ match (PENDING/SUBMITTED) | ✅ |
| 44 | `722bbaa` | **Pay-in duplicate message** — ข้อความ Thai เมื่อส่งสลิปซ้ำ | ✅ |
| 45 | `ca79613` | **Error dismiss UX** — เพิ่มปุ่ม dismiss บน error alert ใน MobileSubmitPayment | ✅ |
| 46 | `d46de83` | **Log noise** — RoleContext ลด console.log → console.debug | ✅ |

### 💰 Session 10 — Pay-in State Machine + Statement-Driven Matching (17-18 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 47 | `57d0a4c` | **Pay-in Lifecycle Contract** — 4 actions only: Delete / Reject / Confirm&Post / Reverse | ✅ |
| 48 | `27e8e6c` | **Phase P1: Statement-Driven Confirm & Post** — match bank txn → accept pay-in | ✅ |
| 49 | `68c042f` | **Cancel fix** — อนุญาต cancel SUBMITTED, clear match before delete | ✅ |

### 🕐 Session 11 — Timezone Hardening & Reconciliation Fix (18-19 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 50 | `cf091bf` | temp: timezone diagnostic endpoint | ✅ |
| 51 | `2e8a337` | **Timezone normalization** — all datetime to UTC, fix pay-in matching | ✅ |
| 52 | `039b654` | chore: run alembic upgrade on deploy | ✅ |
| 53 | `e77eb72` | **transfer_datetime** → return transfer_date directly (UTC) | ✅ |
| 54 | `711a03c` → `1b1b8df` | Audit endpoint for tz migration safety check → fix to use period_snapshots | ✅ |
| 55 | `9877cde` | **assert_utc guards** — runtime guards on datetime, cleanup temp endpoints | ✅ |
| 56 | `fbd95a6` | **Balance formula fix** — ใช้ total_billed ไม่ใช่ outstanding | ✅ |

### 🏗️ Session 12 — Bank Statement Delete + Pay-in Timezone (19-20 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 57 | `10024d0` | **Delete batch FK fix** — handle income_transaction RESTRICT, timezone display Asia/Bangkok | ✅ |
| 58 | `6b7c996` | **Matching diagnostics** — debug info ใน pay-in matching endpoint | ✅ |
| 59 | `7195673` | **Pay-in timezone** — create: strip tz, update: parse date+time correctly | ✅ |

### 🏠 Session 13 — Multi-House Architecture + Phone-First Resident (20-21 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 60 | `d4de1a6` | **House switching** — ปุ่มเปลี่ยนบ้านใน Profile.jsx สำหรับ multi-house residents | ✅ |
| 61 | `3b08d0b` | **Phone-based create_resident** — เช็คเบอร์ก่อน, ถ้ามี User อยู่แล้ว → สร้าง membership เพิ่ม | ✅ |
| 62 | `ee1ddbb` | cleanup: ลบ temp debug endpoints (phone check) | ✅ |

### 📱 Session 14 — Phone-First UI + Identity Hardening (21-22 ก.พ.)

| # | Commit | สิ่งที่ทำ | สถานะ |
|---|--------|----------|-------|
| 63 | `680fe81` | **Phone-First Resident Management** — ทั้งระบบ: | ✅ |
|    |          | • `GET /api/users/residents/search?phone=` — ค้นหา user ด้วยเบอร์ | |
|    |          | • `POST /api/users/residents/{id}/remove-house/{id}` — ถอดลูกบ้านจากบ้าน | |
|    |          | • **AddResident.jsx** rewrite — 2-step UI: ใส่เบอร์ → ดูข้อมูล → เพิ่มบ้าน | |
|    |          | • **Members.jsx** — ปุ่ม "ถอดบ้าน" + confirmation modal | |
|    |          | • **client.js** — searchByPhone + removeFromHouse API | |
| 64 | `639d739` → `0f43558` | **Production data fix** — merge user_id=17 เข้า user_id=6 (duplicate phone 0635162459) → user_id=6 มีบ้าน 28/73 + 28/72 | ✅ |
| 65 | `89f6e14` → `6a0986d` | **Sidebar consolidation** — ย้าย "เพิ่มลูกบ้าน" จาก sidebar → ปุ่ม "+" ใน Members header | ✅ |
| 66 | `05bfb29` | **Phone search ordering** — search + create_resident ใช้ `ORDER BY is_active DESC, line_user_id IS NOT NULL DESC, id ASC` | ✅ |
| 67 | `62bcbd3` | **Link-account ordering** — link-account endpoint ใช้ deterministic ordering + duplicate phone warning log | ✅ |
| 68 | `2a313b6` | **Dashboard house_id fix** — ใช้ JWT `house_id` แทน `HouseMember.first()` สำหรับ multi-house | ✅ |

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
- 👤 **Phone-First Add Resident** — ค้นหาเบอร์ก่อน → ดูข้อมูล user/LINE/บ้าน → assign บ้านเพิ่ม
- 👥 Members — ดูลูกบ้านทั้งหมด + ปุ่ม "ถอดบ้าน" + ปุ่ม "เพิ่มลูกบ้าน" ใน header
- 📊 Dashboard — สรุปภาพรวมหมู่บ้าน
- 💰 Invoice / Pay-in / Ledger — ระบบบัญชี
- 💸 **Statement-Driven Confirm & Post** — match bank txn → accept pay-in → auto ledger
- 📄 Financial Reports — Invoice Aging, Cash Flow
- 🔒 Period Closing — ปิดงวดบัญชี
- 🏢 Vendors & Categories — จัดการ vendor master + หมวดหมู่ค่าใช้จ่าย (ELECTRICITY/WATER แยกจาก UTILITIES)
- 👥 User Management — จัดการ Staff + Resident
- 💸 Expense Matching — จับคู่ค่าใช้จ่ายกับรายการธนาคาร (M:N allocation)
- 📎 Expense Attachments — แนบไฟล์ Invoice/Receipt ผ่าน Cloudflare R2

### สำหรับ Resident (ลูกบ้าน)
- 📱 LINE Login — เข้าสู่ระบบผ่าน LINE (domain: app.moobaan.app)
- 🔗 Link Account — ผูก LINE กับ user ที่ admin สร้างไว้ (phone + house_code)
- 🏡 **Multi-House Support** — เลือกบ้านตอน login + เปลี่ยนบ้านใน Profile
- 💳 ส่งหลักฐานการชำระเงิน (Pay-in Submit) — slip upload → R2
- 📋 ดูประวัติการชำระเงิน (`/resident/payments`)
- 📊 Village Dashboard — ยอดเงิน, รายรับ/จ่าย, ลูกหนี้ + chart + expense breakdown
- 🧾 Resident Dashboard — Compact hero (ยอดค้าง/เกิน) + Invoice Table + **Balance ถูกต้องตามบ้านที่เลือก**
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
| Deprecate `HouseMember` table → ใช้ `ResidentMembership` เท่านั้น | 🔴 สูง | ❌ ยังไม่ทำ |
| ลบ duplicate user (user_id=17, deactivated) ออกจาก DB | 🟡 กลาง | ❌ ยังไม่ทำ (เก็บเป็น audit trail) |
| ตั้ง R2_PUBLIC_URL บน Railway | 🟡 กลาง | ❌ ยังไม่ทำ |
| Token refresh ตรวจสอบ membership ยัง ACTIVE | 🟡 กลาง | ❌ ยังไม่ทำ |
| เปิด CSRF enforcement (เปลี่ยนจาก warn → block) | 🟢 ต่ำ | ❌ ยังไม่ทำ |
| ตั้ง Vercel Git Integration ให้ auto-deploy เมื่อ push | 🟢 ต่ำ | ❌ ยังไม่ทำ |

---

## 📝 หมายเหตุ Vercel Deploy

- Vercel **ไม่ได้ auto-deploy** จาก GitHub push (Git Integration อาจยังไม่ได้ตั้ง)
- Deploy ด้วย CLI: `cd moobaan_smart && vercel link --project moobaan-smart && vercel --prod --force`
- หรือไปตั้งค่า Git Integration ที่ [Vercel Dashboard → moobaan-smart → Settings → Git](https://vercel.com/sss-group/moobaan-smart/settings/git)
- Root Directory ใน Vercel ตั้งเป็น `frontend`
- ⚠️ **ห้าม** deploy จาก `frontend/` folder โดยตรง (จะสร้าง project ซ้ำ) — deploy จาก root เท่านั้น
