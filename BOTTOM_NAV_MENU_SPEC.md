# 📱 Bottom Navigation Menu - Specification

**Date:** January 19, 2026  
**Current State:** 2 menu items (หน้าหลัก, ชำระเงิน)  
**Proposed:** 5 menu items for better navigation

---

## 🔍 Current Menu (ปัจจุบัน)

**File:** `frontend/src/pages/resident/mobile/MobileLayout.jsx` (Line 31-44)

```javascript
const navItems = [
  { 
    path: '/resident/dashboard', 
    icon: '🏠', 
    label: 'หน้าหลัก',
    activeIcon: '🏠'
  },
  { 
    path: '/resident/submit', 
    icon: '💳', 
    label: 'ชำระเงิน',
    activeIcon: '💳'
  },
];
```

**Menu Items:**
1. 🏠 **หน้าหลัก** → `/resident/dashboard`
2. 💳 **ชำระเงิน** → `/resident/submit`

**Issues:**
- ❌ เข้าถึงใบแจ้งหนี้ยาก (ต้อง scroll ใน dashboard)
- ❌ ดูประวัติการส่งสลิปยาก (ต้อง scroll ใน dashboard)
- ❌ ไม่มี quick access ไปหน้าโปรไฟล์
- ❌ แค่ 2 เมนู ไม่เต็มศักยภาพ

---

## ✅ Proposed Menu (เสนอเพิ่ม)

### Option 1: 5 Menu Items (แนะนำ) ⭐

```javascript
const navItems = [
  { 
    path: '/resident/dashboard', 
    icon: '🏠', 
    label: 'หน้าหลัก',
    activeIcon: '🏠'
  },
  { 
    path: '/resident/invoices', 
    icon: '📄', 
    label: 'ใบแจ้งหนี้',
    activeIcon: '📄'
  },
  { 
    path: '/resident/submit', 
    icon: '📸', 
    label: 'ส่งสลิป',
    activeIcon: '📸'
  },
  { 
    path: '/resident/payments', 
    icon: '📋', 
    label: 'ประวัติ',
    activeIcon: '📋'
  },
  { 
    path: '/resident/profile', 
    icon: '👤', 
    label: 'โปรไฟล์',
    activeIcon: '👤'
  },
];
```

**Menu Items:**
1. 🏠 **หน้าหลัก** → Dashboard (Summary + Overview)
2. 📄 **ใบแจ้งหนี้** → Invoice list with filters
3. 📸 **ส่งสลิป** → Submit payment (camera)
4. 📋 **ประวัติ** → Payment history with filters
5. 👤 **โปรไฟล์** → User profile & settings

**Benefits:**
- ✅ Quick access ทุกหน้าสำคัญ
- ✅ ไม่ต้อง scroll หาเมนู
- ✅ Standard 5-tab pattern (iOS/Android)
- ✅ Center button = primary action (ส่งสลิป)

---

### Option 2: 4 Menu Items (กระชับ)

```javascript
const navItems = [
  { 
    path: '/resident/dashboard', 
    icon: '🏠', 
    label: 'หน้าหลัก'
  },
  { 
    path: '/resident/invoices', 
    icon: '📄', 
    label: 'ใบแจ้งหนี้'
  },
  { 
    path: '/resident/submit', 
    icon: '📸', 
    label: 'ส่งสลิป'
  },
  { 
    path: '/resident/payments', 
    icon: '📋', 
    label: 'ประวัติ'
  },
];
```

**Menu Items:**
1. 🏠 **หน้าหลัก**
2. 📄 **ใบแจ้งหนี้**
3. 📸 **ส่งสลิป**
4. 📋 **ประวัติ**

**Benefits:**
- ✅ Cleaner, less cluttered
- ✅ Larger tap targets
- ✅ Focus on core features

**Trade-off:**
- ⚠️ No profile menu (use header button instead)

---

### Option 3: 3 Menu Items (มินิมอล)

```javascript
const navItems = [
  { 
    path: '/resident/dashboard', 
    icon: '🏠', 
    label: 'หน้าหลัก'
  },
  { 
    path: '/resident/submit', 
    icon: '📸', 
    label: 'ส่งสลิป'
  },
  { 
    path: '/resident/history', 
    icon: '📋', 
    label: 'ประวัติ'
  },
];
```

