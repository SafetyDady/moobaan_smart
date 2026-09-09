# Local PC: เว็บทดสอบและผลตรวจเพิ่มเติม

**พร้อมให้เจ้าของทดลอง:** http://127.0.0.1:5175/__local

เปิดจาก PC เครื่องนี้ แล้วกด **เปิดหน้า Admin** หรือ **เปิดหน้าลูกบ้าน 28/95** ไม่ต้องใช้รหัสผ่าน production สลับบทบาทได้จากแถบสีเหลือง LOCAL TEST ทุกหน้า การสลับบทบาทเปลี่ยน session ใน browser เดียวกัน

## ข้อมูลและการแยกจาก production

- ใช้ฐานข้อมูลใหม่ชื่อ `ui_lab_*` ที่คัดลอกจาก backup ณ 9 ก.ย. 2026 เวลา 11:10:13 น. ไทย ครบ 157 บ้าน
- ตรวจ hash ทั้ง 26 ตารางตรงต้นทางก่อนเตรียมบัญชีเข้า Local เปลี่ยนเฉพาะข้อมูลล็อกอินในตาราง users ของสำเนา: สร้าง Admin ทดสอบ และตั้งรหัส Local ให้บัญชี resident ที่มี membership ของ 28/95 อยู่จริง ไม่แก้สมาชิกหรือข้อมูลการเงินตอนเตรียม
- Backend/Frontend/PostgreSQL ฟังเฉพาะ `127.0.0.1` ที่พอร์ต 8010/5175/55440 ไม่เปิดให้เครื่องอื่นใน LAN
- Backend ใช้ DB role ของสำเนาที่ไม่มี superuser/createdb; ตรวจแล้วอ่านตารางในฐานหลักฐานต้นทางไม่ได้ และ guard ปฏิเสธ DB connection นอกฐานทดสอบที่กำหนด
- Process ใช้ environment ที่คัดเฉพาะค่าระบบ ไม่โหลด `.env` ของ production; ปิด LINE/OTP/R2/seed/reset; block external Python DNS/socket connections และ browser external resource requests ด้วย CSP
- ไฟล์อัปโหลดทดสอบลง private local directory; รูปสลิปเก่าที่อยู่บน R2 ไม่ได้ดาวน์โหลดมา จึงทดสอบการดูรูปเก่าและ LINE login จริงไม่ได้
- บัญชี Local ผ่าน password login และ resident house-selection logic เดิม แต่มี launcher เฉพาะเครื่องช่วยล็อกอิน ไม่ใช่การทดสอบ LINE OAuth

Local harness ทั้งหมดอยู่ที่ `C:\Users\sanch\moobaan-db-backups\20260909-2895\local-lab` นอก Git/OneDrive ไม่รวมใน production release

## วิธีลองด้วยตนเอง

1. เปิด portal → Admin → ค้นบ้าน `28/95` ตรวจบิลและเงินรับพฤษภาคม 600 บาทที่ยังเหลือ
2. กดสร้างใบแจ้งหนี้รายเดือน เลือก **กันยายน 2026** การกระทำนี้สร้างบิลและจัดสรรเงินเหลือในฐานทดสอบทุกบ้าน
3. บ้าน 28/95: เงินพฤษภาคมที่เหลือลงบิลกรกฎาคมซึ่งค้างเก่าสุด บิลพฤษภาคม/มิถุนายนที่ชำระไว้แล้วไม่ถูกย้าย; สิงหาคมและกันยายนค้างเดือนละ 600 บาท
4. สร้างเดือนกันยายนซ้ำ ต้องได้ 0 บิลใหม่และไม่มี allocation เพิ่ม
5. กลับ portal → ลูกบ้าน 28/95 → ดูประวัติส่งสลิปและแท็บใบแจ้งหนี้ ตรวจว่าเห็นบิลตรงกับ Admin และสลิปรอตรวจยังไม่ถูกนับเป็นเงินยืนยัน

ขั้นตอนนี้ทดสอบการป้องกันเกิดซ้ำ ไม่ใช่การซ่อมลำดับประวัติย้อนหลัง การเลือกบ้านเพื่อดูข้อมูลไม่ให้สิทธิ์ลูกบ้านเลือกบิลชำระ

## ผลที่รันจริง

