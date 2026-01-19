# Custom Calendar Implementation Guide

## Overview

เอกสารนี้อธิบายการเพิ่ม Custom Calendar (react-datepicker) ในหน้า Submit Payment พร้อม Date Range Limit (ย้อนหลัง 90 วัน)

---

## Features

### ✅ Custom Calendar
- Thai locale (ภาษาไทย)
- Date picker popup
- Visual date selection

### ✅ Date Range Limit
- **Min Date:** 90 วันย้อนหลังจากวันนี้
- **Max Date:** วันนี้
- วันที่นอกช่วง: Disabled (grayed out + strikethrough)

### ✅ Visual Indicators
- **Today:** Green circle background (#10b981)
- **Selected:** Blue circle background (#3b82f6)
- **Disabled:** Gray + strikethrough
- **Hover:** Light gray background

---

## Installation Steps

### Step 1: Install Dependencies

```bash
cd frontend
npm install react-datepicker date-fns
```

**Packages:**
- `react-datepicker`: Custom calendar component
- `date-fns`: Date manipulation library

---

### Step 2: Import CSS

Add to `frontend/src/index.css` or main CSS file:

```css
@import 'react-datepicker/dist/react-datepicker.css';
```

Or import in component:

```javascript
import 'react-datepicker/dist/react-datepicker.css';
```

---

### Step 3: Backup Original File

```bash
cp frontend/src/pages/resident/mobile/MobileSubmitPayment.jsx \
   frontend/src/pages/resident/mobile/MobileSubmitPayment.jsx.backup
```

---

### Step 4: Replace with New Component

```bash
cp MobileSubmitPayment_WithCalendar.jsx \
   frontend/src/pages/resident/mobile/MobileSubmitPayment.jsx
```

---

### Step 5: Test

```bash
cd frontend
npm run dev
```

Navigate to: `http://localhost:5173/resident/submit`

---

## Component Changes

### 1. Imports

**Added:**
```javascript
import DatePicker from 'react-datepicker';
import { subDays, startOfDay } from 'date-fns';
import { th } from 'date-fns/locale';
import 'react-datepicker/dist/react-datepicker.css';
```

---

### 2. Date Range Calculation

```javascript
// Date range: 90 days back from today
const today = startOfDay(new Date());
const minDate = subDays(today, 90);
const maxDate = today;
```

**Example:**
- Today: Feb 24, 2026
- Min Date: Nov 26, 2025 (90 days ago)
- Max Date: Feb 24, 2026 (today)

---

### 3. State Management

**Before:**
```javascript
transfer_date: editPayin?.transfer_date || '', // String
```

**After:**
```javascript
transfer_date: editPayin?.transfer_date ? new Date(editPayin.transfer_date) : null, // Date object
```

**Why?**
- DatePicker requires Date object, not string
- `null` = no date selected (empty state)

---

### 4. DatePicker Component

```jsx
<DatePicker
  selected={formData.transfer_date}
  onChange={(date) => setFormData({ ...formData, transfer_date: date })}
  minDate={minDate}
  maxDate={maxDate}
  dateFormat="dd/MM/yyyy"
  locale={th}
  placeholderText="เลือกวันที่"
  required
  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
  calendarClassName="custom-calendar"
  wrapperClassName="w-full"
/>
```

**Props:**
- `selected`: Current selected date (Date object or null)
- `onChange`: Callback when date is selected
- `minDate`: Minimum selectable date (90 days ago)
- `maxDate`: Maximum selectable date (today)
- `dateFormat`: Display format (dd/MM/yyyy = 24/02/2026)
- `locale`: Thai locale for month/day names
- `placeholderText`: Text when no date selected
- `required`: HTML5 validation
- `className`: Input field styles
- `calendarClassName`: Calendar popup styles
- `wrapperClassName`: Wrapper div styles

---

### 5. Custom Styles

Added `<style jsx global>` for calendar customization:

```jsx
<style jsx global>{`
  .custom-calendar {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  }

  .react-datepicker__day--selected {
    background-color: #3b82f6 !important;
    color: white !important;
  }

  .react-datepicker__day--today {
    background-color: #10b981 !important;
    color: white !important;
    font-weight: bold;
  }

  .react-datepicker__day--disabled {
    color: #d1d5db !important;
    text-decoration: line-through;
    cursor: not-allowed !important;
  }
`}</style>
```

**Styles:**
- `.custom-calendar`: White background, rounded, shadow
- `.react-datepicker__day--selected`: Blue background (selected date)
- `.react-datepicker__day--today`: Green background (today)
- `.react-datepicker__day--disabled`: Gray + strikethrough (disabled dates)

---

### 6. Validation

**Added date validation:**

```javascript
// Validate date
if (!formData.transfer_date) {
  setError('กรุณาเลือกวันที่โอน');
  setSubmitting(false);
  return;
}
```

---

### 7. Date Formatting for API

**No changes to API format!**

```javascript
// Build ISO datetime (same as before)
const paidAtDate = new Date(formData.transfer_date);
paidAtDate.setHours(hour, minute, 0, 0);

const year = paidAtDate.getFullYear();
const month = String(paidAtDate.getMonth() + 1).padStart(2, '0');
const day = String(paidAtDate.getDate()).padStart(2, '0');
const hourStr = String(paidAtDate.getHours()).padStart(2, '0');
const minuteStr = String(paidAtDate.getMinutes()).padStart(2, '0');
const paidAtISO = `${year}-${month}-${day}T${hourStr}:${minuteStr}:00`;
```

**API still receives:**
- `paid_at`: `"2026-02-24T14:30:00"` (ISO string)

---

## User Experience

### Before (Native Date Picker):
1. Tap date field
2. Browser shows native date picker (varies by browser/OS)
3. Select date
4. No visual indication of date range limits

### After (Custom Calendar):
1. Tap date field
2. **Custom calendar popup appears**
3. **Visual indicators:**
   - Today: Green circle
   - Selected: Blue circle
   - Disabled (>90 days ago): Gray + strikethrough
   - Disabled (future): Gray + strikethrough
4. Select date
5. Calendar closes automatically

---

## Date Range Examples

### Scenario 1: Today = Feb 24, 2026

| Date | Status | Reason |
|------|--------|--------|
| Nov 25, 2025 | ❌ Disabled | > 90 days ago |
| Nov 26, 2025 | ✅ Enabled | Exactly 90 days ago |
| Feb 23, 2026 | ✅ Enabled | Yesterday |
| Feb 24, 2026 | ✅ Enabled (Green) | Today |
| Feb 25, 2026 | ❌ Disabled | Future |

---

### Scenario 2: Today = Jan 15, 2026

| Date | Status | Reason |
|------|--------|--------|
| Oct 16, 2025 | ❌ Disabled | > 90 days ago |
| Oct 17, 2025 | ✅ Enabled | Exactly 90 days ago |
| Jan 14, 2026 | ✅ Enabled | Yesterday |
| Jan 15, 2026 | ✅ Enabled (Green) | Today |
| Jan 16, 2026 | ❌ Disabled | Future |

---

## API Compatibility

### ✅ No API Changes

**Create (POST /api/payins):**
```javascript
const submitFormData = new FormData();
submitFormData.append('amount', parseFloat(formData.amount));
submitFormData.append('paid_at', paidAtISO); // Same format
submitFormData.append('slip', formData.slip_image);

await payinsAPI.createFormData(submitFormData);
```

**Update (PUT /api/payins/{id}):**
```javascript
const jsonData = {
  amount: parseFloat(formData.amount),
  transfer_date: `${year}-${month}-${day}`, // Same format
  transfer_hour: parseInt(formData.transfer_hour),
  transfer_minute: parseInt(formData.transfer_minute),
  slip_image_url: formData.slip_preview
};

await payinsAPI.update(editPayin.id, jsonData);
```

**Backend receives exactly the same data format!**

---

## Testing Checklist

### ✅ Scenario 1: Create New Pay-in

1. Navigate to `/resident/submit`
2. Fill amount: `3000`
3. **Click date field → Calendar popup appears**
4. **Try to select date > 90 days ago → Should be disabled**
5. **Try to select future date → Should be disabled**
6. Select valid date (e.g., yesterday)
7. Fill HH: `14`, MM: `30`
8. Upload slip
9. Submit → Should succeed

---

### ✅ Scenario 2: Edit Existing Pay-in

1. Navigate to dashboard
2. Click "แก้ไข" on PENDING pay-in
3. **Date field should show existing date**
4. **Click date field → Calendar popup with pre-selected date**
5. Change date to another valid date
6. Submit → Should succeed

---

### ✅ Scenario 3: Date Validation

1. Navigate to `/resident/submit`
2. Fill amount: `3000`
3. **Do NOT select date**
4. Fill HH: `14`, MM: `30`
5. Upload slip
6. Submit → Should show error: "กรุณาเลือกวันที่โอน"

---

### ✅ Scenario 4: Visual Indicators

1. Open calendar
2. **Today should have green background**
3. **Selected date should have blue background**
4. **Disabled dates should be gray + strikethrough**
5. **Hover over enabled date → Light gray background**

---

## Troubleshooting

### Issue 1: Calendar doesn't show

**Cause:** CSS not imported

**Fix:**
```javascript
import 'react-datepicker/dist/react-datepicker.css';
```

---

### Issue 2: Thai locale not working

**Cause:** Locale not imported

**Fix:**
```javascript
import { th } from 'date-fns/locale';

<DatePicker locale={th} ... />
```

---

### Issue 3: Date format incorrect

**Cause:** Wrong `dateFormat` prop

**Fix:**
```javascript
<DatePicker dateFormat="dd/MM/yyyy" ... />
```

---

### Issue 4: Date range not working

**Cause:** `minDate` or `maxDate` not set

**Fix:**
```javascript
const today = startOfDay(new Date());
const minDate = subDays(today, 90);
const maxDate = today;

<DatePicker minDate={minDate} maxDate={maxDate} ... />
```

---

## Summary

### What Changed:
- ✅ Added react-datepicker
- ✅ Added date-fns for date manipulation
- ✅ Changed `transfer_date` from string to Date object
- ✅ Added date range limit (90 days back)
- ✅ Added custom calendar styles
- ✅ Added date validation

### What Stayed the Same:
- ✅ API format (ISO datetime string)
- ✅ All other validations
- ✅ Error handling
- ✅ File upload logic
- ✅ Edit mode support
- ✅ **No Policy changes**
- ✅ **No Status changes**
- ✅ **No API Contract changes**

### Result:
- ✅ Better UX (visual calendar)
- ✅ Date range enforcement (90 days)
- ✅ Thai locale support
- ✅ No backend changes needed
- ✅ **Guardrails respected**

