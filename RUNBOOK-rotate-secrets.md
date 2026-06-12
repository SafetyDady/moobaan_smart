# RUNBOOK — Rotate Production Secrets + แก้ config เสี่ยง (moobaan_smart)

> สร้าง 2026-06-12 | เจ้าภาพ: Claude Code | ทำที่เครื่องจริง + Railway/Vercel/Cloudflare/LINE dashboard
> **เหตุ:** คีย์ production ชุดหนึ่งถูกวางในแชต (transcript อาจถูก log) → ถือว่า **หลุด** ต้อง rotate
> หลัก: **ของที่ deploy แล้วห้ามพัง** · rotate ทีละคีย์ · redeploy + เทสต์ก่อนปิดคีย์เก่า · ไม่ force-push · ไม่เก็บค่าลับในไฟล์ใน repo

## ⚠️ สถานะ: คีย์ที่ถือว่าหลุด → ต้อง rotate

| คีย์ | ที่ออกใหม่ | ผลข้างเคียงตอนเปลี่ยน | priority |
|------|-----------|----------------------|----------|
| `SECRET_KEY` (JWT) | `python -c "import secrets; print(secrets.token_hex(32))"` | token แอดมิน/ลูกบ้านเดิมใช้ไม่ได้ → ทุกคน login ใหม่ | 🔴 สูง |
| `R2_ACCESS_KEY_ID` + `R2_SECRET_ACCESS_KEY` | Cloudflare → R2 → Manage API Tokens (สร้าง token ใหม่, ลบเก่า) | ระหว่างสลับ upload/อ่านสลิปอาจสะดุดชั่วครู่ | 🔴 สูง (เข้าถึง bucket การเงิน) |
| `LINE_CHANNEL_SECRET` | LINE Developers Console → channel → Basic settings → Issue | LINE login สะดุดถ้า redeploy ไม่ทัน | 🟠 กลาง |
| `PROD_ADMIN_PASSWORD` | ตั้งใหม่ให้แข็งแรง (ค่าเดิมอ่อนมาก + หลุด) | รหัสแอดมินเปลี่ยน | 🟠 กลาง |

> **ไม่ต้อง rotate:** `DATABASE_URL` (เป็น reference `${{Postgres_moobaan.DATABASE_URL}}` ไม่ใช่ค่าจริงที่หลุด);
> `LINE_CHANNEL_ID`, `R2_BUCKET_NAME`, `R2_ENDPOINT`, URL ต่าง ๆ = identifier สาธารณะ ไม่ใช่ความลับ

### ขั้นตอน rotate (ทำทีละคีย์)
1. ออกคีย์ใหม่ที่ provider (Cloudflare / LINE / gen เอง)
2. อัปเดตค่าใหม่บน **Railway dashboard** (Variables) — **อย่าวางค่าในแชต/commit**
3. redeploy → ทดสอบว่าฟีเจอร์ที่เกี่ยวยังทำงาน (login, อัปโหลดสลิป, LINE, OTP)
4. ปิด/ลบคีย์เก่าที่ provider
5. อัปเดต `.env` local ให้ตรง (เฉพาะที่ใช้ dev) → ถ้าเปลี่ยน รัน `UnionMyAi\scripts\backup-secrets.bat`

---

## 🔴 แก้ config เสี่ยง (พบจากค่าที่ตั้งบน Railway)

