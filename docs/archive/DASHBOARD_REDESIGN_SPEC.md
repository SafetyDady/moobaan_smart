# 📱 Resident Mobile Dashboard - Redesign Specification

**Date:** January 19, 2026  
**Design Goal:** Summary-first dashboard with table view for better scalability  
**Target:** Mobile-only resident interface  
**Problem Solved:** Too many large cards causing excessive scrolling

---

## 🎯 Design Overview

### Current Problem
- Large cards (120-180px height each)
- Poor scalability (only 2-3 visible per screen)
- No summary or filtering
- Overwhelming when many invoices/payments exist

### New Solution
- **Summary cards** at top (at-a-glance overview)
- **Filter tabs** for quick access
- **Compact table view** (30-40px per row)
- **Modal for details** (tap to expand)

---

## 📐 Layout Structure

### Screen 1: Dashboard Overview (หน้าหลัก)

```
┌─────────────────────────────────────┐
│ 🏠 Moobaan Smart    บ้านเลขที่ 28/2 │ ← Header
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │      ค่าใช้จ่าย                 │ │ ← Summary Card
│ │      ฿7,000                     │ │   (Total Outstanding)
│ └─────────────────────────────────┘ │
│ ┌───────────────┐ ┌───────────────┐ │
│ │       1       │ │       3       │ │ ← Quick Stats
│ │ ใบแจ้งหนี้ที่  │ │ สลิปรอตรวจ    │ │
│ │ ยังไม่จ่าย     │ │ สอบ           │ │
│ └───────────────┘ └───────────────┘ │
├─────────────────────────────────────┤
│ ใบแจ้งหนี้                          │ ← Section Header
│ ┌───────────────────────────────┐   │
│ │ ทั้งหมด │ ชำระแล้ว │ รอชำระ │   │ ← Filter Tabs
│ └───────────────────────────────┘   │
│ ┌─────────────────────────────────┐ │
│ │ 2026-01    ฿600         [PAID] │ │ ← Table Row
│ │ 2025-12    ฿600         [PAID] │ │
│ │ 2025-11    ฿600       [UNPAID] │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ ประวัติการส่งสลิป (ดูทั้งหมด →)    │ ← Section + Link
│ ┌─────────────────────────────────┐ │
│ │ ฿7,000  [รอตรวจสอบ]  1 ม.ค. 👁│ │ ← Recent 3
│ │ ฿3,500  [ผ่านแล้ว]  15 ธ.ค. 👁│ │
│ │ ฿600    [ผ่านแล้ว]  10 ธ.ค. 👁│ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│  🏠   📄   📸   📋   👤             │ ← Bottom Nav
└─────────────────────────────────────┘
```

---

### Screen 2: Payment History (ประวัติการส่งสลิป)

```
┌─────────────────────────────────────┐
│ ← ประวัติการส่งสลิป                 │ ← Header with Back
├─────────────────────────────────────┤
│ ┌───────────────────────────────┐   │
│ │ ทั้งหมด │ รอตรวจสอบ │ ผ่านแล้ว │ │ ← Filter Tabs
│ │         │ ถูกปฏิเสธ             │ │   (4 tabs)
│ └───────────────────────────────┘   │
│ ┌─────────────────────────────────┐ │
│ │ ฿7,000  [รอตรวจสอบ]            │ │ ← Table Row
│ │ 1 ม.ค. 69 11:11            👁  │ │   (Compact)
│ ├─────────────────────────────────┤ │
│ │ ฿3,500  [ผ่านแล้ว]             │ │
│ │ 15 ธ.ค. 68 14:30           👁  │ │
│ ├─────────────────────────────────┤ │
│ │ ฿600    [ผ่านแล้ว]             │ │
│ │ 10 ธ.ค. 68 09:15           👁  │ │
│ ├─────────────────────────────────┤ │
│ │ ฿1,200  [ถูกปฏิเสธ]            │ │
│ │ 5 ธ.ค. 68 16:45        👁  ✏️ │ │   (Edit for rejected)
│ ├─────────────────────────────────┤ │
│ │ ฿7,000  [รอตรวจสอบ]            │ │
│ │ 1 ธ.ค. 68 10:00            👁  │ │
│ └─────────────────────────────────┘ │
│                                     │
│                                     │
│                              ┌───┐  │
│                              │ + │  │ ← FAB (Add Payment)
│                              └───┘  │
└─────────────────────────────────────┘
```

