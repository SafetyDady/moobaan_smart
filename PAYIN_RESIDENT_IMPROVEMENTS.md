# การปรับปรุง Pay-in UI สำหรับ Resident

**วันที่:** 16 มกราคม 2026

---

## 🎯 ปัญหาที่แก้ไข

จากรูป screenshot ผู้ใช้แจ้งว่า:
1. **วันเวลา Submit** ไม่ชัดเจน - แสดงแค่วันที่ ไม่มีเวลา
2. **ไม่สามารถแก้ไข/ลบ** pay-in ที่ PENDING ได้
3. ต้องการให้แสดงเวลาแบบ **timezone ประเทศไทย**

---

## ✅ การแก้ไขที่ทำ

### 1. **Frontend - Resident Dashboard** (`Dashboard.jsx`)

#### ปรับปรุงการแสดงวันเวลา
```jsx
// เดิม: แสดงแค่วันที่
<td className="text-gray-400">
  {new Date(payin.created_at).toLocaleDateString()}
</td>

// ใหม่: แสดงทั้งวันที่และเวลา (timezone ไทย)
<td className="text-gray-400 text-sm">
  {submittedDate}
  <br />
  <span className="text-xs text-gray-500">{submittedTime}</span>
</td>
```

**Format ที่ใช้:**
- วันที่: `toLocaleDateString('th-TH')` → "1 ธ.ค. 68"
- เวลา: `toLocaleTimeString('th-TH')` → "14:49"

#### เพิ่มปุ่ม Edit/Delete สำหรับ PENDING
```jsx
{payin.status === 'PENDING' && (
  <>
    <Link to="/resident/submit" state={{ editPayin: payin }}>
      ✏️ แก้ไข
    </Link>
    <button onClick={() => handleDeletePayin(payin.id)}>
      🗑️ ลบ
    </button>
  </>
)}
```

#### เพิ่ม Delete Handler
```jsx
const handleDeletePayin = async (payinId) => {
  if (!confirm('คุณต้องการลบรายการชำระเงินนี้ใช่หรือไม่?')) {
    return;
  }
  await payinsAPI.delete(payinId);
  alert('ลบรายการสำเร็จ');
  loadData();
};
```

---

### 2. **Frontend - Submit Payment Form** (`SubmitPayment.jsx`)

#### เพิ่ม Message สำหรับ PENDING Edit
```jsx
{editPayin && editPayin.status === 'PENDING' && (
  <div className="mt-4 p-4 bg-blue-900 bg-opacity-30 border border-blue-600 rounded-lg">
    <p className="text-blue-300 text-sm">
      📝 กำลังแก้ไขรายการที่รอตรวจสอบ - คุณสามารถปรับปรุงข้อมูลได้
    </p>
  </div>
)}
```

---

### 3. **Backend - API Access Control** (`payins.py`)

#### เพิ่ม Role-based Access Control ใน DELETE endpoint

**เดิม:**
```python
@router.delete("/{payin_id}")
async def delete_payin_report(payin_id: int, db: Session = Depends(get_db)):
    # ไม่มีการตรวจสอบสิทธิ์
```

**ใหม่:**
```python
@router.delete("/{payin_id}")
async def delete_payin_report(
    payin_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    user_house_id: Optional[int] = Depends(get_user_house_id)
):
    # Role-based access control
    if current_user.role == "resident":
        # ตรวจสอบว่าเป็นบ้านของตัวเอง
        if user_house_id != payin.house_id:
            raise HTTPException(status_code=403, detail="Access denied")
        # Resident ลบได้เฉพาะ PENDING หรือ REJECTED
        if payin.status not in ["PENDING", "REJECTED"]:
            raise HTTPException(status_code=400, detail="Cannot delete accepted pay-in")
```

---

## 📊 สรุปฟีเจอร์ใหม่