1. **OTP — เลิกใช้แล้ว (ค่าใช้จ่าย SMS) → ปิดให้ขาด** *(login ลูกบ้านใช้ LINE OAuth อย่างเดียว)*
   - **ตั้ง `OTP_PROVIDER=disabled`** บน Railway → OTP endpoint จะปิดสะอาด (main.py รองรับ: PROVIDER=="disabled" → log warning, ไม่ crash)
   - **ลบ env ที่ไม่ใช้แล้ว:** `ALLOW_MOCK_OTP_IN_PROD`, `OTP_SANDBOX_WHITELIST`, `OTP_MOCK_CODE`, `OTP_MODE`, `OTP_*` ที่เหลือ, และ `SMSMKT_API_KEY/PROJECT_KEY/SECRET_KEY`
   - **หมายเหตุ severity (แก้ความเข้าใจเดิม):** `ALLOW_MOCK_OTP_IN_PROD=true` **ไม่ใช่** ช่องโหว่เปิดกว้าง — `factory.py` บังคับว่า production+mock ต้องมี `OTP_SANDBOX_WHITELIST` และเฉพาะเบอร์ใน whitelist เท่านั้นที่ผ่าน (เบอร์อื่น 403); ถ้า whitelist ว่าง provider จะ fail-closed (OTP ปิดโดยพฤตินัย). เป็น **flag โหมดทดสอบที่ค้าง** ควรเอาออกเพราะไม่ใช้แล้ว มากกว่าจะเป็นเหตุฉุกเฉิน
   - **โค้ด OTP เก็บไว้ ไม่ลบ** (owner ตัดสินใจ 2026-06-12) — ปิดด้วย env อย่างเดียว เผื่อเปิดใช้ใหม่ในอนาคต
   - แก้บน Railway → redeploy → ทดสอบว่า login LINE ของลูกบ้านยังทำงาน + endpoint OTP ปิดจริง

2. **`PROD_RESET_ADMIN_PASSWORD` = `true` และ `RUN_PROD_SEED` = `true` → ตั้งเป็น `false` หลัง setup เสร็จ**
   - ผล: ทุก deploy จะ reset รหัสแอดมิน / seed ซ้ำ (เสี่ยงทับข้อมูล/รหัสโดยไม่ตั้งใจ)
   - แก้บน Railway หลังยืนยันว่าแอดมิน + seed data มีครบแล้ว

3. **`R2_PUBLIC_URL` vs `R2_PUBLIC_BASE_URL` (ชื่อไม่ตรง)**
   - โค้ดอ่าน **`R2_PUBLIC_URL`** (`core/uploads.py`, `api/attachments.py`, `api/r2_test.py`) แต่ Railway ตั้ง `R2_PUBLIC_BASE_URL` → ค่าปัจจุบันไม่ถูกอ่าน
   - การเข้าสลิปหลักผ่าน backend proxy (`payinsAPI.slipUrl`) จึงยังทำงาน แต่ public URL feature ใช้ไม่ได้
   - แก้: เพิ่ม `R2_PUBLIC_URL` บน Railway (หรือแก้โค้ดให้อ่าน `R2_PUBLIC_BASE_URL`) — ตัดสินใจให้ชื่อตรงกันหนึ่งทาง
   - `R2_ACCOUNT_ID`, `R2_REGION` บน Railway = โค้ดไม่ได้ใช้ (ลบได้ ไม่กระทบ)

---

## หลัง rotate + แก้ config เสร็จ → backup ค่าใหม่
1. Export env vars ชุดใหม่จาก **Railway + Vercel dashboard** → เซฟลงไฟล์ตรง ๆ ใน `OneDrive\03-ProjectSecrets\_exported-env\moobaan_smart\` (**ไม่ผ่านแชต ไม่เข้า git**)
2. รัน `UnionMyAi\scripts\backup-secrets.bat` → `secrets.7z`
3. restore-test (เปิด `.7z` ด้วย 7-Zip ยืนยันอ่านได้)
4. อัปเดต `STATUS.md` + `KNOWLEDGE-LOG.md`

## ✅ Checklist
- [ ] rotate `SECRET_KEY`
- [ ] rotate `R2_ACCESS_KEY_ID` + `R2_SECRET_ACCESS_KEY`
- [ ] rotate `LINE_CHANNEL_SECRET`
- [ ] เปลี่ยน `PROD_ADMIN_PASSWORD` ให้แข็งแรง
- [ ] ปิด OTP ให้ขาด: `OTP_PROVIDER=disabled` + ลบ `ALLOW_MOCK_OTP_IN_PROD`/`OTP_*`/`SMSMKT_*` (เลิกใช้แล้ว)
- [ ] `PROD_RESET_ADMIN_PASSWORD` → false
- [ ] `RUN_PROD_SEED` → false
- [ ] แก้ชื่อ `R2_PUBLIC_URL` ให้ตรงกับโค้ด
- [ ] export env ใหม่ → secrets.7z → restore-test
