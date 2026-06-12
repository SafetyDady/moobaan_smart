# STATUS — moobaan_smart (อ่านก่อนเริ่ม | สำหรับ Claude + AI ตัวอื่น)

**อัปเดตล่าสุด:** 2026-06-12
**สถานะรวม:** 🟢 active deployed (Vercel `moobaan-smart` / Railway backend) — อยู่ใน maintenance + เพิ่ม feature ย่อย
**หลักนำทาง:** ของที่ deploy แล้ว **ห้ามพัง** · owner รีวิว + deploy เอง อย่า push/commit โดยไม่ถาม

## กำลังทำอยู่
- จัด context ให้ตรงมาตรฐานเล่มกลาง UnionMyAi (เพิ่ม STATUS / KNOWLEDGE-LOG / DESIGN + หัวข้อ AI Collaboration ใน CLAUDE.md) — **เสร็จรอบนี้**

## ทำเสร็จแล้ว (ล่าสุด → เก่า)
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
- [ ] **whitespace ค้างใน working tree:** `backend/app/core/config.py` (ลบ trailing space 1 บรรทัด) — commit รวมกับงานถัดไป หรือ `git checkout` ทิ้งก็ได้
- [ ] **AGENTS.md (untracked):** ตอนนี้เป็นสำเนา CLAUDE.md → ตัดสินใจ commit เป็นสำเนา หรือยุบเหลือไฟล์เดียวกัน drift
- [x] **อัปเดต `backend/.env.example`** ให้มีครบทุกคีย์ที่โค้ดใช้ (R2/LINE/OTP/SMS/token/bootstrap — ชื่อล้วน) ✅ 2026-06-12
- [ ] **moobaan_smart ยังไม่ได้ export env จาก dashboard** (ต่างจาก sss-corp-erp ที่ทำแล้ว) — local `.env` เป็นค่า dev ไม่ใช่ค่า production → ทำตอน rotate

## ปัญหา/บล็อกที่ค้าง
- ไม่มีบล็อกที่ทำให้ทำงานต่อไม่ได้ — branch `master` sync กับ `origin/master`

## บริบทอ้างอิง
- GitHub: `SafetyDady/moobaan_smart` · Deploy: Vercel `moobaan-smart` (`app.moobaan.app`)
- รายละเอียดสถาปัตยกรรม: `CLAUDE.md` · การตัดสินใจดีไซน์: `DESIGN.md` · บทเรียน: `KNOWLEDGE-LOG.md`
