# STATUS — moobaan_smart (อ่านก่อนเริ่ม | สำหรับ Claude + AI ตัวอื่น)

**อัปเดตล่าสุด:** 2026-07-01
**สถานะรวม:** 🟢 active deployed (Vercel `moobaan-smart` / Railway backend) — อยู่ใน maintenance + เพิ่ม feature ย่อย
**หลักนำทาง:** ของที่ deploy แล้ว **ห้ามพัง** · owner รีวิว + deploy เอง อย่า push/commit โดยไม่ถาม

## กำลังทำอยู่
- ไม่มีงานค้างระหว่างทำ — งานล่าสุด (fix timezone bank statement) deploy + ยืนยันใช้ได้แล้ว

## ทำเสร็จแล้ว (ล่าสุด → เก่า)
- `fd4951d` fix(bank-statements): แปลงหน้า `/admin/statements` เป็น dark theme (เดิมตัวหนังสือขาวบนขาว มองไม่เห็น) + เติม i18n key ที่หาย `common.view`/`bankStatements.account`/`period` (2026-07-01, deployed Vercel)
- `14c6500` fix(bank-statements): validate month boundary เป็น Asia/Bangkok ไม่ใช่ UTC — แก้บั๊ก import CSV เดือน มิ.ย. ถูก reject ผิด + เพิ่ม regression test (2026-07-01, deployed + ยืนยันใช้ได้)
- จัด context มาตรฐาน 4 ไฟล์ครบ (2026-06-12)
- `bc2313c` docs: เพิ่ม MIGRATION.md + migrate-bundle.ps1 สำหรับย้ายเครื่อง
- `49afdaa` / `3ddb825` fix(payins): กัน NaN/Inf ในค่า amount ทั้งตอน submit และตอน list/get
- `b89d940` revert ปุ่มลบ invoice (กันข้อมูลหาย) หลังเพิ่งเพิ่มใน `659e583`
- `7db5890` feat: เลือกปี/เดือนตอน generate invoice รายเดือนได้

## 🔴 ด่วน — ความปลอดภัย (ดู `RUNBOOK-rotate-secrets.md`)
- [ ] **Rotate คีย์ production ที่หลุดในแชต (2026-06-12):** `SECRET_KEY`, `R2_ACCESS_KEY_ID`+`R2_SECRET_ACCESS_KEY`, `LINE_CHANNEL_SECRET`, `PROD_ADMIN_PASSWORD`
- [ ] **ปิด OTP ให้ขาด (เลิกใช้แล้ว — ค่าใช้จ่าย SMS):** `OTP_PROVIDER=disabled` + ลบ `ALLOW_MOCK_OTP_IN_PROD`/`OTP_*`/`SMSMKT_*` บน Railway (login ลูกบ้าน = LINE OAuth อย่างเดียว)
- [ ] **แก้ config เสี่ยงบน Railway:** `PROD_RESET_ADMIN_PASSWORD`→false, `RUN_PROD_SEED`→false
- [ ] **แก้ชื่อ R2:** โค้ดอ่าน `R2_PUBLIC_URL` แต่ Railway ตั้ง `R2_PUBLIC_BASE_URL` (ไม่ตรง) → ตั้งให้ตรงกัน
- [ ] หลัง rotate: export env ใหม่จาก dashboard → `secrets.7z` → restore-test

## ค้างอยู่ / ขั้นถัดไป
- [ ] **venv พัง (เปลี่ยน PC ใหม่):** `backend/.venv` ผูก Python 3.13 ที่ถูกถอน เหลือแค่ 3.14 (venv ย้ายเครื่องไม่ได้) → รัน backend/เทสต์ในเครื่องไม่ได้ ทางแก้: ใช้ Docker `cd docker && docker compose up` **หรือ** สร้าง venv ใหม่ด้วย **Python 3.11** ให้ตรง production (`py -3.11 -m venv .venv` + `pip install -r requirements.txt`) — prod ใช้ Docker/py3.11 อย่าใช้ 3.14
- [ ] **whitespace ค้างใน working tree:** `backend/app/core/config.py` (ลบ trailing space 1 บรรทัด) — commit รวมกับงานถัดไป หรือ `git checkout` ทิ้งก็ได้
- [ ] **AGENTS.md (untracked):** ตอนนี้เป็นสำเนา CLAUDE.md → ตัดสินใจ commit เป็นสำเนา หรือยุบเหลือไฟล์เดียวกัน drift
- [x] **อัปเดต `backend/.env.example`** ให้มีครบทุกคีย์ที่โค้ดใช้ (R2/LINE/OTP/SMS/token/bootstrap — ชื่อล้วน) ✅ 2026-06-12
- [ ] **moobaan_smart ยังไม่ได้ export env จาก dashboard** (ต่างจาก sss-corp-erp ที่ทำแล้ว) — local `.env` เป็นค่า dev ไม่ใช่ค่า production → ทำตอน rotate

## ปัญหา/บล็อกที่ค้าง
- ไม่มีบล็อกที่ทำให้ทำงานต่อไม่ได้ — branch `master` sync กับ `origin/master`

## บริบทอ้างอิง
- GitHub: `SafetyDady/moobaan_smart` · Deploy: Vercel `moobaan-smart` (`app.moobaan.app`)
- รายละเอียดสถาปัตยกรรม: `CLAUDE.md` · การตัดสินใจดีไซน์: `DESIGN.md` · บทเรียน: `KNOWLEDGE-LOG.md`
