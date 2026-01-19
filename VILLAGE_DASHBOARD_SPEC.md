# 📊 Village Dashboard - Specification

**Date:** January 19, 2026  
**Purpose:** Overall village financial overview for residents  
**Target:** Mobile-only resident interface  
**New Menu:** ภาพรวมหมู่บ้าน (Village Overview)

---

## 🎯 Overview

**What is Village Dashboard?**

A dedicated page showing **overall village financial statistics** that residents can view to understand:
- Total village balance
- Total income vs expenses
- Number of debtors
- Total debt amount
- Monthly income trends
- Top debtors list

**Why needed?**
- ✅ Transparency (residents see where money goes)
- ✅ Community awareness (who owes money)
- ✅ Financial health monitoring
- ✅ Trust building

---

## 📐 Layout Design

### Village Dashboard Page

```
┌─────────────────────────────────────┐
│ 🏘️ Moobaan Smart  ภาพรวมหมู่บ้าน   │ ← Header
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │   ยอดคงเหลือรวม                 │ │ ← Main Balance Card
│ │   ฿245,000                      │ │   (Gradient green-blue)
│ └─────────────────────────────────┘ │
│                                     │
│ ┌───────────────┐ ┌───────────────┐ │
│ │ รายรับ    ↑   │ │ รายจ่าย   ↓  │ │ ← Income/Expense
│ │ ฿180,000      │ │ ฿65,000       │ │   Cards (2x2 grid)
│ └───────────────┘ └───────────────┘ │
│ ┌───────────────┐ ┌───────────────┐ │
│ │ ลูกหนี้       │ │ มูลค่าหนี้    │ │ ← Debtor Stats
│ │ 12 ราย        │ │ ฿18,500       │ │
│ └───────────────┘ └───────────────┘ │
├─────────────────────────────────────┤
│ สถิติรายเดือน                       │ ← Monthly Chart
│ ┌─────────────────────────────────┐ │   Section
│ │ ม.ค. ████████████████ ฿80,000  │ │
│ │ ก.พ. ██████████ ฿60,000        │ │
│ │ ธ.ค. ██████ ฿40,000            │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ กิจกรรมล่าสุด                       │ ← Recent Activity
│ ┌─────────────────────────────────┐ │   Section
│ │ 🏠 รับชำระค่าส่วนกลาง ม.ค.      │ │
│ │    24 ก.พ., 10:30 น.   ฿5,000  │ │
│ │ 💡 จ่ายค่าไฟฟ้า ประปาหมู่บ้าน   │ │
│ │    23 ก.พ., 15:45 น.   ฿3,500  │ │
│ │ 🎁 บริจาคซ่อมแซมศาลาหมู่บ้าน    │ │
│ │    22 ก.พ., 09:15 น.   ฿1,000  │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│  🏠   📊   📸   📋   👤            │ ← Bottom Nav
│ หน้าหลัก ภาพรวม ส่งสลิป ประวัติ โปรไฟล์ │
└─────────────────────────────────────┘
```

---

## 🎨 Component Specifications

### 1. Main Balance Card

**Purpose:** Show total village balance (income - expenses)

**Design:**
```jsx
<div className="bg-gradient-to-br from-primary-500 via-primary-600 to-blue-600 rounded-xl p-6 shadow-lg mb-4">
  <div className="text-sm text-white/80 mb-2">ยอดคงเหลือรวม</div>
  <div className="text-4xl font-bold text-white">
    ฿{totalBalance.toLocaleString()}
  </div>
</div>
```

**Data:**
- Total balance = Total income - Total expenses
- Updates in real-time

**Height:** ~100px

---

### 2. Income/Expense Cards (2x2 Grid)

**Purpose:** Show key financial metrics

