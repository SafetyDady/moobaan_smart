# ผล release ระบบกระทบยอดอัตโนมัติ

**Owner อนุมัติแล้ว และ deploy สำเร็จวันที่ 9 ก.ย. 2026 ประมาณ 14:49 น. ไทย**

| รายการ | ผล |
|---|---|
| Application commit | `43a52b734e0e762c2a26311c39abec12ac6dc62c` |
| Tree ที่อนุมัติและ deploy | `ebca0b71867f61648d739a0b49408b28e9f00050` ตรง candidate ทุกไฟล์ |
| Parent / rollback code | `f3221398d46d16bf4289e9236962e179193c3738` |
| Railway deployment | `e94d9147-584c-4a9b-8b16-42dad60e07f4` — SUCCESS |
| Vercel deployment | `BcxbhcDiaMXETW16WaE5sXLU2sYf` — SUCCESS |
| Seed / reset ก่อน push | ทั้งคู่ false; ไม่เปลี่ยน config ในรอบนี้ |

## Backup ก่อน push

สำรอง production แบบ read-only ณ **14:46:20 น. ไทย** และกู้คืนในฐานใหม่ก่อน commit/push ตรวจจำนวนแถว/hash 26 ตารางและ Alembic revision ตรงกัน ข้อมูลทุกตารางยังตรง snapshot ที่ใช้ทดสอบ

- SHA256: `4b4ddc0b6dbe2724ecc227af8f6a3efc46ae8ec56a5c459879baead6d9ad57c7`
- 221,544 bytes; PostgreSQL custom dump
- Private directory: `C:\Users\sanch\moobaan-db-backups\20260909-2895\automatic-ready-20260909T074619Z`
- Restored database: `auto_ready_20260909t074619z`
- เก็บ backup ก่อนหน้าครบ รวมสมาชิก 28/95 ที่เจ้าของเพิ่มไว้; DB backup ไม่รวม bytes รูป/เอกสารใน R2

## ตรวจหลัง deploy

- Railway และ Vercel ยืนยัน commit เดียวกันสำเร็จ; health และ ready ตอบ 200
- Anonymous GET ของ invoice list, allocatable-ledgers, single invoice, detail และ payments ผ่านทั้ง API ตรงและ frontend สองโดเมน: **15 requests ตอบ 401**
- ใช้ session Admin จริงที่มีอยู่ รีโหลดแล้วค้นบ้าน 28/95 ได้: 8 บิล ชำระแล้ว 6 ค้าง 2 เดือนละ 600 บาท วันที่ชำระและการผูกยอดเดิมคงเดิม
- ใช้ session resident จริงที่มีอยู่ รีโหลดแล้วเห็นบ้าน 28/95; ประวัติส่งสลิปมี 11 พฤษภาคม 600 บาทยืนยันแล้ว และกันยายนยังรอตรวจ; แท็บใบแจ้งหนี้ตรงกับ Admin (8/6/2)
- ทดสอบ resident อ่าน `/api/invoices?house_id=97`: browser ไม่แสดง JSON แต่ **Railway application log ยืนยัน GET นี้ถูกปฏิเสธ 403 เวลา 07:49:58 UTC** จึงไม่ได้อาศัย browser error อย่างเดียวสรุปสิทธิ์ คืนหน้า resident payments หลังตรวจแล้ว
- เทียบ production หลัง deploy แบบ READ ONLY กับ backup ก่อน push: **26 ตารางไม่มีการเปลี่ยนจำนวนแถว/hash**; Alembic `p5_1_notifications`

ไม่ได้สร้างบิล ยืนยันเงินจริง หรือซ่อมการผูกยอดใดใน production เพื่อทดสอบ การตรวจธุรกรรมใหม่บน Local ก่อนขึ้นระบบผ่าน 101 regressions, 20 race cases และ 9 HTTP lifecycle scenarios ตามรายงาน readiness

## ผลต่อการใช้งานและงานที่ยังแยกอยู่

โค้ดใหม่ใช้งานแล้ว การยืนยันเงินหรือสร้างบิลครั้งถัดไปจะนำเงินยืนยันที่ยังเหลือของบ้านไปชำระบิลอัตโนมัติตาม FIFO ลูกบ้านไม่ต้องเลือกบิล ไม่มี startup sweep หรือการย้ายประวัติเดิมอัตโนมัติ

บ้าน 28/95 และบ้านอื่นยังไม่ได้ซ่อมลำดับประวัติย้อนหลัง ก่อนซ่อมต้องทำ before/after ใหม่จากข้อมูลขณะนั้น เพราะ transaction ปกติหลัง release อาจใช้เงินเหลือไปแล้ว ห้ามนำรายการซ่อมเก่ามารันทันที

การ rollback code ไม่ย้อน allocation ที่เกิดหลัง deploy ต้องเก็บ seed/reset false และไม่ restore DB เก่าทับธุรกรรม/สมาชิกใหม่ หากต้องแก้ยอดใช้รายการชดเชยที่มี audit

ผลข้างต้นเป็นการตรวจ ณ หลัง release ไม่ใช่การรับรองทุกส่วนของระบบหรือการเฝ้าติดตามต่อเนื่อง ไม่ได้ทดสอบ LINE login ใหม่หรือดาวน์โหลดรูป R2 ในรอบนี้

## หลักฐานส่วนตัว

ใต้ `C:\Users\sanch\moobaan-db-backups\20260909-2895`:

- `automatic-approved-release-state.json`, `automatic-publish-preflight.json`
- `automatic-deployment-latest.json`, `automatic-postdeploy-checks.json`
- `automatic-cross-house-verification.json` และ filtered application log
- `automatic-production-candidate-20260909T074014Z/manifest.json`

รายงาน/context นี้บันทึกหลัง application release; commit เอกสารที่ตามมาคง application code ชุดเดียวกัน
