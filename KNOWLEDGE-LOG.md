# KNOWLEDGE LOG — moobaan_smart

> บันทึกข้อสรุป/ข้อเรียนรู้/ข้อมูลใหม่ เรียงจากใหม่ → เก่า
> รูปแบบ: วันที่ + หัวข้อ + สรุปสั้น + (ถ้ามี) เหตุผล/วิธีนำไปใช้

---

## 2026-07-01

### fix(bank-statements): แปลงหน้าเป็น dark theme + เติม i18n key ที่หาย — `fd4951d` (deployed Vercel)
- **อาการ:** หน้า `/admin/statements` ตัวหนังสือจางมองไม่เห็น + หัวตารางโชว์ key ดิบ `BANKSTATEMENTS.ACCOUNT` / `common.view`
- **สาเหตุ:** เป็นหน้าเดียวในแอปที่ยังใช้การ์ดสีขาว (`bg-white`) แต่หัวข้อ/เซลล์ตารางไม่กำหนดสีตัวอักษร เลยรับสีขาวจาก global theme (`:root color: rgba(255,255,255,0.87)` ใน `index.css`) → ขาวบนขาว มองไม่เห็น; ส่วนแอปที่เหลือใช้ระบบ `.card` (พื้น slate-800) อยู่แล้ว
- **แก้:** [BankStatements.jsx](frontend/src/pages/admin/BankStatements.jsx) แปลงทั้งหน้าเป็น dark theme มาตรฐานแอป (`.card`/`.input`, ตาราง slate-700, ตัวอักษรอ่อน, debit/credit → red-400/green-400) + [th.js](frontend/src/locales/th.js) เติม key `common.view`='ดู', `bankStatements.account`='บัญชี', `bankStatements.period`='งวด' (JSX เรียก key เหล่านี้แต่ไม่มีใน locale — มี `batchAccountCol`/`batchPeriodCol` แต่คนละชื่อ)
- **บทเรียน:** หน้าใหม่ทุกหน้า**ต้องใช้ dark theme** (`.card`, ตัวอักษร `text-white`/`text-gray-300/400`) ตาม CLAUDE.md "Dark theme throughout" — อย่าใช้ `bg-white` + ปล่อยตัวอักษรไม่กำหนดสี (จะรับสีขาวจาก global แล้วหายไปบนพื้นขาว); ถ้าเพิ่ม UI text ใหม่ต้องเติม key ใน `locales/th.js` ทุกครั้ง
- **verify:** `npm run build` ผ่าน (ไม่มี error)