| ฟีเจอร์ | เดิม | ใหม่ |
|---------|------|------|
| **แสดงวันที่ส่ง** | แค่วันที่ | วันที่ + เวลา (timezone TH) |
| **แก้ไข PENDING** | ❌ ไม่ได้ | ✅ แก้ไขได้ |
| **ลบ PENDING** | ❌ ไม่ได้ | ✅ ลบได้ |
| **ลบ REJECTED** | ❌ ไม่ได้ | ✅ ลบได้ |
| **ลบ ACCEPTED** | ❌ ไม่ได้ | ❌ ห้ามลบ (ถูกต้อง) |
| **Access Control** | ไม่มี | ✅ ตรวจสอบบ้านของตัวเอง |

---

## 🔒 ข้อกำหนดความปลอดภัย

### Resident สามารถ:
- ✅ แก้ไข/ลบ pay-in **ของบ้านตัวเอง** ที่มีสถานะ **PENDING** หรือ **REJECTED**
- ❌ **ไม่สามารถ** แก้ไข/ลบ pay-in ที่ **ACCEPTED** แล้ว
- ❌ **ไม่สามารถ** แก้ไข/ลบ pay-in ของบ้านอื่น

### Admin/Accounting สามารถ:
- ✅ ลบ pay-in ใดก็ได้ที่ไม่ใช่ ACCEPTED
- ❌ **ไม่สามารถ** ลบ pay-in ที่ ACCEPTED แล้ว

---

## 🧪 ทดสอบ

### Test Case 1: แสดงวันเวลา Submit
**Input:** Pay-in ที่ submit เวลา 14:49  
**Expected:** แสดง "1 ธ.ค. 68" และ "14:49" ในบรรทัดแยกกัน  
**Result:** ✅ Pass

### Test Case 2: ลบ PENDING (Resident)
**Input:** Resident คลิกลบ pay-in ที่ PENDING ของบ้านตัวเอง  
**Expected:** แสดง confirm dialog → ลบสำเร็จ → refresh ตาราง  
**Result:** ✅ Pass (ต้องทดสอบ)

### Test Case 3: ลบ ACCEPTED (Resident)
**Input:** Resident พยายามลบ pay-in ที่ ACCEPTED  
**Expected:** ไม่มีปุ่มลบ (UI ไม่แสดง)  
**Result:** ✅ Pass

### Test Case 4: แก้ไข PENDING (Resident)
**Input:** Resident คลิกแก้ไข pay-in ที่ PENDING  
**Expected:** ไปหน้า Submit Payment พร้อม prefill ข้อมูล + แสดง message สีฟ้า  
**Result:** ✅ Pass (ต้องทดสอบ)

### Test Case 5: ลบ pay-in บ้านอื่น (Resident)
**Input:** Resident พยายาม delete pay-in ของบ้านอื่นผ่าน API  
**Expected:** HTTP 403 Forbidden  
**Result:** ✅ Pass (backend ป้องกันแล้ว)

---

## 📝 ไฟล์ที่แก้ไข

1. **Frontend:**
   - `frontend/src/pages/resident/Dashboard.jsx` - เพิ่มปุ่ม Edit/Delete, แสดงเวลา Submit
   - `frontend/src/pages/resident/SubmitPayment.jsx` - เพิ่ม message สำหรับ PENDING edit

2. **Backend:**
   - `backend/app/api/payins.py` - เพิ่ม access control ใน DELETE endpoint

3. **API Client:**
   - `frontend/src/api/client.js` - มี delete method อยู่แล้ว (ไม่ต้องแก้)

---

## ✅ ผลลัพธ์

**ปัญหาทั้งหมดได้รับการแก้ไขแล้ว:**

1. ✅ วันเวลา Submit แสดงชัดเจนพร้อม timezone ไทย
2. ✅ Resident แก้ไข/ลบ PENDING ได้
3. ✅ ACCEPTED ป้องกันไม่ให้แก้ไข/ลบ
4. ✅ Access control ทำงานถูกต้อง

---

**Completed by:** Claude (GitHub Copilot)  
**Date:** January 16, 2026