---

### Screen 3: Invoice Detail Modal (รายละเอียดใบแจ้งหนี้)

```
┌─────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ ← Dark Overlay
│ ░░░┌───────────────────────────┐░░░ │
│ ░░░│ รายละเอียดใบแจ้งหนี้    X │░░░ │ ← Modal Header
│ ░░░├───────────────────────────┤░░░ │
│ ░░░│                           │░░░ │
│ ░░░│       2026-01             │░░░ │ ← Period (Large)
│ ░░░│                           │░░░ │
│ ░░░│ จำนวนเงิน:        ฿600    │░░░ │
│ ░░░│ สถานะ:        [ชำระแล้ว]  │░░░ │
│ ░░░│ ครบกำหนด:    31 ม.ค. 69  │░░░ │
│ ░░░│ สร้างเมื่อ:   1 ม.ค. 69  │░░░ │
│ ░░░│                           │░░░ │
│ ░░░│ ─────────────────────────  │░░░ │
│ ░░░│                           │░░░ │
│ ░░░│ รายการชำระ:               │░░░ │
│ ░░░│ ┌───────────────────────┐ │░░░ │
│ ░░░│ │ ฿600  15 ม.ค. 69  ✓  │ │░░░ │ ← Payment List
│ ░░░│ └───────────────────────┘ │░░░ │
│ ░░░│                           │░░░ │
│ ░░░│ ┌───────────────────────┐ │░░░ │
│ ░░░│ │ ส่งหลักฐานการชำระ     │ │░░░ │ ← Action Button
│ ░░░│ └───────────────────────┘ │░░░ │
│ ░░░└───────────────────────────┘░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────────────┘
```

---

## 🎨 Component Specifications

### 1. Summary Card (ค่าใช้จ่าย)

**Purpose:** Show total outstanding balance at a glance

**Design:**
```jsx
<div className="bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl p-6 shadow-lg">
  <div className="text-sm text-white/80 mb-2">ค่าใช้จ่าย</div>
  <div className="text-4xl font-bold text-white">
    ฿{totalOutstanding.toLocaleString()}
  </div>
</div>
```

**Data:**
- Total amount from unpaid invoices
- Updates in real-time

**Height:** ~100px

---

### 2. Quick Stats Cards

**Purpose:** Show key metrics (unpaid invoices, pending payments)

**Design:**
```jsx
<div className="grid grid-cols-2 gap-3">
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <div className="text-3xl font-bold text-white mb-1">{unpaidCount}</div>
    <div className="text-xs text-gray-400">ใบแจ้งหนี้ที่ยังไม่จ่าย</div>
  </div>
  
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <div className="text-3xl font-bold text-white mb-1">{pendingCount}</div>
    <div className="text-xs text-gray-400">สลิปรอตรวจสอบ</div>
  </div>
</div>
```

**Data:**
- Left: Count of unpaid invoices
- Right: Count of pending payments

**Height:** ~80px each

---

### 3. Filter Tabs

**Purpose:** Quick filtering without leaving page

**Design:**
```jsx
<div className="flex gap-2 overflow-x-auto pb-2">
  {filters.map(filter => (
    <button
      key={filter.id}
      onClick={() => setActiveFilter(filter.id)}
      className={`
        px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap
        transition-colors
        ${activeFilter === filter.id 
          ? 'bg-primary-500 text-white' 
          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        }
      `}
    >
      {filter.label}
    </button>
  ))}
</div>
```

**Filters for Invoices:**
- ทั้งหมด (All)
- ชำระแล้ว (Paid)
- รอชำระ (Unpaid)

