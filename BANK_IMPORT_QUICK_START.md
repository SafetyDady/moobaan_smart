# Quick Start: Bank Statement Import

## For System Administrators

### Prerequisites
- Login as super_admin or accounting user
- Navigate to: **Bank Statements** (from admin menu)

### Step 1: Create Bank Account (First Time Only)
1. Click **"Add Bank Account"**
2. Fill in:
   - **Bank Code:** e.g., `KBANK`, `SCB`, `BBL`
   - **Account Number (Masked):** e.g., `xxx-x-xxxxx-1234`
   - **Account Type:** `Cash Flow` or `Savings`
3. Click **"Add Account"**

### Step 2: Import Statement
1. **Select Bank Account** from dropdown
2. **Select Year** (e.g., 2025)
3. **Select Month** (e.g., December)
4. **Choose CSV File** (must be from the same month)
5. Click **"Preview CSV"**

### Step 3: Review Preview
The system will show:
- ✅ **Green** = All good, warnings only
- ❌ **Red** = Errors, import blocked
- ⚠️ **Yellow** = Warnings, can proceed

Check:
- Transaction count
- Date range
- Opening/Closing balance
- First ~100 transactions

### Step 4: Confirm or Fix
- **If errors:** Fix CSV file and try again
- **If warnings only:** Review and decide
- **If all good:** Click **"Confirm Import"**

### Step 5: Done!
- Batch appears in "Imported Batches" table
- Transactions stored in database
- Cannot re-import same month for same account

---

## Common Errors & Solutions

### ❌ "A statement batch for 2025-12 already exists"
**Cause:** You already imported this month for this account  
**Solution:** Delete old batch (contact developer) or use different month

### ❌ "Transaction #5 falls outside selected month"
**Cause:** CSV contains transactions from other months  
**Solution:** Ensure CSV only has transactions from selected month

### ❌ "Could not detect header row"
**Cause:** CSV doesn't have proper column headers  
**Solution:** Ensure CSV has headers like: วันที่, รายการ, ถอนเงิน, ฝากเงิน

### ❌ "Found X duplicate transaction(s)"
**Cause:** These transactions were already imported  
**Solution:** Check batch history, remove duplicates from CSV

---

## CSV File Requirements

### Required Columns (Thai or English):
- **Date:** วันที่ / date
- **Description:** รายการ / description
- **Debit:** ถอนเงิน / debit / withdraw
- **Credit:** ฝากเงิน / credit / deposit

### Optional Columns:
- **Balance:** ยอดคงเหลือ / balance
- **Channel:** ช่องทาง / channel

### Sample CSV Format:
```csv
ธนาคารกสิกรไทย จำกัด
รายการเดินบัญชี
เลขที่บัญชี: xxx-x-xxxxx-1234
รอบบัญชี: 01/12/2025 - 31/12/2025
ยอดยกมา: 125000.00

วันที่,รายการ,ถอนเงิน,ฝากเงิน,ยอดคงเหลือ,ช่องทาง
01/12/2025,ค่าธรรมเนียม,50.00,,124950.00,AUTO
02/12/2025,รับชำระ,,5000.00,129950.00,TRANSFER
...
```

**Notes:**
- Metadata rows above header are automatically ignored
- Numbers can have commas (e.g., 1,234.56)
- Empty debit/credit cells are OK (use one or the other)
- All dates must be DD/MM/YYYY format

---

## Tips for Best Results

1. **One Month Per File:** Don't mix multiple months
2. **Clean Data:** Remove totals/summary rows at bottom
3. **Check Dates:** All transactions should be in selected month
4. **Save Original:** Keep original bank file as backup
5. **Import Chronologically:** Start from oldest month first

---

## Need Help?

Contact: System Administrator or IT Support
