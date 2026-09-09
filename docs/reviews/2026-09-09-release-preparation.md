# R2 — เตรียม release หลังเจ้าของอนุมัติให้ดำเนินการต่อ

**อัปเดตถัดมา:** เจ้าของให้ดำเนินการต่อ ปิดseed/resetและแก้หัวรายงานเรียบร้อยแล้ว ดู `2026-09-09-final-release.md` ข้อความด้านล่างเป็นหลักฐานก่อนการเปลี่ยนค่าตั้ง

สถานะ: **เตรียมโค้ดและbackupแล้ว ยังไม่deploy** พบค่าตั้งproductionที่ต้องจัดการก่อนเริ่มrelease รอบนี้ไม่มีการเปลี่ยนapplication codeหรือข้อมูลproduction

## ยืนยันฐานสำหรับ release

- Local HEAD, GitHub master และ Railway active successful deployment ตรงกันที่ `f367d8832c266ad9c9010bd1fb04a1b0fcafcab6`
- Railway backend service `moobaan_smart` / environment `production`, root `/backend`; active deployment `7c6d5c98-918b-4744-b3cc-ab4de9d4454d`
- Railway active build metadataใช้DOCKERFILE เช่นเดียวกับ `backend/railway.json`; startupใช้ `python startup.py` ตามDockerfile การดู service-level builderอย่างเดียวอาจเห็นRAILPACKแต่ไม่ใช่effective buildในdeploymentนี้
- Application/test sources27ไฟล์ยังมีSHA-256ตรงกับแพ็กเกจR2ที่ผ่าน72regressions ไม่ได้แก้โค้ดหลังผลทดสอบ ชุดเอกสารประกอบมีการเพิ่มภายหลัง
- Backend `/health`, `/ready` และหน้าแรกVercelตอบ200 ใช้ตรวจสถานะเบื้องต้นเท่านั้น ไม่ใช่การทดสอบresident loginหรือรายงานproductionด้วยสิทธิ์ลูกบ้าน

## Backup ใหม่และการตรวจคืน

สำรองproduction snapshotเวลา **9ก.ย.2026 10:16:13 น.ไทย** (`2026-09-09T03:16:13.041276Z`):

- ไฟล์private `pre-release-20260909T031612Z/snapshot.dump`, PostgreSQL custom format,221503bytes
- SHA-256 `7b05ab759eb38b7a11e20162af174a1109d305de91f575fe4baf4ab700e273bb`
- Export snapshotจากtransaction REPEATABLE READ READ ONLY แล้วให้pg_dumpใช้snapshotเดียวกันกับการhashข้อมูล เพื่อไม่ให้ธุรกรรมอื่นที่เกิดระหว่างสำรองทำให้เทียบคนละเวลา
- Restoreด้วย`--exit-on-error`ไปDBใหม่บนlocalhost `release_verify_20260909t031612z`; ทั้ง26public tables จำนวนแถวและhashตรงsourceทุกตาราง
- Alembic productionและrestored DBเป็น `p5_1_notifications` ตรงcode head ไม่มีmigrationใหม่ในrelease
- เทียบกับDBสำเนาที่ใช้ทดสอบR2: ไม่มีpublic tableเปลี่ยน จึงไม่ต้องทำfull matrixซ้ำเพียงเพราะไฟล์dumptimestampเปลี่ยน
- รอบแรกกู้คืนได้แต่ตรวจhashไม่ผ่านใน10ตาราง ทั้งหมดจำนวนแถวเท่ากัน สาเหตุคือORDER BYข้อความใช้collationต่างกันระหว่างLinux/Windows แก้ตัวตรวจให้ใช้`COLLATE "C"`ทั้งsource/restore แล้วสร้างbackupใหม่และตรวจผ่าน ไม่ผ่อนเกณฑ์ตรวจข้อมูล เก็บไฟล์รอบแรกไว้เป็นหลักฐานและไม่อ้างว่าเป็นชุดverified
- นี่คือlogical DB backupที่ไม่คืนowner/ACLเดิม และไม่รวมR2 object bytesของสลิป/ไฟล์แนบ ไม่ใช่การสำรองstorageทั้งระบบ

## สิ่งที่พบจาก Railway variables จริง

| ค่า | Productionที่อ่านได้ | ค่าที่เสนอ |
|---|---|---|
| RUN_PROD_SEED | true | false |
| PROD_RESET_ADMIN_PASSWORD | true | false |
| PROD_CREATE_SAMPLE_HOUSE | ไม่ได้ตั้ง | คงเดิม |