**Filters for Payments:**
- ทั้งหมด (All)
- รอตรวจสอบ (Pending)
- ผ่านแล้ว (Accepted)
- ถูกปฏิเสธ (Rejected)

**Height:** ~40px

---

### 4. Table Row (Invoice)

**Purpose:** Compact display of invoice info

**Design:**
```jsx
<div 
  onClick={() => handleViewInvoice(invoice.id)}
  className="flex items-center justify-between p-3 bg-gray-800 border-b border-gray-700 active:bg-gray-750 transition-colors"
>
  <div className="flex-1">
    <div className="text-sm font-medium text-white">{invoice.period}</div>
  </div>
  
  <div className="flex items-center gap-3">
    <div className="text-base font-bold text-white">
      ฿{invoice.amount.toLocaleString()}
    </div>
    <StatusBadge status={invoice.status} size="sm" />
  </div>
</div>
```

**Data:**
- Period (2026-01)
- Amount (฿600)
- Status badge (PAID/UNPAID)

**Interaction:**
- Tap entire row → Open detail modal

**Height:** ~50px

---

### 5. Table Row (Payment)

**Purpose:** Compact display of payment info with actions

**Design:**
```jsx
<div className="flex items-start justify-between p-3 bg-gray-800 border-b border-gray-700">
  <div className="flex-1 min-w-0">
    <div className="flex items-center gap-2 mb-1">
      <span className="text-base font-bold text-white">
        ฿{payment.amount.toLocaleString()}
      </span>
      <StatusBadge status={payment.status} size="sm" />
    </div>
    <div className="text-xs text-gray-400">
      {formatDateTime(payment.paid_at)}
    </div>
  </div>
  
  <div className="flex items-center gap-2 ml-2">
    <button 
      onClick={() => handleViewPayment(payment)}
      className="p-2 text-gray-400 hover:text-primary-400 active:bg-gray-700 rounded transition-colors"
    >
      <Eye size={18} />
    </button>
    
    {payment.status === 'REJECTED' && (
      <button 
        onClick={() => handleEditPayment(payment)}
        className="p-2 text-gray-400 hover:text-blue-400 active:bg-gray-700 rounded transition-colors"
      >
        <Edit2 size={18} />
      </button>
    )}
  </div>
</div>
```

**Data:**
- Amount (฿7,000)
- Status badge (รอตรวจสอบ, ผ่านแล้ว, ถูกปฏิเสธ)
- Date/time (1 ม.ค. 69 11:11)
- Actions (View, Edit if rejected)

**Height:** ~60px

---

### 6. Detail Modal

**Purpose:** Show full invoice/payment details without leaving page

**Design:**
```jsx
<div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
  <div className="bg-gray-900 rounded-xl w-full max-w-md max-h-[80vh] overflow-y-auto border border-gray-700">
    {/* Header */}
    <div className="flex items-center justify-between p-4 border-b border-gray-700">
      <h3 className="text-lg font-semibold text-white">
        รายละเอียดใบแจ้งหนี้
      </h3>
      <button onClick={onClose} className="text-gray-400 hover:text-white">
        <X size={24} />
      </button>
    </div>
    
    {/* Content */}
    <div className="p-4 space-y-4">
      <div className="text-2xl font-bold text-white text-center">
        {invoice.period}
      </div>
      
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="text-gray-400">จำนวนเงิน:</div>
        <div className="text-white font-semibold text-right">
          ฿{invoice.amount.toLocaleString()}
        </div>
        
        <div className="text-gray-400">สถานะ:</div>
        <div className="text-right">
          <StatusBadge status={invoice.status} />
        </div>
        
        <div className="text-gray-400">ครบกำหนด:</div>
        <div className="text-white text-right">
          {formatDate(invoice.due_date)}
        </div>
        
        <div className="text-gray-400">สร้างเมื่อ:</div>
        <div className="text-white text-right">
          {formatDate(invoice.created_at)}
        </div>
      </div>
      
      {/* Payment list if paid */}
      {invoice.payments?.length > 0 && (
        <>
          <div className="border-t border-gray-700 pt-4">
            <div className="text-sm font-medium text-gray-300 mb-2">
              รายการชำระ:
            </div>
            {invoice.payments.map(payment => (
              <div key={payment.id} className="flex items-center justify-between p-2 bg-gray-800 rounded mb-2">
                <span className="text-white">฿{payment.amount}</span>
                <span className="text-xs text-gray-400">{formatDate(payment.paid_at)}</span>
                <CheckCircle size={16} className="text-green-400" />
              </div>
            ))}
          </div>
        </>
      )}
      
      {/* Action button */}
      {invoice.status === 'UNPAID' && (
        <button className="w-full bg-primary-500 hover:bg-primary-600 text-white py-3 rounded-lg font-medium transition-colors">
          ส่งหลักฐานการชำระ
        </button>
      )}
    </div>
  </div>
</div>
```

