# ผลแก้การจับคู่เงินโอนบ้าน 28/16 และ 28/67

ดำเนินการใน production ตามคำอนุมัติ “ดำเนินการให้สองบ้านนี้ถูกต้องตามรายการจริง” และตรวจผลหลัง commit เมื่อ **9 ตุลาคม 2026 เวลา 15:42:51 น. ไทย** ไม่มีการเปลี่ยนโค้ดแอป/schema/config หรือ deploy

## หลักฐานและข้อผิดพลาด

Statement `Mar26.csv` มีเงินเข้า600บาทสองรายการวันที่2มีนาคม: 10:48 K PLUS เป็นของ28/67ตามสลิปที่แนบPayIn106 (memo28/67Mar2026); 13:41 TTBเป็นของ28/16ตามคำยืนยันownerและผู้โอนเดิมในเดือนก.พ./เม.ย. PayIn106เก็บเวลา13:41และจับคู่Statementผิดแถว ขณะที่แถว10:48ยังUNMATCHED ไม่มีPayIn/ledgerอ้างอิง

PayIn106รับยืนยันตั้งแต่1เมษายน จึงมีข้อผิดพลาดก่อนงานUIเดือนกันยายน ไม่ทราบว่าใครกรอกหรือแก้เวลาเป็น13:41จากหลักฐานที่ตรวจ ไม่ได้กล่าวโทษผู้ยื่นหรือผู้รับยืนยัน

## สิ่งที่แก้จริง

| บ้าน | รายการ | ผล |
|---|---|---|
| 28/67 | PayIn106 / ledger138 | เปลี่ยนเวลาและStatement linkให้ตรง10:48; คงhouse/amount/slipและmetadataผู้ยื่น/การรับเดิม เพิ่มaudit noteและเก็บค่าเดิมในjournal |
| 28/67 | payment199 → invoice384/มีนาคม | คงการชำระ600บาทเดิม วันที่รับเงินแสดง10:48จากledgerที่แก้ |
| 28/16 | PayIn363 / ledger325 | รับเงิน13:41จำนวน600จากStatementตามownerอนุมัติ ใช้ADMIN_CREATED ไม่มีการสร้างหรือคัดลอกสลิปของบ้านอื่น ไม่อ้างผู้ยื่น/ผู้รับเป็นบุคคลใด |
| 28/16 | จัดลำดับFIFOประวัติ | คงpayments30/93/839; เปลี่ยน218/288/292/798/838เป็นREVERSED; เพิ่ม840–845 เก็บแถวเดิมทั้งหมด |

การจัดสรรใหม่ของ28/16:

| Paymentใหม่ | Ledger | บิล | จำนวน |
|---|---|---|---|
| 840 | 325 | 333 มีนาคม | 600 |
| 841 | 152 | 647 เมษายน | 600 |
| 842 | 323 | 804 พฤษภาคม | 600 |
| 843 | 225 | 961 มิถุนายน | 600 |
| 844 | 228 | 1118 กรกฎาคม | 600 |
| 845 | 292 | 1432 กันยายน | 600 |

ผลของบิลที่มีอยู่ม.ค.–ก.ย.: **28/16รับและชำระ4,800→5,400บาท ค้าง600→0**; **28/67รับและชำระ5,400/ค้าง0คงเดิม** เงินเข้าตามStatementไม่เพิ่ม/ไม่เปลี่ยน เพียงรับรู้รายการ10:48ที่ยังไม่ถูกจับคู่และแก้เจ้าของการรับรู้รายการ13:41ให้ถูกต้อง แต่ละbankrowยังเชื่อมreceiptเพียงรายการเดียว

**เดือนตุลาคมยังรอตรวจ:** PayIn354ของ28/67และPayIn362ของ28/16คงPENDING ไม่ได้นับในยอดรับยืนยัน ไม่สร้างใบแจ้งหนี้ตุลาคมเพิ่ม และไม่สรุปว่าทั้งสองบ้านไม่มีภาระในอนาคต

## การสำรองและทดสอบ

เริ่มต้นWindows Application Controlบล็อกpg_dumpเดิม และlocalPostgreSQLเดิมหยุดอยู่ หลังDockerEngineเปิดได้ใช้officialPostgreSQL17ในcontainerแยกบนlocalhost55441 ไม่มีการปิดหรือแก้นโยบายWindows

