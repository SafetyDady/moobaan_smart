# 🚨 CRITICAL ISSUE REPORT: Database Data Inconsistency

**วันที่รายงาน:** 15 มกราคม 2026  
**ระดับความรุนแรง:** 🔴 CRITICAL  
**ผู้รายงาน:** User

---

## 📋 สรุปปัญหา

ผู้ใช้รายงานว่าข้อมูลในระบบไม่สอดคล้องกัน:

### ก่อนหน้า (Session 1):
- บ้าน 28/1 มียอดค้าง **1,800 บาท**
- มีรายการ **Submitted payment**

### ตอนนี้ (Session 2):  
- บ้าน 28/1 มียอดค้าง **5,400 บาท**
- **ไม่มี** รายการ Submitted pay-in

---

## 🔍 การสืบสวน

### 1. ตรวจสอบ Database Container

```powershell
docker ps | grep postgres
```

**ผลลัพธ์:**
- `docker-db-1` (moobaan_smart) - **RUNNING** บน port 5432
- `smart_erp_db` - **EXITED** (project อื่น)

✅ **สรุป:** มี PostgreSQL container เดียวที่กำลังรัน

---

### 2. ตรวจสอบ Backend Configuration

**ไฟล์:** `backend/.env`
```dotenv
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/moobaan_smart
```

**ตรวจสอบจริง:**
```python
from app.core.config import Settings
s = Settings()
print(s.DATABASE_URL)
# Output: postgresql+psycopg://postgres:postgres@localhost:5432/moobaan_smart
```

✅ **สรุป:** Backend เชื่อมต่อกับ database ที่ถูกต้อง

---

### 3. ตรวจสอบ Database Schema

**Tables ที่มี:**
```
- alembic_version
- house_members
- houses
- users
- expenses
- invoices
- payin_reports
- income_transactions
- credit_notes
- invoice_payments
```

**Columns ใน `houses` table:**
```sql
- id: INTEGER
- house_code: VARCHAR(20)
- house_status: VARCHAR(10)
- owner_name: VARCHAR(255)
- floor_area: VARCHAR(50)
- land_area: VARCHAR(50)
- zone: VARCHAR(10)
- notes: TEXT
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

⚠️ **ข้อสังเกต:** **ไม่มี `balance` column** - balance คำนวณแบบ dynamic จาก transactions

---

### 4. ตรวจสอบข้อมูลจริงใน Database

**บ้าน 28/1:**
```
ID: 3
Owner: ทดสอบ
Status: ACTIVE
```

**Pay-in reports สำหรับบ้าน 28/1:** **0 รายการ** ❌

**Pay-in reports ทั้งหมดในระบบ:** **2 รายการ**

---

## 🎯 สาเหตุที่เป็นไปได้

### ❌ สาเหตุที่ไม่ใช่:
1. ❌ **มีฐานข้อมูลหลายตัว** - ตรวจสอบแล้วมี container เดียว
2. ❌ **Connection string ผิด** - backend เชื่อมต่อถูกต้อง
3. ❌ **SQLite file ซ่อนอยู่** - ไม่พบไฟล์ .db ในระบบ

### ✅ สาเหตุที่เป็นไปได้สูง:

#### **1. Frontend Cache/Local Storage ปนกับข้อมูลเก่า**
- Browser อาจ cache ข้อมูลจาก session ก่อนหน้า
- LocalStorage หรือ SessionStorage อาจมีข้อมูลตกค้าง

#### **2. การ Seed Data หลายครั้ง**
- มีการรัน seed script ทับข้อมูลเก่า
- Pay-in reports ถูกลบออกจากการ seed ใหม่

#### **3. Backend Restart หรือ Migration ใหม่**
- มีการรัน `alembic downgrade` แล้ว `upgrade` ใหม่
- Data ถูก reset แต่ frontend ยัง cache ข้อมูลเก่า

#### **4. Balance Calculation Logic**
- Balance คำนวณจาก API แบบ real-time
- ค่า 1800 และ 5400 อาจมาจาก:
  - Invoices ที่ยังไม่ได้ชำระ
  - Credit notes
  - Income transactions

---

## 🔬 ข้อมูลเพิ่มเติมที่ต้องการ

เพื่อหาสาเหตุที่แท้จริง ต้องตรวจสอบ:

### 1. Frontend Local Storage
```javascript
console.log(localStorage);
console.log(sessionStorage);
```

### 2. Invoices สำหรับบ้าน 28/1
```sql
SELECT * FROM invoices WHERE house_id = 3;
```

### 3. Income Transactions
```sql
SELECT * FROM income_transactions WHERE house_id = 3;
```

### 4. Credit Notes
```sql
SELECT * FROM credit_notes WHERE house_id = 3;
```

### 5. ประวัติการรัน Seed Scripts
- ตรวจสอบ terminal history
- ดู timestamp ของ alembic_version

---

## 🛠️ แนวทางแก้ไขเบื้องต้น

### ⚡ Quick Fixes (ทันที):

#### 1. Clear Browser Cache & Local Storage
```javascript
// ใน Browser Console
localStorage.clear();
sessionStorage.clear();
location.reload();
```

#### 2. Restart Frontend
```powershell
# Stop frontend
Ctrl+C

