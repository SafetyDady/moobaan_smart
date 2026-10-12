# STATUS — moobaan_smart (อ่านก่อนเริ่ม | สำหรับ Claude + AI ตัวอื่น)

**อัปเดตล่าสุด:** 2026-10-12
**สถานะรวม:** 🟢 active deployed (Vercel `moobaan-smart` / Railway backend) — อยู่ใน maintenance + เพิ่ม feature ย่อย
**หลักนำทาง:** ของที่ deploy แล้ว **ห้ามพัง** · owner รีวิว + deploy เอง อย่า push/commit โดยไม่ถาม

## งานปัจจุบัน — PayIn Match Integrity Phase 1: preflight ผ่าน กำลังเผยแพร่ตาม owner อนุมัติ

- **12 ต.ค. 2026:** Owner อนุมัติให้ตรวจแล้ว push หากไม่มีข้อบล็อก จึงดำเนินการ release ตามคำอนุมัติล่าสุด ไม่ได้อ้างว่ามีผล Auditor รอบใหม่ ทดสอบซ้ำ backend141 + Chrome11 + build ผ่าน หลักฐาน `C:\Users\sanch\moobaan-local-tests\payin-integrity-20261012`. ใช้ container แยก `moobaan-integrity-release-20261012` พอร์ต55443 เพราะพอร์ต55442มีงานอื่นใช้อยู่
- **Preflight ผ่าน 12:35 น. ไทย:** Railway SUCCESS ที่ `598f2bb` ตรง origin/master, seed/reset flags=false, health/ready/frontend200. DB backup `payin-integrity-release-20261012T053519Z` SHA256 `92822dbf82e594fbea45986f6e2d4b9bd85bd455480b9c1fe7cfb029d7ed01a8` ทดลองกู้คืน Local และเทียบ26ตารางจำนวนแถว/hashครบ ไม่มี production write/migration; backupมีobject keysแต่ไม่รวมbytesรูปR2. รายละเอียด [release report](docs/reviews/2026-10-12-payin-integrity-production-release.md)

### ผล implementation วันที่ 9 ต.ค. (ประวัติก่อนอนุมัติ release)

- **9 ต.ค. 2026:** ลงมือครบตาม owner อนุมัติ ตรวจรายละเอียด/คำสั่งทดสอบใน [PAYIN_MATCH_INTEGRITY_SPEC.md](PAYIN_MATCH_INTEGRITY_SPEC.md) ส่วนผลส่งตรวจท้ายไฟล์ ยังไม่ commit/push/deploy และไม่เชื่อมต่อหรือเขียน production ในรอบ implementation นี้
- ปิดหลักฐานเปลี่ยนแล้ว match ค้าง, reject ไม่ปล่อย match และยอดรับผิดจาก PayIn ครบทั้ง **3 ทางรับเงิน**: PayIn Accept, Confirm & Post, AccountingService/API accept. ใช้ Decimal + ยอด/เวลาจาก Statement และล็อกข้อมูลลำดับเดียวกัน ครอบคลุม save-draft/attach-slip/submit/admin-create/delete/reversal ด้วย ไม่มี migration หรือแก้ FIFO/credit logic
- Admin เปิดดูสลิป/ข้อมูลกรอก/Statement พร้อมกันก่อน Match/Post; โหลดข้อมูลใหม่และส่ง review token ตรวจซ้ำใต้ lock กันใช้หน้าตรวจเก่า token optional สำหรับ API clients เดิม แต่หน้า Admin ใหม่ส่งทุกครั้ง รูปโหลดไม่สำเร็จ/ข้อมูล drift บล็อกยืนยัน
- **ผล Local รอบสุดท้าย:** backend **141 tests ผ่าน** (PostgreSQL114 + unit/export27; integrityใหม่40 รวม12 blocking races); browser **11 scenarios ผ่าน** บนChrome ขนาด1280/390 เวลาเครื่องNew_York/Tokyo ด้วยAPI/สลิปสังเคราะห์และบล็อกremote requests; frontend build ผ่าน; git diff --check ผ่านหลังเก็บ whitespace
- PostgreSQL17 เฉพาะงาน `moobaan-integrity-local-20261009`, loopback55442, DB `moobaan_credit_test`, schemaสุ่มและล้างเฉพาะschemaทดสอบ. หลักฐานlocal `C:\Users\sanch\moobaan-local-tests\payin-integrity-20261009` (backend-results.json, results.json, desktop/mobile/tokyo.png). Browserเป็นmockAPI; HTTP handler testsใช้LocalDBจริง ไม่อ้างว่า browser ต่อDBจริง end-to-end หรือทดสอบSafari/มือถือจริง
- **Local baseline 598f2bb**; f367d88 ในเอกสารมอบงานเดิมเป็นcommitเก่า ได้แก้specแล้ว ก่อนreleaseต้องตรวจdeployedrevisionและfreshbackup/restoreอีกครั้ง ไม่มีการนำbackupเก่ามาทับรายการใหม่
- **ขั้นถัดไปตามอนุมัติ 12 ต.ค.:** ปิด preflight/backup → commit/push → ตรวจ deployment และอ่านเทียบข้อมูลหลังเผยแพร่. Phase2 EasySlip/SlipOK/OCRยังไม่อนุมัติ ไม่สมัคร/ส่งสลิปภายนอก ยังไม่อ่านความแท้ของรูปเองอัตโนมัติหรือกวาดแก้ประวัติ
- ปิดLocalVite5176และหยุดเฉพาะcontainerทดสอบของงานนี้หลังจบ เก็บcontainer/หลักฐานไว้ รันทดสอบซ้ำเริ่มด้วย `docker start moobaan-integrity-local-20261009` ไม่ได้หยุดDockerทั้งหมดหรือแตะบริการอื่น