- เปิดหน้าจริงใน browser ทั้ง Admin และ resident; เห็นรายการรับเงินพฤษภาคมและสถานะบิลหลังจัดสรร
- เรียก HTTP ผ่าน Vite proxy → Uvicorn → PostgreSQL จริง: สร้าง 157 บิล / 313 allocations / ใช้เงินเพิ่ม 181,012.56 บาท; retry ได้ 0 บิล และ hash DB หลัง retry เท่าเดิม
- JSON ใบแจ้งหนี้ Admin/resident ของ 28/95 ตรงกัน ก่อนและหลังทดสอบ
- เนื้อหารายงานเงินรับพฤษภาคมของทั้ง 157 บ้านเท่าเดิม (ไม่นับ metadata เวลาที่ร้องขอรายงาน); allocation เดิมและตารางหลักฐานเงินรับเท่าเดิม
- สำเนาหลักฐานต้นทางยังตรงทั้ง 26 ตาราง ไม่เชื่อมต่อ production ในงานนี้
- Regression หลังแก้เพิ่มเติม: **101 ผ่าน = 74 PostgreSQL + 27 status/date/export**; รวม 20 race cases เดิม

HTTP evidence: `local-lab/http-verification.json` บนฐานทดสอบ `ui_lab_20260909_052613` จากนั้นเตรียมฐานสำเนาใหม่ให้เจ้าของเริ่มทดสอบเอง โดยเก็บฐานที่ทดลองแล้วไว้

## พบและแก้เพิ่มเติมจากการทดสอบ Local

**[P1] API อ่านใบแจ้งหนี้ที่หน้าใช้งานจริงขาดการตรวจสิทธิ์ 5 เส้นทาง:** list, single invoice, detail, payments และ allocatable-ledgers. ทดสอบ Local พบ anonymous ได้ 200 และ resident เข้าข้อมูลนอกบ้านได้ จุดนี้ต่างจาก legacy `/accounting/invoices/house/...` ที่แก้ไปก่อนแล้ว จึงห้ามอ้างว่าการแก้ legacy เดิมครอบคลุม route ชุดนี้

แก้ใน `backend/app/api/invoices.py`: ต้องล็อกอิน; resident list จำกัดบ้านจาก token แม้ไม่ส่ง filter, ถ้าระบุบ้านต้องตรง token และมี active membership; single/detail/payments ใช้ house-access guard เดียวกับ reports; allocatable-ledgers ให้ Admin/accounting เท่านั้น ไม่เปลี่ยนยอดหรือการจัดสรรเงิน

เพิ่ม `backend/test_invoice_read_access_postgres.py` 5 tests: ก่อนแก้เกิด 19 failing subcases, หลังแก้ผ่านทั้งหมด ครอบ anonymous, Admin/accounting, resident บ้านตนเอง, ไม่ส่ง filter, token ไม่เลือกบ้าน/บ้านไม่ตรง, membership ปิดใช้งานแม้ legacy row ยังอยู่

ยังไม่ได้ deploy การแก้สิทธิ์นี้ ไม่ได้ทำการสแกน production เพื่อยืนยันการเข้าถึงจากภายนอก และไม่อ้างว่าตรวจสิทธิ์ทุก API ในระบบแล้ว

## เปิด/ปิด/เริ่มทดสอบใหม่

ใน PowerShell:

```powershell
& 'C:\Users\sanch\moobaan-db-backups\20260909-2895\local-lab\Start-Local.ps1'
& 'C:\Users\sanch\moobaan-db-backups\20260909-2895\local-lab\Stop-Local.ps1'
& 'C:\Users\sanch\moobaan-db-backups\20260909-2895\local-lab\Reset-Local.ps1'
```

เลือกใช้คำสั่งตามต้องการ ไม่ต้องรันทั้งสามต่อกัน Reset สร้างสำเนาใหม่ ไม่ลบหรือ restore ทับฐานเดิม หลัง Reset ให้เปิด portal ใหม่และเลือกบทบาทอีกครั้ง

ชุดนี้ยังไม่ได้ commit/push/deploy การอนุมัติ release ต้องอ้าง candidate ล่าสุดที่รวม access fix นี้ และต้องสำรอง DB สดก่อนงาน production ไม่ใช้ผลทดสอบ Local เป็นการอนุมัติย้ายยอดย้อนหลัง
