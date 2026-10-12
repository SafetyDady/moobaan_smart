# SPEC — PayIn Match Integrity (Phase 1: ปิดช่องโหว่หลักฐานเปลี่ยนหลัง match)

> **สถานะล่าสุด 12 ต.ค. 2026:** Owner อนุมัติแล้ว เผยแพร่ application `5467eef` สำเร็จทั้ง Railway/Vercel และตรวจ DB ไม่เปลี่ยนทั้ง26ตาราง ณ12:39:33น. ดู [รายงาน release](docs/reviews/2026-10-12-payin-integrity-production-release.md). ข้อความรอcommit/อนุมัติด้านล่างเป็นประวัติการมอบงาน 9 ต.ค.

> **ผู้วิเคราะห์/เจ้าของ spec:** Claude Code (เจ้าภาพหลัก) — วิเคราะห์จากโค้ดจริง 2026-10-09
> **ผู้ลงมือ:** Codex | **ผู้รีวิวก่อน push:** Claude Code + owner
> **Local baseline ที่ตรวจจริง:** `598f2bb` (`f367d88` ในบันทึกมอบงานเป็น commit เก่า ไม่ใช่ HEAD) ต้องยืนยัน deployed revision ก่อนกำหนด production rollback
> **ที่มา:** เคสบ้าน 28/67 — สลิประบุ 10:48 แต่ Pay-in กรอก 13:41 → ระบบจับคู่กับ statement 13:41 ยอดเท่ากันแล้วผ่าน (ดูข้อเสนอเต็มใน KNOWLEDGE-LOG 2026-10-09)

---

## ขอบเขต Phase 1
- ✅ โค้ดล้วน backend + frontend — **ไม่มี** DB migration, **ไม่แตะ** FIFO/enum/business rule อื่น
- ❌ ไม่รวมบริการตรวจสลิปภายนอก (EasySlip/SlipOK/OCR) — เป็น Phase 2 รอ owner ยืนยันงบ/แพ็กเกจ
- ❌ ไม่ส่งข้อมูล/สลิปจริงออกนอกระบบ

## ช่องโหว่ที่ยืนยันจากโค้ดจริง (3 จุด)

| # | จุด | ไฟล์:บรรทัด | ปัญหา |
|---|-----|------------|-------|
| 1 | แก้ข้อมูลหลัง match | `backend/app/api/payins.py:457` (`update_payin_report`) | ลูกบ้านแก้ ยอด/วันเวลา/รูปสลิป ตอน PENDING ได้ แต่ไม่เคลียร์ `matched_statement_txn_id` → match ค้างทั้งที่หลักฐานเปลี่ยน |
| 2 | Accept ไม่เทียบซ้ำ | `backend/app/api/payins.py:630` (`accept_payin_report`) | มี row lock + เช็ก link แล้ว (ดี) แต่สร้าง IncomeTransaction ด้วย `payin.amount` โดยไม่เช็กว่ายังเท่า `bank.credit` → match 600 → แก้เป็น 999 → ลงบัญชี 999 ได้ (`confirm_and_post` ไม่มีปัญหานี้ — ใช้ยอดธนาคาร) |
| 3 | Reject ไม่ปล่อย match | `backend/app/api/payins.py:583` + `backend/app/api/payin_state.py:126` | เปลี่ยนสถานะ REJECTED_NEEDS_FIX แต่ bank txn ยังค้าง MATCHED กับรายการที่โดน reject |

## งานที่ต้องทำ