**Menu Items:**
1. 🏠 **หน้าหลัก** (Dashboard with invoices + payments)
2. 📸 **ส่งสลิป** (Submit payment)
3. 📋 **ประวัติ** (Combined invoices + payments)

**Benefits:**
- ✅ Very simple
- ✅ Largest tap targets
- ✅ Easy to understand

**Trade-off:**
- ⚠️ Less granular navigation
- ⚠️ Combined history page may be confusing

---

## 🎯 Recommended: Option 1 (5 Menu Items)

**Why:**
- ✅ Standard pattern (most apps use 5)
- ✅ Clear separation of concerns
- ✅ Quick access to all features
- ✅ Center button = primary action (best practice)
- ✅ Profile menu for settings/logout

---

## 📐 Menu Structure

### Layout

```
┌─────────────────────────────────────┐
│                                     │
│         Content Area                │
│                                     │
├─────────────────────────────────────┤
│  🏠     📄     📸     📋     👤    │ ← Bottom Nav (64px)
│ หน้าหลัก ใบแจ้งหนี้ ส่งสลิป ประวัติ โปรไฟล์ │
└─────────────────────────────────────┘
```

**Specifications:**
- Height: 64px (iOS guideline)
- Icon size: 24px
- Text size: 12px
- Min tap target: 44px x 44px
- Active color: Primary green (#10b981)
- Inactive color: Gray (#9ca3af)

---

## 🎨 Visual Design

### Active State
```jsx
<div className="flex-1 flex flex-col items-center justify-center min-h-[64px] text-primary-400 bg-gray-750">
  <span className="text-2xl mb-0.5">🏠</span>
  <span className="text-xs font-semibold">หน้าหลัก</span>
</div>
```

### Inactive State
```jsx
<div className="flex-1 flex flex-col items-center justify-center min-h-[64px] text-gray-400 active:bg-gray-750">
  <span className="text-2xl mb-0.5">📄</span>
  <span className="text-xs font-medium">ใบแจ้งหนี้</span>
</div>
```

### Center Button (Primary Action)
```jsx
<div className="flex-1 flex flex-col items-center justify-center min-h-[64px] text-primary-400">
  <div className="w-12 h-12 bg-primary-500 rounded-full flex items-center justify-center mb-1">
    <span className="text-2xl">📸</span>
  </div>
  <span className="text-xs font-medium">ส่งสลิป</span>
</div>
```

---

## 📄 New Pages Required

### 1. Invoice List Page

**Path:** `/resident/invoices`  
**File:** `frontend/src/pages/resident/mobile/InvoiceList.jsx`

**Features:**
- Filter tabs (All, Paid, Unpaid)
- Table view (compact rows)
- Tap to view detail modal
- Summary at top

**Code:**
```jsx
export default function InvoiceList() {
  const [filter, setFilter] = useState('all');
  const { data: invoices } = trpc.invoice.list.useQuery();
  
  const filteredInvoices = invoices?.filter(inv => {
    if (filter === 'paid') return inv.status === 'PAID';
    if (filter === 'unpaid') return inv.status === 'UNPAID';
    return true;
  });
  
  return (
    <MobileLayout>
      <div className="p-4">
        <h1 className="text-xl font-bold text-white mb-4">ใบแจ้งหนี้</h1>
        
        {/* Filter Tabs */}
        <div className="flex gap-2 mb-4">
          {filters.map(f => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={filter === f.id ? 'active' : ''}
            >
              {f.label}
            </button>
          ))}
        </div>
        
        {/* Invoice List */}
        <div className="space-y-2">
          {filteredInvoices?.map(invoice => (
            <InvoiceRow key={invoice.id} invoice={invoice} />
          ))}
        </div>
      </div>
    </MobileLayout>
  );
}
```

---

### 2. Payment History Page

**Path:** `/resident/payments`  
**File:** `frontend/src/pages/resident/mobile/PaymentHistory.jsx`

**Features:**
- Filter tabs (All, Pending, Accepted, Rejected)
- Table view (compact rows)
- Eye icon to view details
- Edit icon for rejected payments
- FAB to add new payment

**Code:**
```jsx
export default function PaymentHistory() {
  const [filter, setFilter] = useState('all');
  const { data: payments } = trpc.payment.list.useQuery();
  
  const filteredPayments = payments?.filter(p => {
    if (filter === 'pending') return p.status === 'PENDING';
    if (filter === 'accepted') return p.status === 'ACCEPTED';
    if (filter === 'rejected') return p.status === 'REJECTED';
    return true;
  });
  
  return (
    <MobileLayout>
      <div className="p-4">
        <h1 className="text-xl font-bold text-white mb-4">ประวัติการส่งสลิป</h1>
        
        {/* Filter Tabs */}
        <div className="flex gap-2 mb-4">
          {filters.map(f => (
            <button key={f.id} onClick={() => setFilter(f.id)}>
              {f.label}
            </button>
          ))}
        </div>
        
        {/* Payment List */}
        <div className="space-y-2">
          {filteredPayments?.map(payment => (
            <PaymentRow key={payment.id} payment={payment} />
          ))}
        </div>
        
        {/* FAB */}
        <button 
          onClick={() => navigate('/resident/submit')}
          className="fixed bottom-20 right-4 w-14 h-14 bg-primary-500 rounded-full"
        >
          <Plus size={24} />
        </button>
      </div>
    </MobileLayout>
  );
}
```

---

### 3. Profile Page

**Path:** `/resident/profile`  
**File:** `frontend/src/pages/resident/mobile/Profile.jsx`

**Features:**
- User info (name, email, house)
- Settings
- Logout button
- Change password
- Notification preferences

**Code:**
```jsx
export default function Profile() {
  const { user, logout } = useAuth();
  const { currentHouseCode } = useRole();
  
  return (
    <MobileLayout>
      <div className="p-4">
        <h1 className="text-xl font-bold text-white mb-4">โปรไฟล์</h1>
        
        {/* User Info */}
        <div className="bg-gray-800 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 bg-primary-500 rounded-full flex items-center justify-center">
              <span className="text-3xl">👤</span>
            </div>
            <div>
              <div className="text-lg font-semibold text-white">{user?.name}</div>
              <div className="text-sm text-gray-400">{user?.email}</div>
              <div className="text-sm text-gray-400">บ้านเลขที่ {currentHouseCode}</div>
            </div>
          </div>
        </div>
        
        {/* Menu Items */}
        <div className="space-y-2">
          <button className="w-full bg-gray-800 p-4 rounded-lg text-left">
            <div className="text-white">เปลี่ยนรหัสผ่าน</div>
          </button>
          
          <button className="w-full bg-gray-800 p-4 rounded-lg text-left">
            <div className="text-white">การแจ้งเตือน</div>
          </button>
          
          <button 
            onClick={logout}
            className="w-full bg-red-900/20 border border-red-700 p-4 rounded-lg text-left"
          >
            <div className="text-red-400">ออกจากระบบ</div>
          </button>
        </div>
      </div>
    </MobileLayout>
  );
}
```

---

## 🛠 Implementation Plan

### Phase 1: Update MobileLayout (30 min)

**File:** `frontend/src/pages/resident/mobile/MobileLayout.jsx`

**Changes:**
1. Update `navItems` array to 5 items
2. Adjust icon styles
3. Add center button special styling

**Code:**
```jsx
const navItems = [
  { path: '/resident/dashboard', icon: '🏠', label: 'หน้าหลัก' },
  { path: '/resident/invoices', icon: '📄', label: 'ใบแจ้งหนี้' },
  { path: '/resident/submit', icon: '📸', label: 'ส่งสลิป', isPrimary: true },
  { path: '/resident/payments', icon: '📋', label: 'ประวัติ' },
  { path: '/resident/profile', icon: '👤', label: 'โปรไฟล์' },
];

// In render:
{navItems.map(item => {
  const isActive = location.pathname === item.path;
  
  if (item.isPrimary) {
    return (
      <Link key={item.path} to={item.path} className="flex-1 flex flex-col items-center justify-center min-h-[64px]">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-1 ${
          isActive ? 'bg-primary-500' : 'bg-gray-700'
        }`}>
          <span className="text-2xl">{item.icon}</span>
        </div>
        <span className={`text-xs ${isActive ? 'text-primary-400 font-semibold' : 'text-gray-400'}`}>
          {item.label}
        </span>
      </Link>
    );
  }
  
  return (
    <Link key={item.path} to={item.path} className={`flex-1 flex flex-col items-center justify-center min-h-[64px] ${
      isActive ? 'text-primary-400 bg-gray-750' : 'text-gray-400'
    }`}>
      <span className="text-2xl mb-0.5">{item.icon}</span>
      <span className={`text-xs ${isActive ? 'font-semibold' : 'font-medium'}`}>
        {item.label}
      </span>
    </Link>
  );
})}
```

---

### Phase 2: Create InvoiceList Page (1 hour)

**File:** `frontend/src/pages/resident/mobile/InvoiceList.jsx`

**Tasks:**
1. Create page component
2. Add filter tabs
3. Add invoice table view
4. Add detail modal
5. Add to App.jsx routes

---

### Phase 3: Create PaymentHistory Page (1 hour)

**File:** `frontend/src/pages/resident/mobile/PaymentHistory.jsx`

**Tasks:**
1. Create page component
2. Add filter tabs (4 tabs)
3. Add payment table view
4. Add FAB button
5. Add to App.jsx routes

---

### Phase 4: Create Profile Page (45 min)

**File:** `frontend/src/pages/resident/mobile/Profile.jsx`

**Tasks:**
1. Create page component
2. Add user info section
3. Add settings menu
4. Add logout button
5. Add to App.jsx routes

---

### Phase 5: Update App.jsx Routes (15 min)

**File:** `frontend/src/App.jsx`

**Add routes:**
```jsx
<Route path="/resident/invoices" element={<InvoiceList />} />
<Route path="/resident/payments" element={<PaymentHistory />} />
<Route path="/resident/profile" element={<Profile />} />
```

---

### Phase 6: Update Dashboard (30 min)

**File:** `frontend/src/pages/resident/mobile/MobileDashboard.jsx`

**Changes:**
1. Keep summary cards at top
2. Add "ดูทั้งหมด" links to invoice/payment sections
3. Show only top 3 items per section
4. Link to dedicated pages

---

## 📊 Comparison

| Aspect | Current (2 items) | Proposed (5 items) | Improvement |
|--------|-------------------|-------------------|-------------|
| **Menu Items** | 2 | 5 | +150% |
| **Quick Access** | Limited | Full | +100% |
| **Navigation Depth** | 2-3 taps | 1 tap | -67% |
| **User Confusion** | Medium | Low | Better |
| **Standard Pattern** | ❌ | ✅ | iOS/Android |

---

## 🎯 User Benefits

**Before:**
- ❌ ต้อง scroll หาเมนู
- ❌ เข้าถึงใบแจ้งหนี้ยาก
- ❌ ดูประวัติยาก
- ❌ ไม่มีหน้าโปรไฟล์

**After:**
- ✅ Quick access ทุกหน้า
- ✅ 1 tap ไปหน้าใดก็ได้
- ✅ Center button = primary action
- ✅ มีหน้าโปรไฟล์

---

## ⏱ Estimated Time

- Phase 1 (Update MobileLayout): 30 min
- Phase 2 (InvoiceList page): 1 hour
- Phase 3 (PaymentHistory page): 1 hour
- Phase 4 (Profile page): 45 min
- Phase 5 (Update routes): 15 min
- Phase 6 (Update dashboard): 30 min
- Testing: 30 min
- **Total: 4.5 hours**

---

## ✅ Success Criteria

**After implementation:**
- ✅ 5 menu items visible
- ✅ All pages accessible in 1 tap
- ✅ Center button styled as primary
- ✅ Active state clearly visible
- ✅ Touch targets ≥ 44px
- ✅ Smooth navigation
- ✅ No broken links

---

## 🎯 Summary

**Recommended:** Option 1 (5 Menu Items)

**New Menu:**
1. 🏠 **หน้าหลัก** (Dashboard)
2. 📄 **ใบแจ้งหนี้** (Invoice list)
3. 📸 **ส่งสลิป** (Submit payment) ← Primary
4. 📋 **ประวัติ** (Payment history)
5. 👤 **โปรไฟล์** (Profile)

**Benefits:**
- ✅ Better navigation
- ✅ Quick access
- ✅ Standard pattern
- ✅ Clear hierarchy

**Ready to implement!** 🚀