**Design:**
```jsx
<div className="grid grid-cols-2 gap-3 mb-4">
  {/* Income Card */}
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-gray-400">รายรับ</span>
      <ArrowUp size={20} className="text-green-400" />
    </div>
    <div className="text-2xl font-bold text-white">
      ฿{totalIncome.toLocaleString()}
    </div>
  </div>
  
  {/* Expense Card */}
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-gray-400">รายจ่าย</span>
      <ArrowDown size={20} className="text-red-400" />
    </div>
    <div className="text-2xl font-bold text-white">
      ฿{totalExpense.toLocaleString()}
    </div>
  </div>
  
  {/* Debtor Count Card */}
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-gray-400">ลูกหนี้</span>
      <Users size={20} className="text-orange-400" />
    </div>
    <div className="text-2xl font-bold text-orange-400">
      {debtorCount} ราย
    </div>
  </div>
  
  {/* Total Debt Card */}
  <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-gray-400">มูลค่าหนี้</span>
      <DollarSign size={20} className="text-red-400" />
    </div>
    <div className="text-2xl font-bold text-red-400">
      ฿{totalDebt.toLocaleString()}
    </div>
  </div>
</div>
```

**Data:**
- Total income: Sum of all payments
- Total expense: Sum of all expenses
- Debtor count: Number of houses with unpaid invoices
- Total debt: Sum of all unpaid invoice amounts

**Height:** ~80px each card

---

### 3. Monthly Income Chart

**Purpose:** Show income trend over last 3 months

**Design:**
```jsx
<div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-4">
  <h3 className="text-sm font-medium text-gray-300 mb-3">สถิติรายเดือน</h3>
  
  <div className="space-y-3">
    {monthlyData.map(month => (
      <div key={month.period} className="flex items-center gap-3">
        <span className="text-xs text-gray-400 w-12">{month.label}</span>
        <div className="flex-1 bg-gray-700 rounded-full h-6 overflow-hidden">
          <div 
            className="bg-primary-500 h-full rounded-full flex items-center justify-end pr-2"
            style={{ width: `${(month.amount / maxAmount) * 100}%` }}
          >
            <span className="text-xs font-medium text-white">
              ฿{month.amount.toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    ))}
  </div>
</div>
```

**Data:**
- Last 3 months income
- Sorted by most recent first
- Bar width = percentage of max amount

**Height:** ~150px

---

### 4. Recent Activity Feed

**Purpose:** Show recent village financial activities (without personal data)

**Design:**
```jsx
<div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
  <div className="p-3 border-b border-gray-700">
    <h3 className="text-sm font-medium text-gray-300">กิจกรรมล่าสุด</h3>
  </div>
  
  {/* Activity List */}
  <div className="divide-y divide-gray-700">
    {recentActivities.map((activity, index) => (
      <div key={index} className="p-3 flex items-start gap-3">
        <div className="text-2xl">{activity.icon}</div>
        <div className="flex-1 min-w-0">
          <div className="text-sm text-white">{activity.description}</div>
          <div className="text-xs text-gray-400 mt-1">{activity.timestamp}</div>
        </div>
        <div className={`text-sm font-semibold ${
          activity.type === 'income' ? 'text-green-400' : 'text-red-400'
        }`}>
          {activity.type === 'income' ? '+' : '-'}฿{activity.amount.toLocaleString()}
        </div>
      </div>
    ))}
  </div>
</div>
```

**Data:**
- Last 5 financial activities
- Generic descriptions (no personal info)
- Income/expense indicators
- Timestamps

**Height:** ~250px

---

## 📊 Data Structure

### API Endpoint

**Path:** `/api/dashboard/village-summary`