### fix(bank-statements): month validation ต้องเทียบเวลาไทย ไม่ใช่ UTC — `14c6500` (deployed + ยืนยันใช้ได้)
- **อาการ:** อัปโหลด Bank Statement CSV เดือน มิ.ย. → ถูกบล็อก `Transaction #1 (date: 2026-05-31) falls outside selected month 2026-06` + warning `doesn't match CSV date range` ทั้งที่รายการอยู่ในเดือน มิ.ย. จริง
- **สาเหตุ:** `effective_at` เก็บใน DB เป็น **UTC** (ถูกตาม policy) แต่โค้ด validate เดือนเรียก `.date()`/`.month` บนค่า UTC ตรง ๆ โดยไม่แปลงกลับเป็น Asia/Bangkok → รายการหลังเที่ยงคืนไทย (เช่น 01:51 ICT = 18:51 UTC ของวันก่อนหน้า) ถูกตัดสินว่าอยู่คนละเดือน แล้ว reject ผิด
- **ละเมิด policy ตัวเอง:** `timezone.py` ข้อ 3 "All business month boundaries = Asia/Bangkok" — โมดูลอื่น (payins, dashboard, invoices, payin_state) แปลง `.astimezone(BANGKOK_TZ)` ก่อนตัดสินอยู่แล้ว มีแค่ 2 จุดใน bank statement import ที่ลืม
- **แก้ 2 จุด:** [bank_statement_validator.py:95](backend/app/services/bank_statement_validator.py:95) (error ที่บล็อก import) + [bank_statements.py:269](backend/app/api/bank_statements.py:269) (preview warning) → แปลงเป็น Bangkok ก่อนดึง date/month; DB ยังเก็บ UTC เหมือนเดิม ไม่ต้อง migrate batch เก่า
- **เทสต์:** เพิ่ม `backend/test_bank_import_timezone.py` (4 เคส: หลังเที่ยงคืนไทยผ่าน / เดือนผิดจริงยังบล็อก / ปลายเดือนดึกผ่าน / CSV พ.ศ. end-to-end) — ผ่านครบ
- **วิธีนำไปใช้ (ย้ำบทเรียน):** ทุกที่ที่ตัดสิน "อยู่เดือน/วันไหน" ต้อง `.astimezone(BANGKOK_TZ)` ก่อนเสมอ — อย่าเทียบ date/month บน datetime UTC ตรง ๆ
- **rollback point:** ก่อน push = `c8c8020` (ถ้าต้องดึงกลับใช้ `git revert 14c6500` ปลอดภัยกว่า force-push)
- **⚠️ พบระหว่างทาง — venv พัง (เปลี่ยน PC ใหม่):** `backend/.venv` ผูก Python 3.13 (`C:\Python313`) ที่ถูกถอนไป เครื่องใหม่เหลือแค่ 3.14 → venv ย้ายเครื่องไม่ได้ (ฝัง path interpreter เต็ม) จึงพัง ไม่เกี่ยวกับ Docker
  - **production ใช้ Docker/Python 3.11** (`backend/Dockerfile` → `python:3.11-slim`, Railway build ด้วย `railway.json` builder=DOCKERFILE) — คนละชั้นกับ venv ไม่กระทบ
  - **ทางแก้ local (เลือกทางใดทางหนึ่ง):** (1) ใช้ Docker ไปเลย `cd docker && docker compose up` (มี db+backend+frontend, Python 3.11 ตรง prod ที่สุด) หรือ (2) สร้าง venv ใหม่ด้วย **Python 3.11** ให้ตรง prod (`py -3.11 -m venv .venv` + `pip install -r requirements.txt`) — อย่าใช้ 3.14 (ใหม่เกิน dep บางตัวอาจไม่มี wheel + พฤติกรรมต่างจาก prod)

---

## 2026-06-12

### Push docs commit `3342e64` + ยืนยัน production เขียว + พบ URL backend ใน docs ผิด
- push commit docs (context files + .env.example + whitespace) → **Vercel READY + Railway แข็งแรง** (`/health` 200, `/ready` 200 database ok) — production ไม่กระทบ
- **พบ docs ผิด:** CLAUDE.md เขียน backend URL เป็น `moobaan-smart-production.up.railway.app` (มีขีด) แต่ **URL จริงคือ `moobaansmart-production.up.railway.app`** (ไม่มีขีด — ยืนยันจาก JS bundle ของ frontend production) → แก้ใน CLAUDE.md/AGENTS.md แล้ว (รอ push รอบหน้า)
- **health endpoints:** `/health` (liveness), `/ready` (DB check), `/api/system/status` — ไม่ใช่ `/api/health`
- **เครื่องใหม่:** ตั้ง git identity (`SafetyDady <sanchai5651@gmail.com>`) + เคลียร์ `index.lock` ค้าง (lock ตาย 7 ชม. ไม่มี git process)

### ตรวจ env: local ≠ production + คีย์หลุดในแชต + พบ config เสี่ยง
- **local `.env` ไม่ใช่ backup ของ production** — มีแค่ค่า dev: `DATABASE_URL`→local db, `SECRET_KEY`→ค่า dev (ขึ้นต้น `secret` ซึ่ง prod จะ reject), ขาดคีย์ integration ทั้งหมด (R2 5 ตัว, LINE 2, SMSMKT 3, OTP_*, token config). ค่าจริงอยู่บน **Railway dashboard เท่านั้น**
- **🔴 คีย์ production หลุดในแชต (ผู้ใช้วางค่า Railway env ลงแชต) → ต้อง rotate:** `SECRET_KEY`, `R2_ACCESS_KEY_ID`+`R2_SECRET_ACCESS_KEY`, `LINE_CHANNEL_SECRET`, `PROD_ADMIN_PASSWORD` (ค่าเดิมอ่อนมาก). `DATABASE_URL` ปลอดภัย (เป็น reference `${{Postgres_moobaan.DATABASE_URL}}`)
- **OTP เลิกใช้แล้ว (ผู้ใช้แจ้ง 2026-06-12 — มีค่าใช้จ่าย SMS):** login ลูกบ้าน = LINE OAuth อย่างเดียว → ควรปิดให้ขาด `OTP_PROVIDER=disabled` + ลบ `ALLOW_MOCK_OTP_IN_PROD`/`OTP_*`/`SMSMKT_*` บน Railway
  - **แก้ความเข้าใจเดิม:** `ALLOW_MOCK_OTP_IN_PROD=true` **ไม่ใช่** ช่องโหว่เปิดกว้าง — `factory.py` บังคับ production+mock ต้องมี `OTP_SANDBOX_WHITELIST` และเฉพาะเบอร์ใน whitelist เท่านั้นที่ผ่าน; whitelist ว่าง → provider fail-closed (OTP ปิดโดยพฤตินัยอยู่แล้ว). เป็น flag โหมดทดสอบค้าง ไม่ใช่เหตุฉุกเฉิน
  - SMSMKT keys **ไม่ได้หลุด** (ไม่อยู่ในชุดที่วางในแชต) → แค่ลบทิ้งได้ ไม่ต้อง rotate