---

## 📊 Data Flow

### Dashboard Overview

```javascript
// Fetch data
const { data: invoices } = trpc.invoice.list.useQuery();
const { data: payments } = trpc.payment.list.useQuery();

// Calculate summary
const totalOutstanding = invoices
  ?.filter(inv => inv.status === 'UNPAID')
  .reduce((sum, inv) => sum + inv.amount, 0) || 0;

const unpaidCount = invoices?.filter(inv => inv.status === 'UNPAID').length || 0;
const pendingCount = payments?.filter(p => p.status === 'PENDING').length || 0;

// Filter invoices
const [invoiceFilter, setInvoiceFilter] = useState('all');
const filteredInvoices = invoices?.filter(inv => {
  if (invoiceFilter === 'paid') return inv.status === 'PAID';
  if (invoiceFilter === 'unpaid') return inv.status === 'UNPAID';
  return true;
});

// Recent payments (top 3)
const recentPayments = payments?.slice(0, 3) || [];
```

---

### Payment History Page

```javascript
// Fetch all payments
const { data: payments } = trpc.payment.list.useQuery();

// Filter state
const [filter, setFilter] = useState('all');

// Filter logic
const filteredPayments = payments?.filter(payment => {
  if (filter === 'pending') return payment.status === 'PENDING';
  if (filter === 'accepted') return payment.status === 'ACCEPTED';
  if (filter === 'rejected') return payment.status === 'REJECTED';
  return true;
});

// Sort by date (newest first)
const sortedPayments = filteredPayments?.sort((a, b) => 
  new Date(b.paid_at) - new Date(a.paid_at)
);
```

---

## 🎯 Key Improvements

### Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Dashboard Height** | 800px+ | 600px | **-25%** |
| **Invoice Row Height** | 120px | 50px | **-58%** |
| **Payment Row Height** | 180px | 60px | **-67%** |
| **Items per Screen** | 2-3 | 8-10 | **+300%** |
| **Summary Visibility** | None | Always | **New** |
| **Filter Speed** | N/A | Instant | **New** |

---

### User Benefits

**Before:**
- ❌ No overview, must scroll to see all
- ❌ Large cards waste space
- ❌ No filtering, hard to find specific items
- ❌ Overwhelming when many items

**After:**
- ✅ Summary at top (instant overview)
- ✅ Compact rows (see more items)
- ✅ Quick filters (find items fast)
- ✅ Scalable (works with 100+ items)
- ✅ Modal for details (clean separation)

---

## 🛠 Implementation Plan

### Phase 1: Dashboard Summary Section (1 hour)

**File:** `frontend/src/pages/resident/mobile/MobileDashboard.jsx`

**Tasks:**
1. Add summary card component
2. Add quick stats cards
3. Calculate totals from data
4. Add responsive layout

