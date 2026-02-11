# 📋 Mobile Test Plan - Phase 1.3

## 🎯 Acceptance Criteria

Before considering Phase 1.3 "production ready", the following must pass:

### ✅ Build & Deploy
- [ ] Vercel build passes without errors
- [ ] Frontend deploys successfully
- [ ] No console errors on load

### ✅ Device Detection
- [ ] Mobile devices (iPhone/Android) → Mobile UI
- [ ] Desktop browsers → Desktop UI
- [ ] Desktop resized <768px → Still Desktop UI (not mobile)
- [ ] Tablets → Mobile UI (if touch device)

### ✅ Mobile Flow (T1: iPhone Safari)
- [ ] Login as resident
- [ ] Dashboard loads with cards (not tables)
- [ ] Bottom navigation visible and functional
- [ ] Sticky balance card at top
- [ ] Tap "ชำระเงินเลย" → Navigate to Submit Payment
- [ ] Camera button opens camera
- [ ] Take photo → Preview appears
- [ ] Select date/time with native pickers
- [ ] Submit → Success (no errors)

### ✅ Mobile Flow (T2: Android Chrome)
- [ ] All T1 tests pass
- [ ] Rotate to landscape → Layout adjusts
- [ ] Open keyboard → Submit button not blocked
- [ ] File upload works

### ✅ File Validation
- [ ] Upload image <8MB → Success
- [ ] Upload image >8MB → Error message
- [ ] Upload non-image → Error message
- [ ] Error message displays in Thai

### ✅ Desktop Regression (T3)
- [ ] Admin/Accounting → Desktop layout unchanged
- [ ] Resident on desktop → Desktop version (sidebar, tables)
- [ ] No mobile UI appears on desktop

### ✅ UI/UX
- [ ] No horizontal scrolling on mobile
- [ ] All touch targets ≥48px
- [ ] Bottom nav doesn't overlap content
- [ ] Keyboard doesn't block submit button (iOS)
- [ ] Logout button works correctly

---

## 🧪 Test Cases

### **T1: iPhone Safari - Happy Path**

**Prerequisites:**
- iPhone (any model)
- Safari browser
- Account: `resident` / `res123`

**Steps:**
1. Open https://moobaan-smart.vercel.app
2. Login with resident credentials
3. Verify bottom navigation appears (🏠 หน้าหลัก, 💳 ชำระเงิน)
4. Verify dashboard shows:
   - Sticky red balance card at top
   - 2-column quick stats
   - Invoice cards (not table)
   - Payment history cards
5. Scroll down → Balance card stays at top
6. Tap "ชำระเงินเลย" button
7. Verify Submit Payment page loads
8. Enter amount: `3000`
9. Select date: Today
10. Select time: Current time (native picker)
11. Tap "ถ่ายรูปสลิป"
12. Grant camera permission
13. Take photo
14. Verify preview appears
15. Tap "ส่งสลิปเลย"
16. Verify success message
17. Verify redirect to dashboard

**Expected Results:**
- ✅ All steps complete without errors
- ✅ Native pickers work smoothly
- ✅ Camera opens and preview works
- ✅ No UI overlap or blocking

---

### **T2: Android Chrome - Extended**

**Prerequisites:**
- Android phone
- Chrome browser
- Account: `resident` / `res123`

**Steps:**
1-17. Same as T1
18. Rotate to landscape
19. Verify layout adjusts
20. Rotate back to portrait
21. Go to Submit Payment
22. Tap amount field
23. Verify keyboard opens
24. Verify submit button still visible/accessible
25. Close keyboard
26. Try uploading file >8MB
27. Verify error message in Thai

**Expected Results:**
- ✅ Landscape mode works
- ✅ Keyboard doesn't block buttons
- ✅ File validation works
- ✅ Error messages in Thai

---

### **T3: Desktop Regression**

**Prerequisites:**
- Desktop/Laptop browser
- Accounts: `admin`/`admin123`, `resident`/`res123`

**Steps:**
1. Login as `admin`
2. Verify sidebar layout (not bottom nav)
3. Verify tables (not cards)
4. Navigate all admin pages
5. Logout
6. Login as `resident`
7. Verify desktop version (sidebar, tables)
8. Resize browser to <768px
9. Verify still desktop version (not mobile)
10. Logout

**Expected Results:**
- ✅ Admin sees desktop UI
- ✅ Resident on desktop sees desktop UI
- ✅ Resize doesn't trigger mobile UI
- ✅ No regression in functionality

