# STATUS — moobaan_smart (อ่านก่อนเริ่ม | สำหรับ Claude + AI ตัวอื่น)

**อัปเดตล่าสุด:** 2026-09-11
**สถานะรวม:** 🟢 active deployed (Vercel `moobaan-smart` / Railway backend) — อยู่ใน maintenance + เพิ่ม feature ย่อย
**หลักนำทาง:** ของที่ deploy แล้ว **ห้ามพัง** · owner รีวิว + deploy เอง อย่า push/commit โดยไม่ถาม

## สถานะปัจจุบัน — ตรวจหลักฐาน 11 ก.ย. 2026

- **งานตารางใบแจ้งหนี้ลูกบ้านปิดแล้ว:** เจ้าของยืนยัน “OK ใช้ได้แล้ว” หลัง deploy งาน `dbad6bb`; commit เอกสาร `637838a` เป็น baseline ก่อนเผยแพร่การจัด context รอบนี้; รุ่นโค้ดแอปยังคง `dbad6bb`
- **จุดตรวจ production หลังเผยแพร่ UI เวลา 13:06 น.:** `637838ac414a78a9901c6ff3af63cb721952fa99`, Railway `4990adbb-05d4-4568-8970-01c026720825` และ Vercel `8wTv44xGV9UwBKmJ2T322bozDQp3` SUCCESS; ผลตรวจหลัง deploy ล่าสุด 13:06 น. ไทย ไม่ใช่การ query production ใหม่ในรอบจัด context
- ตารางลูกบ้านครบ 5 คอลัมน์บนจอจำลอง 320–768px, ไม่ต้องเลื่อนซ้าย–ขวา, เลื่อนลงได้, หัวตารางตรึง และเปิดที่แถวบนสุด เรียงรอบบิลล่าสุดก่อน; บิลพิเศษใช้ due_date และเสมอกันใช้ id มากก่อน
- สถานะ: ISSUED = ค้างชำระ (slate), PARTIALLY_PAID = ชำระบางส่วน (amber), CREDITED = ลดหนี้แล้ว (sky), PAID = ชำระแล้ว (emerald) ชำระล่าสุดใช้ paid_at จากเวลารับเงินของรายการที่นำมาชำระบิล แสดงเวลาไทย ไม่ใช้ applied_at
- การเรียงหน้าลูกบ้านเป็นการแสดงผลเท่านั้น; API/Admin มีลำดับเริ่มต้นรอบบิลเก่าก่อน ส่วน FIFO การเงินยังรับเงินตาม received_at/id → บิลตาม due_date/id ลูกบ้านไม่เลือกบิล
- ทดสอบ 47 browser checks + 7 native input checks และเปิดหน้า/โหลดใหม่/empty-to-loaded ผ่าน; build ผ่าน เจ้าของยืนยันใช้งานได้ แต่ไม่ได้ระบุเครื่องหรือ browser จึงไม่อ้างว่าทดสอบ Safari/โทรศัพท์ทุกรุ่น
- ผล 13:06: public assets รุ่นใหม่ทั้งสองโดเมน, health/ready 200, anonymous invoice GET 15 รายการตอบ 401; DB 26 ตารางจำนวนแถว/hash ไม่เปลี่ยนจาก backup ก่อน push
- Backup ของ release UI เวลา 13:02 น. ที่ตรวจคืน: `resident-fit-release-20260911T060213Z` เวลา 13:02 น. ไทย, SHA256 `78fede79292fa9be393c8497c3476331fffd5d99171fd99a9a740a0a8b9b5e04`; กู้คืนสำเนา 26 ตารางผ่าน รวม DB/object keys แต่ไม่รวม bytes รูป R2 จุดย้อนกลับ code ของรอบนี้ `2c5922e` ไม่ใช่คำสั่ง restore DB
- การจัด context ผ่าน Auditor และเจ้าของอนุมัติ commit/push แล้ว: รวมเอกสาร 8 ไฟล์พร้อมประวัติ STATUS เดิมครบใน docs/context ไม่มีงาน UI หรือแก้ข้อมูลการเงินที่อนุมัติแล้วค้างอยู่; commit เอกสารนี้ไม่เปลี่ยน application code

รายละเอียด UI: [mobile-fit review](docs/reviews/2026-09-11-resident-invoice-mobile-fit.md)

## งานกระทบยอดที่ปิดแล้ว — ผล ณ เวลาตรวจ ไม่ใช่ยอดสด

- ระบบกระทบยอดอัตโนมัติ deploy แล้วตั้งแต่ 9 ก.ย. (`43a52b7`); การ deploy เองไม่รันกวาดแก้ประวัติ ดู [automatic release](docs/reviews/2026-09-09-automatic-production-release.md)
- Pilot 28/95 และ staged reconciliation 63 บ้าน/14 batches เสร็จแล้ว ยอดที่นำเงินรับเดิมมาชำระเพิ่ม 153,000.24 บาท รายงานรวมรายบ้านตรวจผลต่างตรงกัน; ไม่ใช่เงินเข้าธนาคารใหม่
- 28/30 ปิดการจัดลำดับประวัติแล้ว: ณ 11 ก.ย. 00:32 น. เงินรับ 6,000.30 / ชำระ 5,397.60 / ค้าง 0 / เงินเหลือ 602.70 ดู [รายงาน](docs/reviews/2026-09-11-house2830-reconciliation-result.md)
- 28/56 ปิดประวัติแล้ว และเจ้าของยืนยัน PayIn288 ภายหลัง: ตรวจ 11:01 น. ACCEPTED → ledger291 → payment750 ชำระบิลพฤษภาคม 600 บาท; ค้าง 1,800 (มิ.ย.–ส.ค.) เงินเหลือ 0 ไม่มีสลิปรอตรวจของบ้านนี้ ณ เวลานั้น ดู [รายงาน](docs/reviews/2026-09-11-house2856-reconciliation-result.md)
- Census 157 บ้าน ณ 00:40 น. ผ่านการตรวจลำดับ/เงินเหลือร่วมกับหนี้/ความครบถ้วนหลักฐาน; ไม่ได้สแกนใหม่ทั้งระบบในรอบ context นี้ และไม่ได้หมายความว่าทุกบ้านปลอดหนี้หรือสลิปทั้งหมดผ่านตรวจ
- ห้ามรัน executor/batch ที่เสร็จแล้วซ้ำ และห้าม restore backup เก่าทับรายการใหม่ หลักฐาน Statement และสมาชิกที่แก้ภายหลังต้องคงอยู่