มีตัวแปรseed admin email/passwordอยู่จริง (ไม่เปิดเผยค่า) `prod_seed.py`ตรวจRUN_PROD_SEEDก่อน และเมื่อพบadminเดิมจะรีเซ็ตcredentialsหากPROD_RESET_ADMIN_PASSWORD=true ดังนั้นการrestart/deployโดยปล่อยค่าปัจจุบันมีความเสี่ยงที่เป็นรูปธรรม

เตรียมคำขอแก้variablesสองตัวข้างต้นในprivate JSONแล้ว แต่ **ยังไม่ส่ง mutation** ใช้`replace=false`เพื่อคงตัวแปรอื่น และ`skipDeploys=true`เพื่อไม่ให้เปลี่ยนค่าตั้งแล้วสร้างdeploymentแยกก่อนโค้ดพร้อม ตามschemaRailwayที่ตรวจจริง ต้องอ่านค่ากลับยืนยันและตรวจว่าactive deploymentยังเป็นตัวเดิมก่อนcommit/push ไม่ลบหรือแก้ค่าsecretอื่น

## หัวรายงานยังต้องระบุข้อมูลจริง

Productionยังไม่ได้ตั้ง`PROJECT_NAME_TH`, `PROJECT_NAME_EN`, `ACCOUNTING_CONTACT` จึงใช้ค่าเริ่มต้น “หมู่บ้านสมาร์ท / Smart Village” และเบอร์/อีเมลตัวอย่าง การแจกPDF/Excelลักษณะนี้ไม่เหมาะสม

ชื่อไทยที่มีหลักฐานในโปรเจกต์คือ “หมู่บ้านแมกไม้ลีลาวดี” ได้ถามเจ้าของเรื่องชื่ออังกฤษและช่องทางติดต่อแล้ว ยังไม่ตั้งค่าและไม่สร้างข้อมูลติดต่อขึ้นเอง หากเลือกชื่อไทยอย่างเดียว ต้องปรับการrenderไม่ให้เหลือเครื่องหมาย `/` และตรวจPDFอีกครั้งก่อนfreezeแพ็กเกจสุดท้าย

## ลำดับดำเนินการหลังได้ข้อสรุป

1. ยืนยันชื่อ/ข้อมูลติดต่อหัวรายงาน และแก้/ตรวจเฉพาะส่วนที่จำเป็นก่อนfreezeชุดสุดท้าย
2. อนุมัติค่าตั้งที่จะเปลี่ยน ปิดseed/resetแบบไม่deployอัตโนมัติ แล้วอ่านกลับตรวจผล รวมค่าหัวรายงานที่ตกลง
3. ตรวจremoteยังไม่เปลี่ยนและbackupยังทันต่อข้อมูลล่าสุด; หากผ่านเวลาไปหรือมีธุรกรรมใหม่ ทำbackupก่อนproduction actionอีกครั้ง
4. ให้เจ้าของอนุมัติcommit/pushชุดreleaseที่ชัดเจนตามAGENTS.md แล้วdeployผ่านGitHubไปRailway/Vercel ตรวจทั้งสองฝั่งจนสำเร็จ
5. ตรวจhealth/readiness, สถานะrelease, Admin/residentด้วยสิทธิ์ที่ถูกต้อง, report/download และข้อมูล28/95เทียบStatement โดยไม่แก้allocation
6. หากต้องrollback ใช้revert release commitหรือredeployartifactเดิม ไม่restoreDBเก่าทับธุรกรรมใหม่ และไม่เปิดseed/resetกลับเป็นtrue

ข้อความcommitที่เสนอ: `fix(finance): reconcile receipt reports and enforce house report access`

การซ่อมallocation28/95และรายการ62บ้านเป็นอีกขั้น ต้องใช้แผนรายรายการ/backup/transaction preconditionsแยก ไม่มีส่วนใดในrelease preparationนี้ดำเนินการแทน

หลักฐานprivateและคำขอแก้ที่ยังไม่executeอยู่ใน `C:\Users\sanch\moobaan-db-backups\20260909-2895`: `pre-release-current.json`, `release-startup-settings.private.json`, `release-service-state.private.json`, `proposed-disable-seed.variables.json` ไม่ใส่secretsหรือข้อมูลลูกบ้านในGit