# Start fresh
cd C:\web_project\moobaan_smart\frontend
npm run dev
```

#### 3. ตรวจสอบ Balance Calculation API
```powershell
# Test API endpoint
curl http://127.0.0.1:8000/api/dashboard/summary
```

---

### 🏗️ Long-term Solutions:

#### 1. **เพิ่ม Logging สำหรับ Balance Calculation**
```python
# backend/app/api/dashboard.py
import logging
logger = logging.getLogger(__name__)

def calculate_balance(house_id: int):
    logger.info(f"Calculating balance for house {house_id}")
    # ... existing logic
    logger.info(f"Result: {balance}")
```

#### 2. **ทำ Database Snapshot ก่อน/หลัง Seed**
```sql
-- Backup before seed
pg_dump -U postgres moobaan_smart > backup_before_seed.sql

-- Restore if needed
psql -U postgres moobaan_smart < backup_before_seed.sql
```

#### 3. **เพิ่ม API Endpoint สำหรับ Debug**
```python
@router.get("/debug/house/{house_id}/balance-breakdown")
async def debug_balance_breakdown(house_id: int):
    """Show detailed balance calculation"""
    return {
        "invoices": [...],
        "payments": [...],
        "credit_notes": [...],
        "net_balance": ...
    }
```

#### 4. **Frontend: Disable Caching สำหรับ Financial Data**
```javascript
// api/client.js
const financialAPI = axios.create({
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate'
  }
});
```

---

## 📊 ข้อมูลที่ควร Collect ก่อนแก้ไข

1. Screenshot หน้า Dashboard ที่แสดงยอด 5400
2. Network tab ใน DevTools - ดู API response
3. Console logs - ดู error messages
4. Database query ผลลัพธ์:
   ```sql
   SELECT * FROM invoices WHERE house_id = 3;
   SELECT * FROM income_transactions WHERE house_id = 3;
   SELECT * FROM payin_reports WHERE house_id = 3;
   ```

---

## ⏭️ Next Steps

### สิ่งที่ควรทำต่อ:

1. ✅ **User ลอง Clear Browser Cache + Reload**
2. ✅ **รัน script ตรวจสอบ invoices/transactions**
3. ✅ **ดู Network tab ว่า API ส่งข้อมูลอะไรมา**
4. ✅ **ถ้าปัญหายังมี → ส่ง screenshot + API response มา**

### คำถามสำหรับ User:

1. คุณเคย **รัน migration หรือ seed script** ระหว่าง 2 session หรือไม่?
2. คุณ **logout แล้ว login ใหม่** หรือแค่ refresh?
3. Balance **1800** และ **5400** แสดงที่ไหน? (Dashboard, Statement, Invoice?)
4. มี **error messages** ใน Console หรือไม่?

---

## 🔐 Safety Measures ที่ควรทำ

### ป้องกันปัญหาซ้ำ:

1. **Database Backup Schedule**
   ```bash
   # Daily backup at 2 AM
   0 2 * * * pg_dump -U postgres moobaan_smart > /backups/daily_$(date +\%Y\%m\%d).sql
   ```

2. **Audit Log สำหรับ Data Changes**
   ```python
   # Track who modified what, when
   class AuditLog(Base):
       id = Column(Integer, primary_key=True)
       user_id = Column(Integer)
       action = Column(String)  # CREATE, UPDATE, DELETE
       table_name = Column(String)
       record_id = Column(Integer)
       old_value = Column(JSON)
       new_value = Column(JSON)
       timestamp = Column(DateTime)
   ```

3. **Frontend API Response Caching Strategy**
   - ใช้ React Query หรือ SWR
   - Set proper `staleTime` และ `cacheTime`
   - Invalidate cache เมื่อมีการเปลี่ยนแปลงข้อมูล

---

## 🎓 สรุป

**สถานะปัจจุบัน:**
- Database connection: ✅ ถูกต้อง
- Schema: ✅ ครบถ้วน (แต่ไม่มี balance column)
- Data: ⚠️ บ้าน 28/1 มีอยู่แต่ไม่มี payin reports
- Root cause: 🔍 **ยังไม่ทราบแน่ชัด** - ต้องข้อมูลเพิ่มเติมจาก user

**แนวทางแก้ไข:**
1. Clear browser cache (immediate)
2. ตรวจสอบ API responses (debugging)
3. เพิ่ม logging & monitoring (long-term)

**รอ User ดำเนินการ:**
- Clear cache & reload
- ส่ง screenshot + Network tab data
- รายงานผลว่ายังเห็นปัญหาหรือไม่