### ขอบเขตเพิ่มเติมตาม owner อนุมัติหลัง Codex review
- ครอบคลุม update/save-draft/attach-slip/submit/reject และ match/unmatch/admin-create พร้อมตรวจทั้ง Accept และ Confirm & Post
- จากการค้นทุก IncomeTransaction constructor พบทางที่สาม AccountingService.accept_payin ผ่าน API accounting ต้องใช้ validator/lock/ยอดStatementเดียวกันด้วย รวม delete endpoints/reversal ให้ร่วมลำดับlockโดยไม่เปลี่ยนFIFO
- ใช้ลำดับ bank row → PayIn row → household gate → ledger IDs → invoice IDs; เมื่ออ่านคู่ก่อน lock แล้วคู่เปลี่ยน ให้ conflict/retry ไม่ขอล็อกย้อนลำดับ; อ่านสถานะใหม่ใต้ lock ทุกครั้ง
- helper ปล่อย match ต้องปฏิเสธ ACCEPTED/POSTED/REVERSED หรือมี active ledger และตรวจคู่สองฝั่ง ไม่ทำ orphan cleanup แบบเดา
- เทียบยอดด้วย Decimal รักษาขอบเขตเดิม ±0.01 และเวลา ±60s; ยอด/เวลาที่ลงบัญชีต้องมาจาก Statement ทั้งสองช่องทาง ไม่ใช้ยอดที่กรอก
- หลักฐานเปลี่ยนจริงเท่านั้นจึง unmatch; normalize timezone ก่อนเทียบ และการแก้เฉพาะชั่วโมง/นาทีต้องอัปเดต timestamp ที่ใช้จับคู่จริง
- เพิ่ม PostgreSQL race tests สำหรับ edit/accept, reject/post, match/edit และ accept/post พร้อมกัน; ห้ามใช้ production DB ในการทดสอบ
- Local เท่านั้น อัปเดต STATUS ทุกช่วงสำคัญ ไม่ commit/push/deploy ต้องขอ owner อนุมัติ deploy หลังส่งผลทดสอบและผ่านรีวิว
- Phase 1 ยังไม่อ่าน/พิสูจน์สลิปจริงอัตโนมัติ และยังไม่ป้องกันเวลาที่กรอกผิดตั้งแต่ก่อนจับคู่ได้ทั้งหมด

### R1 — หลักฐานเปลี่ยน → match หลุด (จุด 1)
ใน `update_payin_report`: ถ้า payin มี `matched_statement_txn_id` และ request แก้ field หลักฐานใด ๆ (`amount`, `transfer_date`, `transfer_hour`, `transfer_minute`, `slip_image_url`) →
1. lock bank txn ด้วย `with_for_update()` (ลำดับ lock เดียวกับ `accept_payin_report` กัน deadlock)
2. เคลียร์ทั้ง 2 ฝั่ง + `posting_status = UNMATCHED` — **ใช้ pattern เดียวกับ endpoint `unmatch`** (`bank_reconciliation.py:149`); แนะนำ extract เป็น helper `release_bank_match(db, payin, bank_txn, reason)` ใช้ร่วม R1/R2
3. `logger.info` ระบุ payin_id, txn_id, field ที่เปลี่ยน, user id
- ค่าที่ส่งมาเท่าค่าเดิม = ไม่ถือว่าเปลี่ยน (เทียบก่อนเคลียร์)
- **ค่าเริ่มต้นที่เลือก:** auto-unmatch (ไม่ block การแก้) — admin จับคู่ใหม่หลังตรวจ (owner เปลี่ยนเป็น "ห้ามแก้จนกว่า unmatch" ได้ก่อนเริ่ม)

### R2 — Reject ปล่อย match (จุด 3)
ทั้ง 2 path ของ reject (`payins.py` reject + `payin_state.py` reject_payin_needs_fix): ถ้ามี match → `release_bank_match(...)` ภายใต้ lock เดียวกัน

### R3 — Accept เทียบหลักฐานซ้ำใต้ lock (จุด 2)
ใน `accept_payin_report` หลัง lock bank txn (โค้ดมีอยู่แล้ว) เพิ่ม:
- `abs(Decimal(bank.credit) - Decimal(payin.amount)) <= Decimal('0.01')`
- `abs((payin.transfer_datetime - bank.effective_at).total_seconds()) <= 60`
- ไม่ผ่าน → 400 `{"code": "EVIDENCE_CHANGED", "message": "หลักฐานไม่ตรงกับรายการธนาคารแล้ว กรุณา unmatch และตรวจใหม่"}` (ไม่ auto-unmatch ในจุดนี้ — ให้ admin เห็นก่อน)