## ประวัติการเตรียมงาน

การเผยแพร่เอกสารรอบจัด context: baseline/rollback `637838a`; สำรอง DB แบบอ่านอย่างเดียว 11 ก.ย. 13:28 น. ไทยที่ `context-docs-release-20260911T062827Z`, SHA256 `bbc6fb734f47bd36231c2079fb5894def573c3438b96ed6bca754a6316b0ff69` และกู้คืนแยกตรวจครบ 26 ตารางผ่าน ผลเผยแพร่ของ commit เอกสารให้ตรวจจาก Git/deployment; ผล 13:06 ด้านบนเป็นหลักฐานของ release UI ที่เสร็จแล้ว

บันทึก “กำลังทำ/ยังไม่ push/รอ deploy” เดิมย้ายไป [ประวัติ STATUS](docs/context/2026-09-11-status-history-before-consolidation.md) โดยเก็บข้อความครบ ใช้สำหรับตามรอยเท่านั้น ห้ามนำสถานะเก่ากลับมาเป็นงานค้าง; KNOWLEDGE-LOG และรายงานที่มีวันที่เป็นบันทึกเหตุการณ์ตามเวลา

## ทำเสร็จแล้ว (ล่าสุด → เก่า)
- `6eacde6` feat(reports): export ใบแจ้งหนี้ตรงหน้าจอ — Excel 11 คอลัมน์ (+ชำระแล้ว/เครดิต/ค้างชำระ/วันครบกำหนด/วันที่ชำระล่าสุด), สถานะไทยจาก canonical, `issue_date` แทน `created_at`, เงินเป็นเซลล์ตัวเลข, เวลาไทย, ปุ่มส่ง filter ปัจจุบัน, PDF ย่อ 8 คอลัมน์ + 8 tests (2026-09-08, deployed + ยืนยันใช้ได้)
- `abbcaa7` fix(invoices): canonical settlement status ที่เดียวใช้ทุกที่ — แก้ "จ่ายครบโชว์เครดิตแล้ว"/"ลดหนี้บางส่วนโชว์ชำระบางส่วน", filter CREDITED ไม่ยิง enum, รวม Decimal เป็น single source, UI เลิกคำนวณเอง + 12 tests (2026-09-08, deployed)
- `44fc26f` fix(credits): ลดหนี้ได้ไม่เกินยอดค้างจริง + serialize credit/payment/FIFO/bank reversal ด้วย row lock, Decimal money, PG suite 20 เคส (2026-09-08, deployed)
- `b645e0e` feat(invoices): เพิ่มคอลัมน์ "วันที่ชำระล่าสุด" (ใช้ `received_at` เวลารับเงินจริง ไม่ใช่ `applied_at`) + payment history แยกเวลารับเงิน/บันทึกเข้าบิล ทุก timestamp เป็นเวลาไทย + eager load กัน N+1 + unit test 7 เคส (2026-09-08, deployed + ยืนยันใช้ได้)
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
- [x] **แก้ config เสี่ยงบน Railway:** `PROD_RESET_ADMIN_PASSWORD=false`, `RUN_PROD_SEED=false` — ตรวจล่าสุดก่อน push mobile-fit 2026-09-11: ทั้งคู่ false; คงค่า false ระหว่าง rollback.
- [ ] **แก้ชื่อ R2:** โค้ดอ่าน `R2_PUBLIC_URL` แต่ Railway ตั้ง `R2_PUBLIC_BASE_URL` (ไม่ตรง) → ตั้งให้ตรงกัน
- [ ] หลัง rotate: export env ใหม่จาก dashboard → `secrets.7z` → restore-test

## ค้างอยู่ / ต้องยืนยันแยกจากงาน UI

- รายการความปลอดภัยที่ยังไม่ติ๊กด้านบนคงไว้ เพราะรอบนี้ไม่ได้ตรวจ dashboard/secrets จึงยังยืนยันว่าปิดแล้วไม่ได้
- [ ] Export production env หลัง rotate และ restore-test ของ secrets archive ตามแผนเดิม; ไม่พิมพ์ค่า secret ลง context
- รายการเก่าที่ปิดจากหลักฐาน local ในรอบนี้: venv ใช้งานได้ Python 3.11.9/import SQLAlchemy+psycopg ผ่าน, `AGENTS.md` tracked และตรง `CLAUDE.md`, ไม่มี diff ค้างใน `backend/app/core/config.py`
- ไม่มีบล็อกใหม่ของงาน UI; การแก้ context รอบนี้เป็นเอกสารเท่านั้น; push จะกระตุ้น auto-deploy ตามปกติ แต่ไม่มีการแก้ application code/config/DB

## บริบทอ้างอิง
- GitHub: `SafetyDady/moobaan_smart` · Deploy: Vercel `moobaan-smart` (`app.moobaan.app`)
- รายละเอียดสถาปัตยกรรม: `CLAUDE.md` · การตัดสินใจดีไซน์: `DESIGN.md` · บทเรียน: `KNOWLEDGE-LOG.md`