**Response:**
```json
{
  "total_balance": 245000,
  "total_income": 180000,
  "total_expense": 65000,
  "debtor_count": 12,
  "total_debt": 18500,
  "monthly_income": [
    { "period": "2026-01", "label": "ม.ค.", "amount": 80000 },
    { "period": "2025-12", "label": "ธ.ค.", "amount": 60000 },
    { "period": "2025-11", "label": "พ.ย.", "amount": 40000 }
  ],
  "recent_activities": [
    {
      "icon": "🏠",
      "description": "รับชำระค่าส่วนกลาง ม.ค.",
      "timestamp": "24 ก.พ., 10:30 น.",
      "amount": 5000,
      "type": "income"
    },
    {
      "icon": "💡",
      "description": "จ่ายค่าไฟฟ้า ประปาหมู่บ้าน",
      "timestamp": "23 ก.พ., 15:45 น.",
      "amount": 3500,
      "type": "expense"
    },
    {
      "icon": "🎁",
      "description": "บริจาคซ่อมแซมศาลาหมู่บ้าน",
      "timestamp": "22 ก.พ., 09:15 น.",
      "amount": 1000,
      "type": "income"
    }
  ]
}
```

---

### Calculation Logic

**Total Balance:**
```python
total_balance = sum(all_payments) - sum(all_expenses)
```

**Total Income:**
```python
total_income = sum(payments where status = 'ACCEPTED')
```

**Total Expense:**
```python
total_expense = sum(all_expenses)
```

**Debtor Count:**
```python
debtor_count = count(distinct houses with unpaid invoices)
```

**Total Debt:**
```python
total_debt = sum(unpaid_invoice_amounts)
```

**Monthly Income:**
```python
monthly_income = [
  {
    "period": month,
    "amount": sum(payments in month where status = 'ACCEPTED')
  }
  for month in last_3_months
]
```

**Recent Activities:**
```python
recent_activities = [
  {
    "icon": get_activity_icon(activity.type),
    "description": activity.description,
    "timestamp": activity.created_at.strftime("%d %b, %H:%M น."),
    "amount": activity.amount,
    "type": "income" if activity.amount > 0 else "expense"
  }
  for activity in recent_transactions
  order by created_at desc
  limit 5
]
```

---

## 🎯 Updated Bottom Navigation

### New Menu (5 Items)

```javascript
const navItems = [
  { 
    path: '/resident/dashboard', 
    icon: '🏠', 
    label: 'หน้าหลัก',
    description: 'Personal dashboard'
  },
  { 
    path: '/resident/village', 
    icon: '📊', 
    label: 'ภาพรวม',
    description: 'Village overview',
    isPrimary: false
  },
  { 
    path: '/resident/submit', 
    icon: '📸', 
    label: 'ส่งสลิป',
    description: 'Submit payment',
    isPrimary: true  // Center button
  },
  { 
    path: '/resident/payments', 
    icon: '📋', 
    label: 'ประวัติ',
    description: 'Payment history'
  },
  { 
    path: '/resident/profile', 
    icon: '👤', 
    label: 'โปรไฟล์',
    description: 'User profile'
  },
];
```

**Menu Items:**
1. 🏠 **หน้าหลัก** → Personal dashboard (my house)
2. 📊 **ภาพรวม** → Village overview (all houses) ← NEW!
3. 📸 **ส่งสลิป** → Submit payment (center button)
4. 📋 **ประวัติ** → Payment history
5. 👤 **โปรไฟล์** → User profile

---

## 🛠 Implementation Plan

### Phase 1: Backend API (2 hours)

**File:** `backend/app/api/dashboard.py`

**Tasks:**
1. Create `/api/dashboard/village-summary` endpoint
2. Implement calculation logic
3. Add caching (5 minutes)
4. Test with sample data

