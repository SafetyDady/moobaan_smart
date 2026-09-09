# ผล deploy R1/R2 — 9 กันยายน 2026

เจ้าของอนุมัติชุดสุดท้ายแล้ว จึง commit/push `67e7a57eee1f8053b8d269e66f1a1d46b25580f9` ขึ้น master และตรวจหลัง deploy จนถึงประมาณ10:41น.ไทย โค้ดตรงกับ approved tree `73a8745ead07921439beeca850800211ee16f6aa` ทั้ง40ไฟล์

## Deployment

| ระบบ | ผล |
|---|---|
| Railway | SUCCESS; active deployment `8769c9df-ae9e-4c3b-9122-ee915e02b1b0`, exact release commit |
| Vercel | SUCCESS; deployment `RKqmvMUH39tnVki7HEJppLrwL32G`, GitHub status on exact release commit |
| Backend health / ready | HTTP200 ทั้งคู่ |
| Frontend | `moobaan-smart.vercel.app` และ `app.moobaan.app` serve JS เดียวกัน |

JS SHA256 production `d33b31020a26665e9851a4522829db4817916ad9eba957b13622b0203add8dbf` ตรงกับ build ที่ทดสอบหลังแทนเฉพาะ URL local→production และ normalize CRLF ของ string ที่ฝังใน source Windows ไม่ได้อ้างว่า artifact local กับCIมีbyte/hashเดียวกัน

## Backup และความครบถ้วนของข้อมูล

- Backupก่อนpush **10:31:18น.ไทย** ใช้ exported read-only snapshot เดียวกับ source fingerprints; pg_dump custom format แล้ว restore ลงDBlocalใหม่สำเร็จ
- ทุก **26public tables** จำนวนแถวและhashตรงกัน; SHA256dump `34852a2efcd59d27766fdbca99cf51e9e8626dd683bd518f9ae0a661d7068105`; Alembic `p5_1_notifications`
- หลังdeployใช้production REPEATABLE READ READ ONLY snapshotเทียบกับbackupก่อนpush: **ไม่มีpublic tableใดเปลี่ยน** จึงไม่พบการเปลี่ยนข้อมูลจากstartup/deployในช่วงที่ตรวจ
- เก็บprivateที่ `C:\Users\sanch\moobaan-db-backups\20260909-2895\pre-release-20260909T033118Z` นอกGit/OneDrive มีไฟล์connectionแยกที่จำกัดสิทธิ์ ไม่เผยsecretในรายงาน
- DBdumpรวมข้อมูล/อ้างอิงไฟล์ แต่ **ไม่รวมR2 object bytesของสลิป/เอกสารแนบ** และไม่ใช่backupPGroles/ACL
- RUN_PROD_SEED=false และ PROD_RESET_ADMIN_PASSWORD=false ตรวจยืนยันก่อนpush ปิดไว้ต่อไป

## ผลตรวจหลัง deploy

- Anonymous GETทั้ง6accounting read aliases และlegacy house-invoices routeถูกปฏิเสธ401 ไม่มีการเปิดรายงานโดยไม่เข้าสู่ระบบ
- หน้าAdmin invoicesโหลดข้อมูลจริง1256รายการรายเดือนและปุ่มexportกลับพร้อมใช้งานหลังโหลด ตรวจแบบอ่านอย่างเดียว ไม่ได้กดชำระ/ลดหนี้/ส่งออกที่เขียนaudit
- Sessionลูกบ้านที่มีอยู่แล้วบนcustomdomainเปิดใหม่ได้ บ้าน28/73แสดงบิลมกราคม–สิงหาคม2026จำนวน8ใบ ใบละ600 ยอดค้าง4,800บาท ตรงกับlive SQLแบบread-only
- ไม่ได้ทดสอบLINE OAuthเริ่มloginใหม่ ไม่ได้เปลี่ยนบ้านในsession และไม่ได้ทดสอบธุรกรรมเงินจริงผ่านหน้าจอ
- ก่อนdeployผ่าน72regressions (รวม13PGblockingraces) และ2,532finalreport/access/download checksบนbackupที่restore ครอบคลุม157บ้าน ไม่อ้างว่าตัวเลขนี้เป็นจำนวนproductionHTTP checks

## สิ่งที่ยังแยกไว้

Releaseนี้แก้การแสดง/คำนวณรายงานและการควบคุมสิทธิ์/การรับชำระตามR1/R2 ไม่มีmigrationหรือdata-repair และ **ไม่ได้ย้ายallocation28/95หรือ62บ้าน** รายการรับเงินจริงเดือนพฤษภาคมของ28/95ยังอยู่ หลักฐานStatement/เวลา/ยอดเดิมไม่ถูกแก้ รายงานรับเงินกับยอดที่ผูกเข้าบิลต้องอ่านแยกความหมาย

การปรับallocationย้อนหลังต้องมีรายการก่อน/หลังและreviewเป็นงานแยก ข้อสรุปนี้ยืนยันเฉพาะขอบเขตที่ตรวจ ไม่ใช่คำรับประกันว่าทุกflowในระบบไม่มีความเสี่ยง

## Rollback

ฐานโค้ด `f367d8832c266ad9c9010bd1fb04a1b0fcafcab6`; หากจำเป็นให้revert release commitแล้วdeploy หรือredeployartifactฐานเดิมตามขั้นตอนตรวจ ห้ามrestoreDBเก่าทับธุรกรรมใหม่ และห้ามเปิดseed/resetกลับเป็นtrue

หลักฐานprivate: `approved-release-state.private.json`, `release-deployment-latest.private.json`, `pre-release-current.json`, `postdeploy-smoke.private.json`, `postdeploy-browser-check.private.json` ที่backup root ส่วนcommitถัดจากreleaseซึ่งบันทึกรายงานนี้เป็นเอกสารเท่านั้น ไม่มีapplication changes