**Code:**
```jsx
// Summary Section
<div className="p-4 space-y-3">
  {/* Total Outstanding */}
  <div className="bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl p-6 shadow-lg">
    <div className="text-sm text-white/80 mb-2">ค่าใช้จ่าย</div>
    <div className="text-4xl font-bold text-white">
      ฿{totalOutstanding.toLocaleString()}
    </div>
  </div>
  
  {/* Quick Stats */}
  <div className="grid grid-cols-2 gap-3">
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="text-3xl font-bold text-white mb-1">{unpaidCount}</div>
      <div className="text-xs text-gray-400">ใบแจ้งหนี้ที่ยังไม่จ่าย</div>
    </div>
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="text-3xl font-bold text-white mb-1">{pendingCount}</div>
      <div className="text-xs text-gray-400">สลิปรอตรวจสอบ</div>
    </div>
  </div>
</div>
```

---

### Phase 2: Invoice Table View (1.5 hours)

**File:** `frontend/src/pages/resident/mobile/MobileDashboard.jsx`

**Tasks:**
1. Add filter tabs component
2. Convert card list to table rows
3. Add tap to view modal
4. Implement filtering logic

**Code:**
```jsx
// Filter Tabs
<div className="px-4 mb-3">
  <div className="flex gap-2 overflow-x-auto pb-2">
    {invoiceFilters.map(filter => (
      <button
        key={filter.id}
        onClick={() => setInvoiceFilter(filter.id)}
        className={`
          px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap
          transition-colors
          ${invoiceFilter === filter.id 
            ? 'bg-primary-500 text-white' 
            : 'bg-gray-800 text-gray-400'
          }
        `}
      >
        {filter.label}
      </button>
    ))}
  </div>
</div>

// Table Rows
<div className="bg-gray-800 rounded-lg overflow-hidden mx-4">
  {filteredInvoices.map((invoice, index) => (
    <div
      key={invoice.id}
      onClick={() => handleViewInvoice(invoice)}
      className={`
        flex items-center justify-between p-3
        ${index > 0 ? 'border-t border-gray-700' : ''}
        active:bg-gray-750 transition-colors
      `}
    >
      <div className="text-sm font-medium text-white">
        {invoice.period}
      </div>
      <div className="flex items-center gap-3">
        <div className="text-base font-bold text-white">
          ฿{invoice.amount.toLocaleString()}
        </div>
        <StatusBadge status={invoice.status} size="sm" />
      </div>
    </div>
  ))}
</div>
```

---

### Phase 3: Payment Table View (1 hour)

**File:** `frontend/src/pages/resident/mobile/MobileDashboard.jsx`

**Tasks:**
1. Convert payment cards to table rows
2. Add "ดูทั้งหมด" link to separate page
3. Show only recent 3 on dashboard

**Code:**
```jsx
// Section Header with Link
<div className="flex items-center justify-between px-4 mb-3">
  <h2 className="text-lg font-semibold text-white">ประวัติการส่งสลิป</h2>
  <Link 
    to="/resident/payments" 
    className="text-sm text-primary-400 hover:text-primary-300"
  >
    ดูทั้งหมด →
  </Link>
</div>

// Recent Payments (Top 3)
<div className="bg-gray-800 rounded-lg overflow-hidden mx-4">
  {recentPayments.map((payment, index) => (
    <div
      key={payment.id}
      className={`
        flex items-start justify-between p-3
        ${index > 0 ? 'border-t border-gray-700' : ''}
      `}
    >
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-base font-bold text-white">
            ฿{payment.amount.toLocaleString()}
          </span>
          <StatusBadge status={payment.status} size="sm" />
        </div>
        <div className="text-xs text-gray-400">
          {formatDateTime(payment.paid_at)}
        </div>
      </div>
      <button 
        onClick={() => handleViewPayment(payment)}
        className="p-2 text-gray-400"
      >
        <Eye size={18} />
      </button>
    </div>
  ))}
</div>
```

---

### Phase 4: Detail Modal (1 hour)

**File:** `frontend/src/components/InvoiceDetailModal.jsx` (new)

**Tasks:**
1. Create modal component
2. Add invoice details layout
3. Add payment history if paid
4. Add action button