**Code:**
```python
@router.get("/village-summary")
async def get_village_summary(db: Session = Depends(get_db)):
    """Get overall village financial summary"""
    
    # Total income (accepted payments)
    total_income = db.query(func.sum(Payment.amount))\
        .filter(Payment.status == 'ACCEPTED')\
        .scalar() or 0
    
    # Total expense
    total_expense = db.query(func.sum(Expense.amount)).scalar() or 0
    
    # Total balance
    total_balance = total_income - total_expense
    
    # Debtor count (houses with unpaid invoices)
    debtor_count = db.query(func.count(func.distinct(Invoice.house_id)))\
        .filter(Invoice.status == 'UNPAID')\
        .scalar() or 0
    
    # Total debt
    total_debt = db.query(func.sum(Invoice.amount))\
        .filter(Invoice.status == 'UNPAID')\
        .scalar() or 0
    
    # Monthly income (last 3 months)
    monthly_income = []
    for i in range(3):
        month_start = datetime.now() - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)
        
        amount = db.query(func.sum(Payment.amount))\
            .filter(
                Payment.status == 'ACCEPTED',
                Payment.paid_at >= month_start,
                Payment.paid_at < month_end
            )\
            .scalar() or 0
        
        monthly_income.append({
            "period": month_start.strftime("%Y-%m"),
            "label": month_start.strftime("%b"),  # Thai month abbreviation
            "amount": amount
        })
    
    # Recent activities (last 5 transactions)
    recent_payments = db.query(Payment)\
        .filter(Payment.status == 'ACCEPTED')\
        .order_by(desc(Payment.paid_at))\
        .limit(3)\
        .all()
    
    recent_expenses = db.query(Expense)\
        .order_by(desc(Expense.created_at))\
        .limit(2)\
        .all()
    
    activities = []
    
    for payment in recent_payments:
        activities.append({
            "icon": "🏠",
            "description": f"รับชำระค่าส่วนกลาง {payment.period}",
            "timestamp": payment.paid_at.strftime("%d %b, %H:%M น."),
            "amount": payment.amount,
            "type": "income"
        })
    
    for expense in recent_expenses:
        activities.append({
            "icon": "💡",
            "description": expense.description or "รายจ่ายหมู่บ้าน",
            "timestamp": expense.created_at.strftime("%d %b, %H:%M น."),
            "amount": expense.amount,
            "type": "expense"
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return {
        "total_balance": total_balance,
        "total_income": total_income,
        "total_expense": total_expense,
        "debtor_count": debtor_count,
        "total_debt": total_debt,
        "monthly_income": monthly_income,
        "recent_activities": activities[:5]
    }
```

---

### Phase 2: Frontend Page (2 hours)

**File:** `frontend/src/pages/resident/mobile/VillageDashboard.jsx`

**Tasks:**
1. Create page component
2. Fetch data from API
3. Implement all cards and charts
4. Add loading states