## ผลแก้ล่าสุด — 9 ต.ค. 2026 เวลา 15:42–15:43 ไทย

- **ปิดการแก้บ้าน28/16และ28/67ในproductionแล้ว ตาม owner อนุมัติ:** เงิน600วันที่2มี.ค.10:48/KPLUSเป็น28/67; เงิน600เวลา13:41/TTBเป็น28/16. สลิป106เดิมระบุ28/67/10:48แต่PayInเก็บ13:41และจับคู่ผิด; แก้PayIn106และledger138ให้ตรงStatement10:48 เก็บยอด/บ้าน/สลิป/ประวัติรับเดิมไว้และเพิ่มaudit note พร้อมjournalก่อน–หลัง
- บ้าน28/16รับยอด13:41ผ่านPayInใหม่**363**/ledger**325** (ADMIN_CREATEDจากStatementตามคำยืนยันowner ไม่มีสลิปปลอมหรืออ้างผู้ยื่น/ผู้รับยืนยันรายบุคคล). จัดFIFOย้อนหลัง: เก็บpayments30/93/839; เปลี่ยน218/288/292/798/838เป็นREVERSED ไม่ลบ; เพิ่ม840–845. ม.ค.–ก.ย.รับและชำระ4,800→5,400บาท ค้าง600→0; 28/67รับและชำระ5,400/ค้าง0คงเดิม มีนาคมแสดง10:48
- **สลิปเดือนต.ค.ยังรอตรวจ:** PayIn354ของ28/67 และPayIn362ของ28/16 คงPENDING ไม่ได้นับเป็นยอดรับยืนยันหรือสร้างบิลต.ค.เพิ่ม. ระหว่างเตรียมมี362เข้ามา ตัวตรวจstaleหยุดattemptแรกก่อนเขียน; ทดสอบใหม่บนbaselineที่รวม362ก่อนapplyจริง
- ทดสอบบนPostgreSQL17แยกในDockerผ่าน: rollbackหลังแก้source/เพิ่มreceipt, stale, duplicate, เพดานยอด, source18รายการตรงrawStatement, independentFIFOoracle, ขอบเขตrows/columns และอีก155บ้านไม่เปลี่ยน. หลังcommitตรวจ26ตารางตรงjournal และbackupหลังแก้กู้คืนครบ26ตารางตรงผลcommit
- Actual read-handler checks บนสำเนาที่กู้คืนหลังproductionผ่าน: Admin+residentจริงuser39/38ได้ข้อมูลตรงกัน9บิล/9acceptedpayinsต่อบ้านและรายงานรับเงิน18เดือนรวมสองบ้าน; ไม่ได้ทดสอบผ่านbrowser/HTTPจริงรอบนี้. หลักฐานยอดเงิน/วันที่/rawStatementและสลิปต้นฉบับไม่เปลี่ยน; เปลี่ยนเฉพาะการเชื่อมbank2แถว, PayIn106+ใหม่363, ledger138+ใหม่325, allocation/invoiceที่ระบุ อีก21ตารางไม่เปลี่ยน
- Backupก่อนแก้15:39:51 SHA256 `24257b6e0e3060e16a72913d119f529010c42613d2d87cf3707d7c46487f1c46`; หลังแก้15:43:02 SHA256 `d1eefbf2ba341b7f17af590c50e686fd6dde6be7b4473df0c42306ef72bc6faf`. PostgreSQL custom dumps/restoreผ่าน รวมDBแต่ไม่รวมR2ทั้งหมด; สลิป106เก็บสำเนา+hashแยก. หลักฐานprivate `C:\Users\sanch\moobaan-db-backups\20261009-transfer-02mar1341`
- อุปสรรคเริ่มต้นpg_dumpWindowsถูกApplicationControlบล็อกและlocalPGเดิมหยุด **คลี่คลายด้วยDocker Engineที่เปิดได้และofficialPostgreSQL17container** ไม่เปลี่ยนนโยบายWindows. Snapshotdata-onlyก่อนหน้าไม่ใช่verifiedbackup; ใช้preapply/finaldumpที่กู้คืนผ่านข้างบนแทน
- รายงาน [ผลแก้สองบ้าน](docs/reviews/2026-10-09-house2816-house2867-statement-correction.md). ห้ามรันexecutorซ้ำ/restorebackupเก่าทับข้อมูลใหม่. ไม่มีapp/schema/config change หรือdeploy; contextรอบนี้ยังไม่commit/push. ปิดเฉพาะincidentสองบ้าน ไม่ใช่การรับรองสลิปทุกบ้านหรือแก้กลไกป้องกันจับคู่ผิดทั้งระบบ

## สถานะ release UI — ตรวจหลักฐาน 11 ก.ย. 2026 (ประวัติ)

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
