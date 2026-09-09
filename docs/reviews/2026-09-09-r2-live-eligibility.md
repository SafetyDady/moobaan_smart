# R2 — ตรวจเงื่อนไข eligibility บน production ตามข้อเสนอที่ปรึกษา

ตรวจเมื่อ **9 กันยายน 2026 เวลา10:09:33 น. Asia/Bangkok** ใช้ PostgreSQL `REPEATABLE READ`, `transaction_read_only=on`, SSL และ statement timeout30วินาที ไม่เรียก financial writer หรือ application startup และปิด transaction ด้วย rollback

| รายการตรวจ | จำนวน |
|---|---:|
| POSTED ledger ทั้งหมด | 283 |
| ผ่าน `allocation_error()` | 283 |
| ไม่ผ่าน `allocation_error()` | 0 |
| POSTED ledger ที่ `payin_id IS NULL` | 0 |
| กลุ่มไม่มี pay-in: ผ่าน / ไม่ผ่าน | 0 / 0 |
| สาเหตุปฏิเสธในกลุ่มไม่มี pay-in | ไม่มีรายการให้จัดประเภท |

เรียกฟังก์ชัน eligibility จริงจาก sourceที่ SHA-256ตรงกับแพ็กเกจR2 และตรวจเกณฑ์ no-pay-in ซ้ำด้วย SQLอิสระใน transactionเดียวกัน ผลตรงกัน ไม่ใช่ใช้ตัวเลขจากbackupเก่า

**ข้อสรุปเฉพาะเงื่อนไขที่ที่ปรึกษาขอ:** ณ เวลาตรวจ ไม่มี POSTED no-pay-in ledger ที่จะถูกซ่อนจาก pickerเพราะการเทียบยอด/เวลาแบบเป๊ะ จึงไม่มีรายการเงินจริงในกลุ่มนี้ที่ต้องแก้ก่อน release ด้วยเหตุผลดังกล่าว การผ่าน eligibilityทั้งหมดไม่ได้แปลว่า283รายการยังมีเงินเหลือให้ใช้ เพราะ pickerตรวจ remaining>0แยกอีกชั้น

คงเกณฑ์ยอดและเวลาให้ตรง Statement ไม่เพิ่ม toleranceหรือเปลี่ยนข้อมูลต้นฉบับเพื่อให้ผ่าน ถ้าในอนาคตมีรายการไม่ผ่าน:

1. ใช้ auditอ่านอย่างเดียวระบุledger/bank/batch และเงื่อนไขที่ไม่ผ่าน ตรวจยอดคงเหลือแยกจากการจัดสรร
2. เทียบStatementต้นฉบับกับledgerและประวัติ reversal/matching ระบุว่าผิดที่หลักฐาน การเชื่อม หรือข้อมูลในledger
3. บันทึกรายการค้างและสาเหตุให้Adminตรวจ ห้ามตีความว่าไม่มีเงินหรือชำระเรียบร้อยเพราะไม่ปรากฏในpicker
4. ออกแผนแก้รายรายการพร้อมbackupใหม่และaudit trail ขออนุมัติก่อนเปลี่ยนเงินจริง ไม่แก้ยอด/เวลา/สลิปต้นฉบับแบบเงียบๆ

นี่เป็นขั้นตอนรับมือที่บันทึกไว้ ไม่ใช่ระบบแจ้งเตือนอัตโนมัติใหม่หรือหน้าจอแสดงรายการถูกปฏิเสธที่พัฒนาแล้ว

## ปรับถ้อยคำในรีวิวให้ตรงหลักฐาน

- `excluded_from_confirmed_receipts=True` เป็นข้อมูลกำกับ ไม่ได้ทำให้การบวกเงินผิดเป็นไปไม่ได้ สิ่งที่ตรวจแล้วคือ calculationและUIแยกยอด พร้อมregression tests
- Guardเดียวกันครอบคลุม7handlerที่ตรวจ ไม่ใช่การรับรองauthorizationทั้งระบบ; ข้อบกพร่องguardเดิมควรแก้ แต่การอ่านโค้ดนี้ยังไม่พิสูจน์ว่ามีผู้ใช้ดึงข้อมูลบ้านอื่นจากproductionสำเร็จ
- Deployโค้ดไม่เท่ากับไม่มีการเขียนDBโดยอัตโนมัติ: startupเดิมอาจmigrate/seedตามlive flags ต้องตรวจตามrelease checklist
- Rollbackด้วยrevert release commitหรือredeploy artifactเดิม ไม่reset/force-pushกลับฐานเก่า และไม่restoreDBเก่าทับธุรกรรมใหม่

ไม่มีการแก้application code, production DB, allocation, commit, push หรือdeployในรอบตรวจนี้ เงื่อนไขเรื่องledgerไม่มีpay-inปิดได้ ณ เวลาตรวจ; เงื่อนไขreleaseอื่นจากรายงานR2ยังคงอยู่ รวมowner approval, fresh backup, live startup flags และpost-deploy checks

หลักฐานprivate: `C:\Users\sanch\moobaan-db-backups\20260909-2895\20260909T030934Z-r2-live-eligibility.private.json` สคริปต์อ่านอย่างเดียว `audit_r2_live_eligibility.py` อยู่ในโฟลเดอร์เดียวกัน ไม่เก็บcredential/ข้อมูลลูกบ้านไว้ในGit

แพ็กเกจR2เดิมคงไว้ไม่เปลี่ยน รอบนี้เพิ่มเอกสาร/contextเท่านั้น ก่อนcommitต้องรวมและตรวจdiffของเอกสารที่เพิ่มภายหลังแพ็กเกจด้วย
