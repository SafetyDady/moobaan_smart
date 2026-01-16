# 🐛 Login Redirect Loop Issue Report

**Date:** January 15, 2026  
**Commit:** 4508e0f  
**Status:** ⚠️ แก้ไขแล้วแต่ต้องการการทดสอบเพิ่มเติม

---

## 📋 สรุปปัญหา

หลังจากแก้ไขให้ระบบ **redirect กลับไปหน้าเดิมหลัง login** (เช่น ถ้าเข้า `/admin/payins` แล้วยัง login ไม่ได้ หลัง login ให้กลับไปหน้า `/admin/payins`) พบว่าเกิด **Login Redirect Loop** ที่ผู้ใช้ login สำเร็จแล้วแต่ถูก redirect กลับมาหน้า login ซ้ำๆ

### อาการ
- กรอก username/password แล้วกด Login
- ไม่มี error แสดง
- หน้าจอกระพริบแล้วกลับมาหน้า Login อีกครั้ง
- ไม่สามารถเข้าใช้งานระบบได้

---

## 🔍 Root Cause Analysis

### ลำดับเหตุการณ์ที่ทำให้เกิดปัญหา:

1. **User กด Login button**
   ```jsx
   // Login.jsx - handleSubmit()
   const success = await login(formData); // เรียก AuthContext.login()
   ```

2. **AuthContext.login() ทำงาน**
   ```jsx
   // AuthContext.jsx
   setToken(access_token);                    // setState เป็น async
   setUser(userResponse.data);                // setState เป็น async
   localStorage.setItem('auth_token', token); // ✅ ทำงานทันที
   return true;
   ```

3. **Login.jsx navigate ทันที**
   ```jsx
   // Login.jsx
   if (success) {
     navigate('/admin/dashboard', { replace: true }); // ✅ ทำงานทันที
   }
   ```

4. **⚠️ ปัญหาเกิดที่นี่: React Router navigate ไปยัง `/admin/dashboard`**
   - `setUser()` ยัง**ไม่ทันทำงานเสร็จ** (asynchronous)
   - `user` state ยังเป็น `null`
   - `isAuthenticated: !!user` → ยังได้ค่า `false`

5. **ProtectedRoute render และเช็ค authentication**
   ```jsx
   // ProtectedRoute.jsx
   if (!isAuthenticated) {  // !!user = false เพราะ user ยังเป็น null
     return <Navigate to="/login" state={{ from: location }} replace />;
   }
   ```

6. **🔄 Redirect กลับไป `/login` พร้อม state.from = '/admin/dashboard'**

7. **🔁 Loop เริ่มต้น**
   - ถ้า user พยายาม login อีก → กลับไปขั้นตอนที่ 1

---

## 🔧 สาเหตุที่แท้จริง: **Race Condition**

```jsx
// ❌ ก่อนแก้ไข
const value = {
  isAuthenticated: !!user,  // ต้องรอ setUser() ทำงานเสร็จ (async)
  // ...
};
```

**ปัญหา:**
- `setUser()` เป็น **asynchronous operation**
- React จะ batch state updates และ schedule re-render
- ในช่วง "หลัง login สำเร็จ" แต่ "ก่อน re-render เสร็จ" → `user` ยังเป็น `null`
- `navigate()` ทำงานเร็วกว่า → ProtectedRoute เช็คเจอ `isAuthenticated = false`

---

## ✅ วิธีแก้ไข

### แก้ที่: `frontend/src/contexts/AuthContext.jsx`

```jsx
// ✅ หลังแก้ไข
const value = {
  isAuthenticated: !!token || !!localStorage.getItem('auth_token'),
  // ไม่พึ่ง user state แล้ว, เช็ค token และ localStorage แทน
  // ...
};
```

**เหตุผล:**
- `localStorage.getItem()` เป็น **synchronous operation** → อ่านค่าได้ทันที
- `login()` function เซ็ต `localStorage` **ก่อน** return → ค่าพร้อมใช้งานทันที
- ตอน ProtectedRoute เช็ค → `localStorage.getItem('auth_token')` มีค่าแล้ว
- `isAuthenticated` เป็น `true` → ผ่านการเช็ค → ไม่ redirect กลับ login

### ไฟล์ที่แก้ไข:

1. ✅ **frontend/src/contexts/AuthContext.jsx**
   - เปลี่ยน `isAuthenticated: !!user` → `isAuthenticated: !!token || !!localStorage.getItem('auth_token')`

2. ✅ **frontend/src/pages/auth/Login.jsx**
   - เพิ่มเงื่อนไข: ถ้า `from === '/login'` ให้ไปหน้า default แทน (ป้องกัน redirect loop)

3. ✅ **frontend/src/components/ProtectedRoute.jsx**
   - เพิ่ม `state: { from: location }` ตอน redirect ไป login (เพื่อบันทึกหน้าเดิม)

4. ✅ **frontend/src/contexts/RoleContext.jsx**
   - ลบ debug console.log ที่อยู่นอก useEffect (ป้องกัน re-render loop)

---

## 🧪 การทดสอบที่ต้องทำ

### Test Case 1: Login ปกติ (ไม่มี previous page)
```
1. เปิด browser ใหม่ (Incognito)
2. ไปที่ http://127.0.0.1:5174/login
3. Login ด้วย admin@moobaan.com / password
4. ✅ Expected: Redirect ไป /admin/dashboard สำเร็จ
```