### R4 — หน้า Admin เทียบหลักฐาน (frontend)
ใน modal รีวิว PayIn (`frontend/src/pages/admin/PayIns.jsx`): แสดง 3 คอลัมน์ข้างกัน — **ภาพสลิป | ข้อมูลที่กรอก (ยอด/วันเวลา) | Statement ที่ match (ยอด/เวลา/channel)** + ป้ายเตือนสีเหลือง-แดงเมื่อยอดหรือเวลาต่างกัน
- สลิปผ่าน `payinsAPI.slipUrl(id)` เท่านั้น (ห้ามใช้ `slip_url` ตรง)
- dark theme มาตรฐาน (`.card`, slate-700/800) + ข้อความผ่าน `t()` เพิ่ม key ใน `locales/th.js` ทุกตัว

### R5 — Tests (บังคับ มีครบจึงถือว่าเสร็จ)
1. แก้ amount หลัง match → match หลุด, bank กลับ UNMATCHED
2. แก้เวลา/สลิปหลัง match → เหมือนข้อ 1; แก้ด้วยค่าเดิม → match คงอยู่
3. reject (ทั้ง 2 path) → match หลุด
4. ยอด/เวลา drift แล้วกด Accept → 400 EVIDENCE_CHANGED, ไม่เกิด IncomeTransaction
5. เคสปกติ (match → accept) ยังผ่าน + รัน suite เดิมทั้งหมดต้องเขียว
- รันบน Python 3.11 (Docker `cd docker && docker compose up` หรือ `py -3.11 -m venv`) — **ห้ามใช้ 3.14**

## กติกา (จาก CLAUDE.md — สรุปซ้ำ)
- ห้าม force-push / commit `.env` / แตะ env บน dashboard / เปลี่ยนโครงสร้างโปรเจกต์
- **Codex ทำใน working tree เท่านั้น — ไม่ commit/push เอง** → เสร็จแล้วแจ้ง owner ให้ Claude Code รีวิวก่อน
- จบงานบันทึก `KNOWLEDGE-LOG.md` + อัปเดต `STATUS.md`

## Acceptance Criteria
- [x] R1–R3: ปิดใน working tree พิสูจน์ด้วย Local tests (ยังไม่ deploy)
- [x] R4: หน้ารีวิวเห็นสลิป/ข้อมูล/Statement + เตือนความต่าง, `npm run build` ผ่าน
- [x] ไม่มี migration, FIFO/credit logic เดิมไม่เปลี่ยน, regression Local ที่ระบุด้านล่างผ่าน
- [x] ยังไม่ commit — รอ Auditor รีวิวและ owner อนุมัติ deploy

> **อัปเดต 12 ต.ค. 2026:** Owner อนุมัติ commit/push หลังตรวจผ่านแล้ว คำว่า “ยังไม่ commit/รออนุมัติ” ด้านล่างเป็นสถานะวันที่ 9 ต.ค. ไม่ใช่ข้อห้ามใหม่ ดูผล release ปัจจุบันใน STATUS.md และ docs/reviews/2026-10-12-payin-integrity-production-release.md. ไม่ได้อ้างว่าได้รับผล Auditor รอบใหม่

## ผลส่งตรวจ — 9 ตุลาคม 2026 (Codex)

### ขอบเขตสุดท้าย