**Code:**
```jsx
import { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, Users, DollarSign } from 'lucide-react';
import MobileLayout from './MobileLayout';
import { api } from '../../../api/client';

export default function VillageDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    try {
      const response = await api.get('/api/dashboard/village-summary');
      setData(response.data);
    } catch (error) {
      console.error('Failed to load village summary:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">กำลังโหลด...</div>
        </div>
      </MobileLayout>
    );
  }
  
  const maxMonthlyAmount = Math.max(...data.monthly_income.map(m => m.amount));
  
  return (
    <MobileLayout>
      <div className="p-4 space-y-4">
        {/* Main Balance Card */}
        <div className="bg-gradient-to-br from-primary-500 via-primary-600 to-blue-600 rounded-xl p-6 shadow-lg">
          <div className="text-sm text-white/80 mb-2">ยอดคงเหลือรวม</div>
          <div className="text-4xl font-bold text-white">
            ฿{data.total_balance.toLocaleString()}
          </div>
        </div>
        
        {/* Income/Expense/Debtor Grid */}
        <div className="grid grid-cols-2 gap-3">
          {/* Income */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">รายรับ</span>
              <ArrowUp size={20} className="text-green-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              ฿{data.total_income.toLocaleString()}
            </div>
          </div>
          
          {/* Expense */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">รายจ่าย</span>
              <ArrowDown size={20} className="text-red-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              ฿{data.total_expense.toLocaleString()}
            </div>
          </div>
          
          {/* Debtor Count */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">ลูกหนี้</span>
              <Users size={20} className="text-orange-400" />
            </div>
            <div className="text-2xl font-bold text-orange-400">
              {data.debtor_count} ราย
            </div>
          </div>
          
          {/* Total Debt */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">มูลค่าหนี้</span>
              <DollarSign size={20} className="text-red-400" />
            </div>
            <div className="text-2xl font-bold text-red-400">
              ฿{data.total_debt.toLocaleString()}
            </div>
          </div>
        </div>
        
        {/* Monthly Income Chart */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-300 mb-3">สถิติรายเดือน</h3>
          <div className="space-y-3">
            {data.monthly_income.map(month => (
              <div key={month.period} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-12">{month.label}</span>
                <div className="flex-1 bg-gray-700 rounded-full h-6 overflow-hidden">
                  <div 
                    className="bg-primary-500 h-full rounded-full flex items-center justify-end pr-2"
                    style={{ width: `${(month.amount / maxMonthlyAmount) * 100}%` }}
                  >
                    <span className="text-xs font-medium text-white">
                      ฿{month.amount.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Recent Activity Feed */}
        <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
          <div className="p-3 border-b border-gray-700">
            <h3 className="text-sm font-medium text-gray-300">กิจกรรมล่าสุด</h3>
          </div>
          
          <div className="divide-y divide-gray-700">
            {data.recent_activities.map((activity, index) => (
              <div key={index} className="p-3 flex items-start gap-3">
                <div className="text-2xl">{activity.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white">{activity.description}</div>
                  <div className="text-xs text-gray-400 mt-1">{activity.timestamp}</div>
                </div>
                <div className={`text-sm font-semibold ${
                  activity.type === 'income' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {activity.type === 'income' ? '+' : '-'}฿{activity.amount.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </MobileLayout>
  );
}
```

---

### Phase 3: Update Navigation (30 min)

**File:** `frontend/src/pages/resident/mobile/MobileLayout.jsx`

**Changes:**
1. Add village dashboard to navItems
2. Update icon (📊)

**File:** `frontend/src/App.jsx`

**Changes:**
1. Add route: `/resident/village` → `<VillageDashboard />`

---

## 📊 Privacy & Access Control

### Considerations

**Q: Should all residents see village-wide data?**

**Decision: Public with Privacy Protection** ✅

**What is shown:**
- ✅ Total balance
- ✅ Total income/expense
- ✅ Debtor count (number only)
- ✅ Total debt amount (aggregate)
- ✅ Monthly trends
- ✅ Recent activities (generic descriptions)

**What is NOT shown:**
- ❌ Individual house codes
- ❌ Personal debtor names
- ❌ Specific house debt amounts
- ❌ Personal payment details

**Compliance:**
- ✅ PDPA compliant (no personal data exposure)
- ✅ Transparency maintained
- ✅ Privacy protected
- ✅ Community awareness without shaming

---

## ⏱ Estimated Time

- Phase 1 (Backend API): 2 hours
- Phase 2 (Frontend page): 2 hours
- Phase 3 (Update navigation): 30 min
- Testing: 1 hour
- **Total: 5.5 hours**

---

## ✅ Success Criteria

**After implementation:**
- ✅ Village dashboard accessible from bottom nav
- ✅ All statistics display correctly
- ✅ Real-time data updates
- ✅ Charts render properly
- ✅ Mobile responsive
- ✅ Loading states work
- ✅ Error handling in place

---

## 🎯 Summary

**New Feature:** Village Dashboard (ภาพรวมหมู่บ้าน)

**Key Metrics:**
1. ✅ Total balance
2. ✅ Total income
3. ✅ Total expense
4. ✅ Debtor count
5. ✅ Total debt
6. ✅ Monthly income trend
7. ✅ Top debtors list

**Benefits:**
- ✅ Transparency
- ✅ Community awareness
- ✅ Financial monitoring
- ✅ Trust building

**Ready to implement!** 🚀