**Code:**
```jsx
export default function InvoiceDetailModal({ invoice, onClose }) {
  if (!invoice) return null;
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-900 rounded-xl w-full max-w-md max-h-[80vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 sticky top-0 bg-gray-900">
          <h3 className="text-lg font-semibold text-white">
            รายละเอียดใบแจ้งหนี้
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={24} />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Period */}
          <div className="text-2xl font-bold text-white text-center">
            {invoice.period}
          </div>
          
          {/* Details Grid */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="text-gray-400">จำนวนเงิน:</div>
            <div className="text-white font-semibold text-right">
              ฿{invoice.amount.toLocaleString()}
            </div>
            
            <div className="text-gray-400">สถานะ:</div>
            <div className="text-right">
              <StatusBadge status={invoice.status} />
            </div>
            
            <div className="text-gray-400">ครบกำหนด:</div>
            <div className="text-white text-right">
              {formatDate(invoice.due_date)}
            </div>
            
            <div className="text-gray-400">สร้างเมื่อ:</div>
            <div className="text-white text-right">
              {formatDate(invoice.created_at)}
            </div>
          </div>
          
          {/* Payments */}
          {invoice.payments?.length > 0 && (
            <div className="border-t border-gray-700 pt-4">
              <div className="text-sm font-medium text-gray-300 mb-2">
                รายการชำระ:
              </div>
              {invoice.payments.map(payment => (
                <div key={payment.id} className="flex items-center justify-between p-2 bg-gray-800 rounded mb-2">
                  <span className="text-white">฿{payment.amount}</span>
                  <span className="text-xs text-gray-400">
                    {formatDate(payment.paid_at)}
                  </span>
                  <CheckCircle size={16} className="text-green-400" />
                </div>
              ))}
            </div>
          )}
          
          {/* Action */}
          {invoice.status === 'UNPAID' && (
            <button 
              onClick={() => handleSubmitPayment(invoice)}
              className="w-full bg-primary-500 hover:bg-primary-600 text-white py-3 rounded-lg font-medium transition-colors"
            >
              ส่งหลักฐานการชำระ
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

### Phase 5: Payment History Page (1 hour)

**File:** `frontend/src/pages/resident/mobile/PaymentHistory.jsx` (new)

**Tasks:**
1. Create full-page payment list
2. Add filter tabs (4 filters)
3. Add FAB for new payment
4. Implement filtering

**Code:**
```jsx
export default function PaymentHistory() {
  const { data: payments } = trpc.payment.list.useQuery();
  const [filter, setFilter] = useState('all');
  
  const filters = [
    { id: 'all', label: 'ทั้งหมด' },
    { id: 'pending', label: 'รอตรวจสอบ' },
    { id: 'accepted', label: 'ผ่านแล้ว' },
    { id: 'rejected', label: 'ถูกปฏิเสธ' },
  ];
  
  const filteredPayments = payments?.filter(payment => {
    if (filter === 'pending') return payment.status === 'PENDING';
    if (filter === 'accepted') return payment.status === 'ACCEPTED';
    if (filter === 'rejected') return payment.status === 'REJECTED';
    return true;
  });
  
  return (
    <div className="min-h-screen bg-gray-900 pb-20">
      {/* Header */}
      <div className="bg-gray-800 p-4 flex items-center gap-3">
        <button onClick={() => navigate(-1)}>
          <ArrowLeft size={24} className="text-white" />
        </button>
        <h1 className="text-xl font-semibold text-white">
          ประวัติการส่งสลิป
        </h1>
      </div>
      
      {/* Filter Tabs */}
      <div className="p-4">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {filters.map(f => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`
                px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap
                ${filter === f.id 
                  ? 'bg-primary-500 text-white' 
                  : 'bg-gray-800 text-gray-400'
                }
              `}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Payment List */}
      <div className="bg-gray-800 rounded-lg overflow-hidden mx-4">
        {filteredPayments?.map((payment, index) => (
          <div
            key={payment.id}
            className={`
              flex items-start justify-between p-3
              ${index > 0 ? 'border-t border-gray-700' : ''}
            `}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-base font-bold text-white">
                  ฿{payment.amount.toLocaleString()}
                </span>
                <StatusBadge status={payment.status} size="sm" />
              </div>
              <div className="text-xs text-gray-400">
                {formatDateTime(payment.paid_at)}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => handleView(payment)}>
                <Eye size={18} className="text-gray-400" />
              </button>
              {payment.status === 'REJECTED' && (
                <button onClick={() => handleEdit(payment)}>
                  <Edit2 size={18} className="text-gray-400" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* FAB */}
      <button 
        onClick={() => navigate('/resident/submit-payment')}
        className="fixed bottom-20 right-4 w-14 h-14 bg-primary-500 rounded-full flex items-center justify-center shadow-lg"
      >
        <Plus size={24} className="text-white" />
      </button>
    </div>
  );
}
```

---

## 📱 Responsive Considerations

### Small Screens (< 360px)

```css
@media (max-width: 360px) {
  /* Smaller summary card */
  .summary-amount { font-size: 2rem; }
  
  /* Tighter stats */
  .stats-number { font-size: 1.5rem; }
  .stats-label { font-size: 0.7rem; }
  
  /* Compact table rows */
  .table-row { padding: 0.625rem; }
  .table-amount { font-size: 0.875rem; }
}
```

### Large Screens (> 420px)

```css
@media (min-width: 420px) {
  /* Slightly larger summary */
  .summary-amount { font-size: 2.5rem; }
  
  /* More breathing room */
  .table-row { padding: 1rem; }
}
```

---

## ✅ Success Criteria

**After implementation, verify:**

1. **Summary Visibility**
   - ✅ Total outstanding always visible at top
   - ✅ Quick stats show key metrics
   - ✅ Updates in real-time

2. **Scalability**
   - ✅ Works with 100+ invoices
   - ✅ Works with 100+ payments
   - ✅ No performance issues

3. **Filtering**
   - ✅ Instant filter switching
   - ✅ Correct counts per filter
   - ✅ Visual feedback (active tab)

4. **Usability**
   - ✅ Easy to scan (compact rows)
   - ✅ Tap to view details
   - ✅ Clear status indicators
   - ✅ Touch targets ≥ 44px

5. **Visual Hierarchy**
   - ✅ Summary most prominent
   - ✅ Filters easy to find
   - ✅ Table rows scannable
   - ✅ Actions accessible

---

## 🚀 Deployment Checklist

**Before pushing to production:**

- [ ] Test with 0 invoices (empty state)
- [ ] Test with 1-5 invoices (normal)
- [ ] Test with 50+ invoices (stress test)
- [ ] Test all filter combinations
- [ ] Test modal open/close
- [ ] Test on iPhone SE (375px)
- [ ] Test on iPhone 12 (390px)
- [ ] Test on iPhone 14 Pro Max (430px)
- [ ] Verify touch targets (≥ 44px)
- [ ] Check loading states
- [ ] Check error states
- [ ] Test offline behavior
- [ ] Verify accessibility (screen reader)

---

## 📊 Estimated Impact

**Time Savings:**
- Before: 15 seconds to find specific invoice (scroll + search)
- After: 3 seconds (filter + scan)
- **80% faster** task completion

**User Satisfaction:**
- Better overview (summary cards)
- Faster filtering (instant tabs)
- Less scrolling (compact rows)
- Cleaner interface (table view)

**Development Time:**
- Phase 1 (Summary): 1 hour
- Phase 2 (Invoice table): 1.5 hours
- Phase 3 (Payment table): 1 hour
- Phase 4 (Modal): 1 hour
- Phase 5 (Payment page): 1 hour
- Testing: 1 hour
- **Total: 6.5 hours**

---

## 🎯 Summary

**New Design Features:**
1. ✅ Summary cards (total, counts)
2. ✅ Filter tabs (instant filtering)
3. ✅ Table view (compact rows)
4. ✅ Detail modal (tap to expand)
5. ✅ Separate payment history page

**Key Benefits:**
- ✅ Better scalability (100+ items)
- ✅ Faster navigation (filters)
- ✅ Less scrolling (compact)
- ✅ Cleaner design (organized)
- ✅ Better UX (summary-first)

**Ready to implement!** 🚀
