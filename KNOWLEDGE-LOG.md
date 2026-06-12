# KNOWLEDGE LOG — moobaan_smart

> บันทึกข้อสรุป/ข้อเรียนรู้/ข้อมูลใหม่ เรียงจากใหม่ → เก่า
> รูปแบบ: วันที่ + หัวข้อ + สรุปสั้น + (ถ้ามี) เหตุผล/วิธีนำไปใช้

---

## 2026-06-12

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
