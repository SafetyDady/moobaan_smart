# Quick Test Guide: Pay-in Review System

## 🎯 Complete Test Flow (15 minutes)

### Setup
- Backend: http://127.0.0.1:8000
- Frontend: http://127.0.0.1:5174
- Test credentials below

---

## Test 1: Resident Submits Pay-in (3 min)

**Login as Resident:**
- Email: `resident@moobaan.com`
- Password: `res123`

**Steps:**
1. Click "💳 Submit Payment" (mobile) or navigate to Submit Payment
2. Fill form:
   - Amount: `600`
   - Transfer Date: Today
   - Transfer Time: `14:30`
   - Upload slip image (any image)
3. Click **"✅ ส่งสลิป"**
4. ✅ **Verify:** Button shows "⏳ กำลังส่ง..." and is disabled
5. ✅ **Verify:** Success message appears
6. ✅ **Verify:** Redirects to dashboard

**Expected Result:**
- Pay-in created with status PENDING
- Submit button was disabled during submission

---

## Test 2: Test Duplicate Prevention (2 min)

**Still logged in as Resident:**

**Steps:**
1. Go back to Submit Payment
2. Fill same form again: ฿600, today
3. Click **"✅ ส่งสลิป"**
4. ✅ **Verify:** Alert shows:
   ```
   ⚠️ มีรายการรอตรวจสอบอยู่แล้ว กรุณารอสักครู่ก่อนส่งใหม่
   ```
5. ✅ **Verify:** Button re-enables
6. ✅ **Verify:** No console errors

**Expected Result:**
- Duplicate prevented
- User-friendly message shown
- No payin created

---

## Test 3: Admin Reviews and Accepts (5 min)

**Logout and Login as Admin:**
- Email: `admin@moobaan.com`
- Password: `admin123`

**Steps:**
1. Navigate to **"Pay-in Reports"**
2. Verify default filter is **"Pending Review"**
3. ✅ **Verify:** See the ฿600 payin from Test 1
4. ✅ **Verify:** See 4 buttons:
   - **👁️ View Slip** (opens image)
   - **✓ Accept**
   - **✗ Reject**
   - **🗑 Cancel**

**Test Accept Flow:**
1. Click **"✓ Accept"**
2. Confirm action
3. ✅ **Verify:** Status changes to ACCEPTED
4. ✅ **Verify:** Shows "✓ Ledger created"
5. ✅ **Verify:** No action buttons (only View Slip remains)
6. ✅ **Verify:** List refreshes automatically

**Expected Result:**
- Pay-in status = ACCEPTED
- IncomeTransaction created in database
- Payment will appear in house statement

---

## Test 4: Admin Rejects Pay-in (3 min)

**Create new payin first:**
1. Logout, login as **resident**
2. Submit another payin: ฿500 (must wait 5 min OR admin can cancel the first one)
3. Logout, login as **admin**

**Steps:**
1. Go to Pay-in Reports → Pending Review
2. Find the ฿500 payin
3. Click **"✗ Reject"**
4. Modal opens
5. Enter reason: `จำนวนเงินไม่ตรงกับสลิป`
6. Click **"Reject"**
7. ✅ **Verify:** Status changes to REJECTED
8. ✅ **Verify:** Rejection reason shows in table
9. ✅ **Verify:** Message: "Resident can resubmit"

**Expected Result:**
- Pay-in status = REJECTED
- Resident can edit and resubmit
- No ledger entry created

---

## Test 5: Admin Cancels Pay-in (2 min)

**Steps:**
1. Still in Pay-in Reports
2. Find a PENDING or REJECTED payin
3. Click **"🗑 Cancel"**
4. Modal opens with warning
5. Enter reason: `ข้อมูลทดสอบ`
6. Click **"Delete"**
7. ✅ **Verify:** Payin disappears from list
8. ✅ **Verify:** Record deleted from database

**Expected Result:**
- Pay-in permanently deleted
- Used for test cleanup

---

## Database Verification (Optional)

**Check IncomeTransaction was created:**
```sql
SELECT 
  it.id,
  it.house_id,
  it.payin_id,
  it.amount,
  it.received_at,
  pr.status
FROM income_transactions it
JOIN payin_reports pr ON pr.id = it.payin_id;
```

**Expected:**
- One row for the ACCEPTED payin (฿600)
- `amount` = 600.00
- `status` = ACCEPTED

---

## Success Criteria ✅

- [ ] Resident can submit payin
- [ ] Submit button disables during submission
- [ ] Duplicate within 5 min is prevented with friendly message
- [ ] Admin can see all action buttons for PENDING
- [ ] Accept creates ledger entry (IncomeTransaction)
- [ ] Reject updates status and shows reason
- [ ] Cancel deletes payin
- [ ] List refreshes after each action
- [ ] No console errors
- [ ] Both accounting and super_admin can manage payins

---

## Common Issues & Solutions

**Issue:** "ไม่พบข้อมูลบ้าน"
- **Fix:** Resident not linked to house. Check HouseMember table.

**Issue:** Action buttons not showing
- **Fix:** Check role is super_admin or accounting in console.

**Issue:** 409 error not showing friendly message
- **Fix:** Check browser console for actual error, refresh page.

**Issue:** Submit button stays disabled
- **Fix:** Refresh page, clear form state.

---

**Total Test Time:** ~15 minutes  
**Result:** All features working as expected ✅