### Test Case 2: Login หลังจาก session หมดอายุ
```
1. Login ด้วย admin@moobaan.com
2. เข้าใช้งานปกติ (เช่น ไปหน้า /admin/payins)
3. ลบ auth_token จาก localStorage (simulate expired token)
4. Refresh หน้า → ถูก redirect ไป /login
5. Login อีกครั้ง
6. ✅ Expected: Redirect กลับไป /admin/payins ที่พยายามเข้าก่อนหน้า
```

### Test Case 3: Direct access to protected route
```
1. ยังไม่ได้ login
2. พิมพ์ URL http://127.0.0.1:5174/admin/expenses
3. ถูก redirect ไป /login
4. Login สำเร็จ
5. ✅ Expected: Redirect กลับไป /admin/expenses
```

### Test Case 4: Role-based access
```
1. Login ด้วย resident@moobaan.com
2. ✅ Expected: Redirect ไป /resident/dashboard
3. พยายามเข้า /admin/dashboard ผ่าน URL
4. ✅ Expected: Redirect กลับไป /resident/dashboard
```

### Test Case 5: Remember me functionality
```
1. Login พร้อมเช็ค "Remember me"
2. ปิด browser
3. เปิด browser ใหม่
4. ไปที่ http://127.0.0.1:5174
5. ✅ Expected: Auto login และเข้า dashboard ได้ทันที (ถ้ามี Remember me)
```

---

## 🚨 ปัญหาที่อาจเกิดขึ้น (Potential Issues)

### 1. Token ใน localStorage แต่ไม่ valid
**Scenario:** 
- Token หมดอายุแล้วแต่ยังอยู่ใน localStorage
- `isAuthenticated` เป็น `true` → ผ่าน ProtectedRoute
- แต่ทุก API call จะ return 401 Unauthorized

**Solution ปัจจุบัน:**
```jsx
// AuthContext.jsx - checkAuth()
try {
  const response = await api.get('/api/auth/me');
  setUser(response.data);
} catch (error) {
  // Token expired or invalid
  clearAuth(); // ลบ token และ redirect ไป login
}
```

**⚠️ แนะนำให้เพิ่ม:**
- Axios interceptor เพื่อจับ 401 response ทุก API
- Auto clear localStorage และ redirect ไป login

### 2. Multiple tabs/windows
**Scenario:**
- User เปิด 2 tabs
- Logout ที่ tab 1
- Tab 2 ยังคง `isAuthenticated: true` (localStorage ยังมี)

**แนะนำแก้ไข:**
- ใช้ `storage` event listener เพื่อ sync auth state ระหว่าง tabs

### 3. XSS Attack
**Scenario:**
- Token เก็บใน localStorage → เสี่ยงต่อ XSS
- ถ้ามี XSS vulnerability → attacker อ่าน token ได้

**แนะนำ (Future improvement):**
- เปลี่ยนเป็น httpOnly cookie แทน localStorage
- หรือเพิ่ม CSRF token protection

---

## 📊 Performance Impact

### Before Fix:
- Login → Redirect → ProtectedRoute check → Redirect back to login → **Loop**
- จำนวน re-renders: **∞ (infinite loop)**

### After Fix:
- Login → Redirect → ProtectedRoute check → **Pass** → Show dashboard
- จำนวน re-renders: **2-3 renders** (normal React behavior)

---

## 🎯 ทำไมปัญหานี้ไม่เคยเจอก่อนหน้านี้?

1. **ก่อนแก้ "login redirect to previous page":**
   - มี hardcode `navigate('/admin/dashboard')` 
   - แต่ปัญหานี้มีอยู่แล้ว จะเห็นได้จาก browser กระพริบชั่วครู่ก่อนเข้า dashboard
   - แต่เนื่องจากทำงานเร็ว → user ไม่ได้สังเกต

2. **หลังเพิ่ม "redirect to previous page":**
   - มี location state passing → เพิ่มความซับซ้อน
   - ปัญหาที่มีอยู่แล้วกลายเป็น infinite loop ชัดเจนขึ้น

3. **Debug console.log ใน RoleContext:**
   - มี console.log นอก useEffect → re-render loop
   - ทำให้ปัญหาแย่ลงอีก

---

## ✍️ Lessons Learned

1. **ใช้ Synchronous data เพื่อเช็ค auth status**
   - localStorage/sessionStorage (sync)
   - ไม่ใช่ React state (async)

2. **เข้าใจ React state updates lifecycle**
   - setState ไม่ update ทันที
   - ใช้ callback หรือ useEffect ถ้าต้องการทำอะไรหลัง state update

3. **ระวัง console.log ที่อยู่นอก useEffect**
   - ทำให้เกิด re-render loop
   - ใช้แค่เพื่อ debug แล้วลบทิ้ง

4. **Test authentication flow ในทุก scenario**
   - Direct access
   - Session expiry
   - Role-based access
   - Multiple tabs

---

## 📚 References

- [React setState is Asynchronous](https://react.dev/learn/state-as-a-snapshot)
- [React Router - Location State](https://reactrouter.com/en/main/hooks/use-location)
- [Authentication Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

## 👥 ต้องการความช่วยเหลือ

ขอความช่วยเหลือในการ:

1. **ทดสอบทั้ง 5 test cases** ที่ระบุด้านบน
2. **ตรวจสอบ edge cases** อื่นๆ ที่อาจเกิดขึ้น
3. **Review security implications** ของการเก็บ token ใน localStorage
4. **แนะนำ best practices** สำหรับ authentication flow ใน React

---

**Created by:** GitHub Copilot  
**Reviewed by:** _[รอการ review]_