- Shared helper: `backend/app/services/payin_integrity.py` ล็อก/อ่านข้อมูลใหม่ ตรวจคู่เชื่อมสองด้าน ยอด Decimal/เวลา และ Statement batch ยืนยันแล้ว ก่อนสร้าง ledger ใช้ยอด/เวลาจากธนาคารเสมอ คง tolerance เดิม ±0.01 บาท / ±60 วินาที
- ครอบคลุม **สามทางสร้าง IncomeTransaction** ที่ค้นพบใน app: `payins.accept_payin_report`, `bank_reconciliation.confirm_and_post`, `AccountingService.accept_payin` ผ่าน API accounting ไม่เหลือ constructor รับเงินที่ใช้ยอด PayIn โดยไม่ตรวจ
- Edit/save-draft/attach-slip/reject ทั้งสองทาง ปล่อย match ใน transaction เดียวกับการแก้; submit/admin-create/delete/reversal ร่วม lock protocol ป้องกันทำแข่งกับรับเงิน; ห้ามปล่อยคู่ ACCEPTED/POSTED/REVERSED หรือมี active ledger กรณีข้อมูลเก่าลิงก์ผิดให้ conflict ไม่เดาซ่อม
- Normalize เวลา: ISO aware รักษา instant, date-only ใช้เวลาเดิม, แก้เฉพาะชั่วโมง/นาทีเปลี่ยน canonical timestamp จริง; ค่าเหมือนเดิมไม่ unmatch
- หน้า Admin ใหม่โหลดหลักฐานล่าสุดก่อน Match/Post และส่ง opaque `evidence_revision` ตรวจใต้ lock ป้องกันใช้หน้าตรวจเก่าหลังเปลี่ยนรูป/ข้อมูลหรือ unmatch/rematch. ไม่เพิ่ม column; token optional เพื่อรองรับ clients เก่า ส่วน guard/lock บังคับทุกทาง
- API detail เพิ่ม Statement แบบย่อสำหรับ Admin/accounting เท่านั้น ไม่มี raw_row/บัญชีอื่นให้ลูกบ้าน หน้าreviewใช้proxyสลิป ข้อมูล/รูปโหลดไม่สำเร็จหรือdriftไม่ให้ยืนยัน รูปไม่มีแสดงคำเตือนสำหรับกระบวนการรับจากStatementเดิม
- ไม่มี migration, dependencies, FIFO algorithm, credit rule หรือ production config changes

### ผลทดสอบ Local

| ชุด | จำนวน | ผล |
|---|---:|---|
| PayIn integrity ใหม่ (รวม 12 blocking races และ HTTP handler checks) | 40 | ผ่าน |
| Credit settlement PostgreSQL | 25 | ผ่าน |
| Automatic allocation PostgreSQL | 24 | ผ่าน |
| Accounting reads PostgreSQL | 8 | ผ่าน |
| R2 ledger eligibility PostgreSQL (ไม่ใช่ Cloudflare upload) | 12 | ผ่าน |
| Invoice access PostgreSQL | 5 | ผ่าน |
| Paid-at / settlement status / Excel-PDF export | 27 | ผ่าน |
| รวม backend | **141** | **ผ่าน** |
| Chrome Local UI scenarios | **11** | **ผ่าน** |
| Frontend production build / diff check | — | ผ่าน |

Race testsใช้สองconnectionจริงและยืนยันการรอผ่านpg_blocking_pids ไม่ใช่เพียงรันเรียงกัน: edit↔accept, reject↔post, accept↔post, match↔edit, post→unmatch, accounting accept↔edit, accounting accept→post. มี rollback injection, stale review, duplicate/idempotency, same values/offset, Statement original fields preserved, active-ledger/reversed guards, ownership/read-access และ FIFO checks

Fixtureเดิมในtest_credit_settlement_postgresเคยสร้างลิงก์ด้านเดียวและbatchPARSED จึงแก้เป็นลิงก์สองด้าน/batchCONFIRMEDให้ตรงnormalworkflow ไม่ลดvalidator. ไม่รันlegacy ad-hoc test scriptsที่ฝังproduction/externalURLs ไม่อ้างว่าทุกไฟล์testในrepoถูกexecute

UIทดสอบหน้า `/admin/payins` จริงผ่านChromeบนLocalVite แต่ตอบAPIด้วยfixtureสังเคราะห์และบล็อกremoteทุกrequest: 1280px/390px, ยอด/เวลาdrift, ไม่มีStatement/สลิป, รูป/ข้อมูลโหลดล้มเหลว, backend400, Match และtimezoneNew_York/Tokyo. HTTPhandler+PostgreSQLทดสอบแยก ไม่อ้างเป็นbrowserต่อDBจริงแบบend-to-end หรือSafari/มือถือจริง

