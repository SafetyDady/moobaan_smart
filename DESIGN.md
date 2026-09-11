# DESIGN — moobaan_smart (แนวคิดและการตัดสินใจด้านดีไซน์)

> บันทึกว่า "ทำไมถึงออกแบบแบบนี้" เพื่อให้ AI และคนเข้าใจเหตุผล ไม่รื้อของที่ตั้งใจไว้
> รายละเอียดสถาปัตยกรรม/conventions ครบอยู่ใน `CLAUDE.md` — ไฟล์นี้เก็บเฉพาะ "เหตุผลเบื้องหลัง"

## ภาพรวมสถาปัตยกรรม
- **2026-09-09 — Automatic allocation (deployed in `43a52b7`):** one shared household FIFO service runs in the receipt-confirmation/invoice-creation transaction. Acquire transaction-scoped household advisory gates before ledger-ID/invoice-ID row locks, including empty households; monthly batches acquire all gates/ledgers/invoices in that order. Receipts sort by received_at/id; bills by due_date/id (manual bills do not jump priority because cycle=0). Existing allocations are retained, and historical correction is separate. Resident has no invoice-selection path. Release activates use of existing unused funds on future triggers; deployment alone runs no sweep. See [release evidence](docs/reviews/2026-09-09-automatic-production-release.md); the subsequently completed historical repairs are listed in STATUS.md.
- **2026-09-09 — R2 owner-approved scope:** invoice picker and locked apply endpoint share eligibility. A no-pay-in ledger needs confirmed posted Statement provenance; null payin_id alone is insufficient. Cash reporting counts POSTED ledger once. This extends existing receipt application, not Case B creation. Historical aging is restated by invoice/receipt/credit-created dates; current Aging uses canonical present debt with a reference aging date. Pending evidence is current/all-period metadata excluded from confirmed totals. Legacy invoice reads now share the selected-house ResidentMembership report guard.
- **2026-09-09 — Report access integration (owner-approved):** scoped `require_report_house_access` reuses authenticated current-user and token-house dependencies, checks current ResidentMembership and house status, and does not infer a selected house. Limited to six accounting report endpoints so report corrections do not rewrite global login policy or revive deprecated screens.
- **2026-09-09 — Read report semantics (owner-approved follow-up):** invoice settlement balances count allocated ACTIVE payments; cash statements count POSTED receipts once, including unallocated money. Applied credits join through invoices. Shared `accounting_reports.py` gives Bangkok opening/period/closing from the same dated records with Decimal math and explicit failure propagation. A historical date range is restated using currently valid records; it is not a frozen period-close snapshot. No financial writers or production evidence are rewritten by this calculation.
- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL (psycopg3) + Alembic (32 routes, 22 models)
- **Frontend:** React 18 + Vite 5 + Tailwind + React Router 7 — dark theme, ไทยเป็นหลักผ่าน `t()`
- **Storage:** Cloudflare R2 (สลิป/ไฟล์แนบ) — เก็บเป็น object key ไม่ใช่ URL ตรง
- **Auth:** JWT (admin/accounting) · LINE OAuth (resident); โค้ด OTP เก็บไว้แต่ owner เลิกใช้ตาม decision log ด้านล่าง ส่วนการปิดค่า env ให้ครบยังอยู่ในรายการต้องยืนยันของ STATUS
- **การไหลของเงิน:** PayIn → จับคู่ bank tx → ACCEPTED → IncomeTransaction → InvoicePayment → ปิด Invoice

## การตัดสินใจสำคัญ (decision log)

| วันที่ | เรื่อง | ตัดสินใจว่า | เหตุผล |
|--------|--------|-------------|--------|
| 2026-09-11 | ตารางใบแจ้งหนี้ลูกบ้าน (owner ยืนยันใช้ได้หลัง deploy) | 5 คอลัมน์พอดีมือถือ ไม่มี minimum 520px; รอบบิล/วันที่แบบสั้น เลื่อนแนวตั้ง หัวตารางตรึง เปิดที่แถวแรก และเรียงรอบบิลล่าสุดก่อน (บิลพิเศษใช้ due_date, เสมอกันใช้ id มากก่อน) | ให้เห็นข้อมูลครบบนมือถือโดยไม่เลื่อนซ้าย–ขวา เป็นกติกาการแสดงผล ไม่เปลี่ยน API/Admin ordering หรือ FIFO การเงิน ดู mobile-fit review |
| 2026-09-09 | การเลือกบิลชำระ (owner ยืนยันเพิ่มเติม) | ลูกบ้านไม่มีสิทธิ์เลือกบิล ระบบต้องกระทบยอดอัตโนมัติตาม FIFO; คงพฤติกรรมนี้เมื่อแก้ปัญหาเงินรับที่ยังไม่ผูก | การซ่อมข้อมูลย้อนหลังหรือการตรวจของ Admin ต้องไม่กลายเป็นขั้นตอนให้ลูกบ้านเลือกบิล และต้องแก้จุดรับเงิน/สร้างบิลที่ปล่อยเงินค้างเพื่อไม่ให้เกิดซ้ำ |
| 2026-09-09 | หลักฐานการรับเงิน (owner ยืนยัน) | Statement ที่ Admin อัปโหลดเป็นหลักฐานอ้างอิงยอดและเวลารับเงินจริง; เดือนที่นำเงินไปชำระบิลเป็นอีกข้อมูลหนึ่ง; สลิปที่รอตรวจสอบยังไม่ใช่ยอดรับยืนยัน | Admin และลูกบ้านต้องเห็นข้อเท็จจริงเดียวกัน ไม่เปลี่ยนวันรับเงินให้ตรงเดือนบิลหรือเรียกเก็บซ้ำโดยไม่ตรวจสลิปที่รออยู่ |
| 2026-09-08 | เพดานลดหนี้ (owner ยืนยันกับ Codex) | ลดได้เฉพาะยอดค้างจริงหลังหักเครดิตเดิมและ ACTIVE payments; ลดเต็ม = ยอดค้าง ไม่ใช่ยอดบิลเต็ม | ป้องกัน paid + credit เกินยอดบิล; บิลพิเศษ 20,000 ยังลด 5,000 ได้เมื่อยอดค้างเพียงพอ |
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