---

### **T4: File Validation**

**Prerequisites:**
- Mobile device
- Test files:
  - Small image (<1MB)
  - Large image (>8MB)
  - PDF file

**Steps:**
1. Go to Submit Payment
2. Upload small image → ✅ Preview appears
3. Clear and upload large image → ❌ Error: "ไฟล์ใหญ่เกินไป"
4. Clear and upload PDF → ❌ Error: "กรุณาเลือกไฟล์รูปภาพเท่านั้น"

**Expected Results:**
- ✅ Small images work
- ✅ Large images rejected with Thai error
- ✅ Non-images rejected with Thai error

---

### **T5: Keyboard Overlap (iOS)**

**Prerequisites:**
- iPhone
- Safari

**Steps:**
1. Go to Submit Payment
2. Tap amount field
3. Keyboard opens
4. Scroll down
5. Verify submit button visible
6. Tap submit button (should be accessible)

**Expected Results:**
- ✅ Submit button not blocked by keyboard
- ✅ Can scroll to reach button if needed
- ✅ Extra padding added when keyboard open

---

## 📸 Required Screenshots

Before marking Phase 1.3 complete, provide:

### **iPhone Safari (3 screenshots)**
1. Dashboard - Top section (balance card + stats)
2. Submit Payment - With camera preview
3. Bottom navigation - Active state

### **Android Chrome (3 screenshots)**
1. Dashboard - Invoice cards
2. Submit Payment - Native time picker open
3. Error message - File too large

### **Desktop (2 screenshots)**
1. Admin dashboard - Sidebar layout
2. Resident dashboard - Desktop version

---

## 🚨 Known Issues & Limitations

### **Phase 1 Limitations (Expected)**
- File upload is mocked (no real S3 upload)
- No image compression
- No OCR for slip amount
- No push notifications

### **Potential Issues to Watch**
- iPad detection (might show desktop or mobile)
- Older Android browsers (pointer: coarse might not work)
- Very small phones (<360px width)

---

## ✅ Gate Criteria

Phase 1.3 is "production ready" when:

1. ✅ Vercel build passes
2. ✅ T1 (iPhone) passes completely
3. ✅ T2 (Android) passes completely
4. ✅ T3 (Desktop regression) passes
5. ✅ T4 (File validation) passes
6. ✅ No bottom nav overlap
7. ✅ No keyboard blocking buttons
8. ✅ All screenshots provided

---

## 🔧 Fixes Applied

### **Fix 1: Device Detection** ✅
- Added `pointer: coarse` check
- Desktop resize <768px won't trigger mobile UI
- Touch capability required for mobile detection

**Code:**
```javascript
const isTouchDevice = window.matchMedia("(pointer: coarse)").matches;
return isMobileUA || (isSmallScreen && isTouchDevice);
```

### **Fix 2: File Validation** ✅
- Max file size: 8MB
- File type validation (images only)
- Error messages in Thai

**Code:**
```javascript
if (file.size > MAX_FILE_SIZE) {
  setError(`ไฟล์ใหญ่เกินไป (${sizeMB}MB) กรุณาเลือกไฟล์ที่เล็กกว่า 8MB`);
  return;
}
```

### **Fix 3: iOS Keyboard Overlap** ✅
- Detect keyboard open via visualViewport
- Add extra padding when keyboard visible
- Ensure submit button accessible

**Code:**
```javascript
const isOpen = window.visualViewport.height < window.innerHeight * 0.75;
setKeyboardOpen(isOpen);
// ...
<div className={`p-4 ${keyboardOpen ? 'pb-96' : ''}`}>
```

---

## 📝 Test Execution Log

| Test | Device | Browser | Status | Notes |
|------|--------|---------|--------|-------|
| T1 | iPhone 13 | Safari | ⏳ Pending | |
| T2 | Samsung S21 | Chrome | ⏳ Pending | |
| T3 | MacBook | Chrome | ⏳ Pending | |
| T4 | iPhone 13 | Safari | ⏳ Pending | |
| T5 | iPhone 13 | Safari | ⏳ Pending | |

---

**Status:** 🔧 Fixes Applied - Ready for Testing  
**Next Step:** Push to GitHub → Deploy → Test on real devices  
**Target:** All tests pass before production release

---

*Test Plan created: 2025-01-12*  
*Last updated: 2025-01-12*