หลักฐาน: `C:\Users\sanch\moobaan-local-tests\payin-integrity-20261009\backend-results.json`, `results.json`, `desktop.png`, `mobile.png`, `tokyo.png` ใช้ข้อมูลสมมติทั้งหมด ภาพถูกดูตรวจด้วยตาแล้ว

### วิธีรันซ้ำสำหรับ Auditor

1. เปิด PostgreSQL17 local ฐานชื่อ `moobaan_credit_test` (containerงานนี้ `moobaan-integrity-local-20261009`, loopback55442; หยุดไว้หลังทดสอบ ใช้ `docker start moobaan-integrity-local-20261009`). ให้ `CREDIT_TEST_DATABASE_URL` ชี้localhostฐานนี้เท่านั้น
2. ที่ backend ใช้ Python3.11: `.venv\Scripts\python.exe -B run_payin_integrity_checks.py --results <local-results.json>` runnerตรวจhost/ชื่อDBและoverrideappDATABASE_URLก่อนimport; ทุกPGsuiteใช้schemaสุ่มที่cleanupเอง ไม่ใช้production.envเพื่อเลือกDB
3. ที่ frontend ตั้ง `VITE_API_BASE_URL=http://127.0.0.1:5176` แล้ว `npm run dev -- --port 5176 --strictPort`
4. ให้NodeหาPlaywrightได้ (ติดตั้งอยู่ในbundledruntime ไม่ต้องเปลี่ยนpackage.json) ตั้ง `NODE_PATH` ไปnode_modulesของruntime และรัน `node tests/payin-evidence-review.cjs` ใช้Chromeที่ติดตั้งอยู่ ภาพ/ผลไปtempหรือ`PAYIN_UI_EVIDENCE_DIR`
5. `npm run build` และ `git diff --check`

### ข้อจำกัดและก่อน release

- Phase1ไม่อ่านความแท้ของภาพ ไม่ตรวจQR/APIและไม่จับสลิปซ้ำจากtransactionreference; เวลาที่กรอกผิดตั้งแต่แรกยังต้องอาศัยAdminตรวจภาพ ผลmatchedไม่ใช่verifiedslip
- การรับเงินจากStatementโดยไม่มีรูปยังรองรับตามflowเดิม ต้องมีหลักฐานระบุบ้าน; ลูกบ้านไม่เลือกบิล และไม่มีการกวาดแก้ประวัติ
- review tokenช่วยหน้าAdminใหม่; clientเก่าที่ไม่ส่งtokenยังใช้freshDBguard/auto-unmatch แต่ไม่สามารถยืนยันได้ว่ามนุษย์เห็นรูปversionไหน
- Audit loggingระบุPayIn/bank/actor/fields/reasonตามspec แต่ไม่ใช่ตารางauditถาวรใหม่; ถ้าtransactionrollback logattemptอาจยังอยู่ อย่าอ้างว่าlogทุกบรรทัดเท่ากับcommitสำเร็จ
- รายการเก่า REVERSED หรือคู่เชื่อมผิดจะถูกหยุดให้ตรวจ ไม่เปิดให้แก้/ปล่อยคู่แล้วรับซ้ำเงียบ ๆ
- Buildมีwarningbundleขนาดใหญ่/Browserslistเก่า และtestsมีStarlettehttpxdeprecated ไม่มีtestfailure; ไม่อัปเกรดdependencyนอกขอบเขต
- **ยังไม่ commit/push/deploy:** ให้Auditorตรวจworking treeรวมไฟล์ใหม่ทั้งหมดก่อน แล้วขอownerอนุมัติrelease. ยืนยันdeployedrevisionจริง+freshbackupที่restoreผ่านก่อนdeploy ห้ามใช้f367d88หรือbackupเก่าย้อนทับproduction
