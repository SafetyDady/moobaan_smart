# ชุด release สุดท้าย — รออนุมัติ commit/push

หลังเจ้าของให้ดำเนินการต่อ ได้ปิดความเสี่ยงseed/resetตามค่าที่เสนอ และแก้หัวรายงานให้ใช้ข้อมูลที่ทราบจริง ขั้นเตรียมreleaseเสร็จแล้ว ยังไม่commit/push/deployโค้ดและยังไม่ซ่อมallocation

## เปลี่ยน production config แล้ว

เวลา9ก.ย.2026 **10:25:43 น.ไทย** อ่านกลับจากRailwayยืนยัน:

| ตัวแปร | ก่อน | หลัง |
|---|---|---|
| RUN_PROD_SEED | true | false |
| PROD_RESET_ADMIN_PASSWORD | true | false |

ส่งเฉพาะสองค่านี้ด้วย`replace=false`, `skipDeploys=true` เปรียบเทียบvariablesก่อน/หลังแล้วตัวแปรอื่นไม่เปลี่ยน Active deploymentยังเป็น `7c6d5c98-918b-4744-b3cc-ab4de9d4454d` ไม่ได้สั่งrestart/deploy ไม่เปลี่ยนsecretหรือข้อมูลการเงิน การปิดค่าตั้งมีผลกับstartupครั้งถัดไป

## หัวรายงาน

- Defaultชื่อโครงการไทย: **หมู่บ้านแมกไม้ลีลาวดี** ตามข้อมูลโปรเจกต์
- ยังไม่มีชื่ออังกฤษที่เจ้าของระบุ จึงให้เป็นค่าว่างและrenderชื่อไทยอย่างเดียว ไม่มี `/` ค้างท้าย รองรับชื่ออังกฤษผ่านconfigเมื่อมีข้อมูลในอนาคต
- ข้อความติดต่อ: **กรุณาติดต่อฝ่ายบัญชี/นิติบุคคล** แทนเบอร์และอีเมลสมมติ ไม่มีการสร้างช่องทางติดต่อขึ้นเอง
- เปลี่ยนเฉพาะค่าตั้งเริ่มต้นใน `config.py` และการประกอบชื่อในPDF/Excel ไม่ได้เปลี่ยนค่าPROJECT_NAME/CONTACTบนRailwayซึ่งปัจจุบันยังunset

## ผลตรวจชุดสุดท้าย

- รันregressionหลังแก้หัวรายงาน: **72ผ่าน** (PG45 + canonical12 + paid-at7 + export8) รวม13real PostgreSQL blocking race tests
- HTTP/download/สิทธิ์บนสำเนาbackupใหม่: **2,532 checksผ่าน** รวม157บ้าน,114membership records,111resident/Adminรายงานตรงกัน,222resident downloads และเพิ่มตรวจชื่อจริงในExcelทุกบ้าน
- ตรวจPDF 28/95พฤษภาคม1หน้าและรายงานทดสอบยาว3หน้าครบทุกหน้า: ชื่อไทยถูก ไม่มีเบอร์/อีเมลสมมติ ยอดและข้อความรอตรวจชัด หัวตาราง/เลขหน้าครบ
- Fingerprintทุกpublic tableของสำเนาที่ใช้ตรวจไม่เปลี่ยน ใช้read-onlyตลอด; testsที่เขียนข้อมูลใช้random schemaของlocal test DB
- Financial/read codeนอกส่วนหัวรายงานคงจากR2ที่ผ่านall-house/SQL matricesก่อนหน้า Frontendไม่เปลี่ยนในรอบหัวรายงาน ผลbuildและharnessR2เดิมยังใช้กับsourceเดียวกัน
- DB backupล่าสุดที่verified: เวลา10:16:13น.26ตารางตรงกับsourceในexported snapshotเดียวกัน; SHA256 `7b05ab759eb38b7a11e20162af174a1109d305de91f575fe4baf4ab700e273bb`; Alembic `p5_1_notifications`

## ชุดที่จะอนุมัติ

รวมการแก้R1/R2ที่reviewแล้ว: ยอดและสถานะใบแจ้งหนี้/รายงาน, การรับเงินกับallocationแยกความหมาย, eligibilityที่ยืนยันStatement, สิทธิ์รายงานลูกบ้าน, เวลาไทย, สลิปรอตรวจ, export/downloadและหัวรายงาน มีfinancial writer changesที่เปิดเผยแล้วในR2 ไม่มีmigration/dependency/Docker/startup script changes ไม่มีdata-repair scriptในsourceที่จะcommit

ฐานrollbackโค้ด `f367d8832c266ad9c9010bd1fb04a1b0fcafcab6`; เสนอcommit `fix(finance): reconcile receipt reports and enforce house report access`

แพ็กเกจpatch/zip/manifestสุดท้ายเก็บprivateนอกGitใน `release-candidate-20260909-final` ใช้private Git indexเตรียมtree ไม่มีcommitและไม่เปลี่ยนreal index; R1/R2 packagesเดิมเก็บไว้

หลังได้รับอนุมัติ: ตรวจremoteและsource hashesก่อนcommit/push, ตรวจว่าค่าปิดseed/resetยังอยู่, refreshbackupหากมีข้อมูลใหม่/เวลาผ่านไป, รอRailway/Verceldeployทั้งคู่และตรวจproductionตามสิทธิ์จริง การแก้allocation28/95/62บ้านยังเป็นงานแยก

ข้อจำกัดที่ยังต้องยืนยันหลังdeploy: LINE OAuth/มือถือจริง และการใช้งานproductionหลังrelease; Docker Desktopในเครื่องยังbuildไม่ได้ R2 object bytesของสลิป/ไฟล์แนบไม่ได้อยู่ในDB dump ไม่รับรองว่าทั้งระบบไม่มีความเสี่ยง

Rollbackให้revertreleasecommit/redeployartifactเดิม ไม่restoreDBเก่าทับธุรกรรมใหม่ และไม่เปิดseed/resetกลับเป็นtrue

หลักฐานprivate: `release-seed-disabled.private.json`, `release-final-validation/report-access-validation.private.json`, `release-final-validation/regression-pg.log`, `pre-release-current.json` ใน `C:\Users\sanch\moobaan-db-backups\20260909-2895`
