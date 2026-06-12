# DESIGN — moobaan_smart (แนวคิดและการตัดสินใจด้านดีไซน์)

> บันทึกว่า "ทำไมถึงออกแบบแบบนี้" เพื่อให้ AI และคนเข้าใจเหตุผล ไม่รื้อของที่ตั้งใจไว้
> รายละเอียดสถาปัตยกรรม/conventions ครบอยู่ใน `CLAUDE.md` — ไฟล์นี้เก็บเฉพาะ "เหตุผลเบื้องหลัง"

## ภาพรวมสถาปัตยกรรม
- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL (psycopg3) + Alembic (32 routes, 22 models)
- **Frontend:** React 18 + Vite 5 + Tailwind + React Router 7 — dark theme, ไทยเป็นหลักผ่าน `t()`
- **Storage:** Cloudflare R2 (สลิป/ไฟล์แนบ) — เก็บเป็น object key ไม่ใช่ URL ตรง
- **Auth:** JWT (admin/accounting) · OTP + LINE OAuth (resident)
- **การไหลของเงิน:** PayIn → จับคู่ bank tx → ACCEPTED → IncomeTransaction → InvoicePayment → ปิด Invoice

## การตัดสินใจสำคัญ (decision log)

| วันที่ | เรื่อง | ตัดสินใจว่า | เหตุผล |
|--------|--------|-------------|--------|
| 2026-06-12 | ปุ่มลบ invoice | **ไม่มี** ปุ่มลบ invoice | revert ออกเพราะเสี่ยงข้อมูลการเงินหายถาวร — ต้องมี safeguard ก่อนถึงจะพิจารณาใหม่ |
| 2026-06-12 | OTP login ลูกบ้าน | **เลิกใช้** (ค่าใช้จ่าย SMS) — ปิดด้วย `OTP_PROVIDER=disabled` แต่**เก็บโค้ดไว้ ไม่ลบ** | login = LINE OAuth อย่างเดียว; เก็บโค้ดเผื่อเปิดใช้ใหม่ — อย่าเสนอลบซ้ำจนกว่า owner สั่ง |
| — | สลิป R2 | proxy ผ่าน backend (`payinsAPI.slipUrl(id)`) เสมอ | `slip_url` เป็น object key + ต้องผ่าน auth ไม่เปิด public |
| — | PayIn → ledger | เฉพาะสถานะ **ACCEPTED** เท่านั้นที่สร้าง IncomeTransaction | กันเงินเข้าบัญชีก่อนยืนยันการจับคู่ bank tx |
| — | Bank matching | จับคู่ 1:1 ด้วย amount (±0.01) + time (±60s) | ลด false match จากยอด/เวลาใกล้กัน |
| — | Resident UI | mobile-only, house-bound | ลูกบ้านใช้มือถือเป็นหลัก, จำกัดสิทธิ์ที่บ้านตัวเอง |
| — | Village info | hardcoded ใน `MobileDashboard.jsx` | หมู่บ้านเดียว ไม่ต้องมี config หลังบ้าน (KBANK 040-1-56500-0) |

## สิ่งที่พิจารณาแล้วไม่เลือก (และทำไม)
- **ใช้ `slip_url` เป็น img src ตรง** → ไม่เลือก เพราะเป็น object key + ต้อง auth
- **interpolation params ใน `t()`** → ไม่มี รองรับแค่ key + fallback (ออกแบบให้เรียบง่าย)
- **ปุ่มลบ invoice แบบไม่มี safeguard** → ตัดออก (ดู decision log)