- **🔴 config เสี่ยงบน Railway (ยังต้องแก้):**
  1. `PROD_RESET_ADMIN_PASSWORD=true` + `RUN_PROD_SEED=true` ค้างไว้ → ทุก deploy reset รหัสแอดมิน/seed ซ้ำ → ต้อง false หลัง setup
  2. **`R2_PUBLIC_URL` (โค้ดอ่าน) ≠ `R2_PUBLIC_BASE_URL` (Railway ตั้ง)** → public URL ไม่ถูกอ่าน (สลิปยังเข้าได้เพราะใช้ backend proxy); `R2_ACCOUNT_ID`/`R2_REGION` โค้ดไม่ใช้
- **ทำแล้ว:** เขียน `RUNBOOK-rotate-secrets.md` (checklist) + อัปเดต `backend/.env.example` ให้ครบทุกคีย์ (ชื่อล้วน ไม่มีค่า)
- **บทเรียน (ย้ำ):** export secret อย่าวางในแชต — เซฟลงไฟล์ตรง ๆ ใน `OneDrive\03-ProjectSecrets`; แอป active = canonical secret อยู่บน dashboard, ต้อง export มาเก็บเข้ารหัสถึงจะนับว่า backup ครบ

### จัด context มาตรฐานให้ตรงเล่มกลาง UnionMyAi
- เพิ่มไฟล์ context มาตรฐานที่ราก repo: `STATUS.md`, `KNOWLEDGE-LOG.md`, `DESIGN.md` + หัวข้อ "🤝 AI Collaboration & Context System" ใน `CLAUDE.md` (กำหนด Claude Code = เจ้าภาพหลัก, read order, กฎเหล็กห้ามทำ prod พัง)
- **เหตุผล:** ให้ AI ตัวอื่นเข้ามาทำงานต่อบนบริบทเดียวกันได้ ตาม `WEB-PROJECT-WORKFLOW.md` ข้อ 1-2 (เหมือนที่ทำกับ sss-corp-erp)
- **วิธีนำไปใช้:** เปิดโปรเจกต์ → อ่าน 4 ไฟล์ตามลำดับ CLAUDE → STATUS → KNOWLEDGE-LOG → DESIGN; งานที่ยังไม่ push/แก้ context บันทึกใน repo นี้ (ไม่ใช่เล่มกลาง)
- **หมายเหตุ:** `AGENTS.md` เป็นสำเนา CLAUDE.md (untracked) → เสี่ยง drift ถ้าแก้ตัวเดียว ควร sync หรือยุบรวม

### บทเรียนจาก payins (สรุปจาก commit ล่าสุด)
- **ค่า amount ที่เป็น NaN/Inf** ทำให้ endpoint list/get และ submit พังได้ → ต้อง guard ทั้ง 2 ฝั่ง (defense in depth: `3ddb825` + `49afdaa`)
- **ปุ่มลบ invoice** เคยเพิ่ม (`659e583`) แล้ว revert (`b89d940`) เพราะเสี่ยงข้อมูลหาย → **อย่าเพิ่มปุ่มลบ invoice กลับโดยไม่มี safeguard**
- **สลิป:** `slip_url` ใน DB เป็น R2 object key ไม่ใช่ URL ตรง → ต้องใช้ proxy `payinsAPI.slipUrl(id)` เสมอ (`2d1a51f` แก้ viewer ให้ใช้ endpoint ที่ auth)