- ก่อนแก้: 15:39:51ไทย, PostgreSQL custom dump SHA256 `24257b6e0e3060e16a72913d119f529010c42613d2d87cf3707d7c46487f1c46`
- หลังแก้: 15:43:02ไทย, SHA256 `d1eefbf2ba341b7f17af590c50e686fd6dde6be7b4473df0c42306ef72bc6faf`
- ทั้งสองชุดทดลองกู้คืนแยกและเทียบ26ตารางทั้งจำนวนแถว/hashกับsnapshotต้นทางผ่าน; หลังแก้ตรงjournalผลcommitทุกตาราง รวมAlembic revision `p5_1_notifications`
- DB backupไม่รวมbytesR2ทั้งหมด; เก็บสำเนาสลิป106แยก SHA256 `fb63537c6653c69924d1f8545e98277d090ef2305a890d14a8589edc5508d7d7` ไม่แก้R2object
- Snapshotแบบdata-onlyที่ทำก่อนDockerพร้อมเป็นหลักฐานเสริม ไม่ใช่ตัวแทนcustomdumpที่กู้คืนผ่าน

บนสำเนาPostgreSQLจริง: rollbackหลังแก้source/เพิ่มreceiptผ่าน; staleข้อมูลเปลี่ยนปฏิเสธก่อนเขียน; duplicateปฏิเสธ; เพดานเงิน/source18รายการ/rawStatementผ่าน; เปรียบเทียบคู่FIFOกับoracleแยกผ่าน เก็บbefore/prepared/committedjournalsพร้อมhash

ระหว่างเตรียมมีPayIn362เข้ามาเมื่อ15:37 ทำให้attemptV1หยุดที่fingerprintก่อนเขียน ไม่มีproductionjournalหรือfinancialwriteจากattemptนั้น จึงสร้างbaselineV2รวมรายการใหม่และทดสอบใหม่ครบก่อนapply ไม่ข้ามตัวตรวจและไม่ลบรายการผู้ใช้

หลังแก้ตรวจcolumnallowlist: Statement2แถวเปลี่ยนเฉพาะmatch/posting metadata ไม่เปลี่ยนยอด/วันเวลา/raw rows; PayIn106และledger138เปลี่ยนเฉพาะช่องที่อนุมัติ; อีก155บ้านและ21ตารางที่ไม่อยู่ในscopeคงเดิม สมาชิก/เครดิต/สลิปรอตรวจคงเดิม

Actual read-handler verificationบนlocalrehearsalและสำเนาหลังproduction: Admin+residentจริงuser39/38ให้9บิล/9acceptedpayinsต่อบ้านตรงกันทั้งหมด ชำระ5,400/ค้าง0; เวลาMarchตรง13:41/10:48; payment historyเก็บreversal; cash reportม.ค.–ก.ย.600บาททุกเดือนทั้งสองบ้าน รวม18เดือน; pending blockingของ354/362ยังทำงาน การตรวจนี้ไม่ใช่browserหรือHTTPจริง

## หลักฐานและข้อจำกัด

Private root: `C:\Users\sanch\moobaan-db-backups\20261009-transfer-02mar1341`

- `production-BEFORE.private.json`, `production-PREPARED.private.json`, `production-COMMITTED.json`
- `repair-tests-v2.json`, `read-view-v2-test-proof.private.json`, `read-view-v2-final-proof.private.json`
- `preapply-backup-20261009T083950Z`, `final-backup-20261009T084300Z`
- `repair_two_houses_v2.py` SHA256 `2918b57af6f20677b40ed300338b8bd80bcbba68ac606c893bd50ff00e9d283e`

ห้ามรันexecutorที่สำเร็จแล้วซ้ำ ห้ามrestorebackupเก่าทับรายการใหม่ หากต้องแก้เพิ่มให้เทียบข้อมูลสดและใช้journalวางแผนใหม่ ไม่มีการเปลี่ยนกลไกmatchingของแอปในงานนี้ และไม่ได้ตรวจภาพสลิปทุกบ้าน จึงไม่ใช่การรับรองว่าทั้งระบบไม่มีการจับคู่ผิดอื่น เอกสารรอบนี้ยังไม่commit/push
