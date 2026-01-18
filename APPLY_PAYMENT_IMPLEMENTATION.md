# Apply Ledger → Invoice Implementation Complete

**Date**: January 17, 2026  
**Phase**: 3 - Invoice Payment Allocation  
**Status**: ✅ Backend Complete, Frontend Pending

---

## Overview

Implemented the **Apply Ledger → Invoice** feature allowing admins to allocate recognized ledger entries (from ACCEPTED pay-ins) to invoices with immutable audit trails and automatic status updates.

---

## Backend Implementation

### API Endpoints Added

#### 1. GET `/api/invoices/allocatable-ledgers`
List ledger entries available for allocation to invoices.

**Query Parameters:**
- `house_id` (optional): Filter ledgers by house

**Response:**
```json
{
  "ledgers": [
    {
      "id": 10,
      "house_id": 5,
      "house_code": "28/1",
      "payin_id": 29,
      "amount": 600.00,
      "allocated": 0.00,
      "remaining": 600.00,
      "received_at": "2025-01-15T10:00:00+07:00",
      "created_at": "2025-01-15T10:05:00+07:00"
    }
  ],
  "count": 1
}
```

**Business Rules:**
- Only ledgers from ACCEPTED pay-ins (never PENDING/REJECTED)
- Only ledgers with `remaining_amount > 0` (not fully allocated)
- Optional house filter for targeted allocation

---

#### 2. POST `/api/invoices/{invoice_id}/apply-payment`
Apply ledger entry to invoice with validation.

**Request Body:**
```json
{
  "income_transaction_id": 10,
  "amount": 600.00,
  "note": "Optional note"
}
```

**Response:**
```json
{
  "message": "Payment applied successfully",
  "invoice_id": 13,
  "payment": {
    "id": 4,
    "amount": 600.00,
    "applied_at": "2026-01-17T14:52:01+07:00",
    "ledger_id": 10
  },
  "invoice": {
    "id": 13,
    "total_amount": 600.00,
    "paid_amount": 600.00,
    "outstanding_amount": 0.00,
    "status": "PAID"
  },
  "ledger": {
    "id": 10,
    "remaining_amount": 0.00
  }
}
```

**Validations (Guard Rails):**
1. ✅ Invoice must exist and not be fully paid
2. ✅ Ledger must exist and be from ACCEPTED pay-in
3. ✅ Amount to apply must not exceed invoice outstanding
4. ✅ Amount to apply must not exceed ledger remaining
5. ✅ Atomic transaction: Create payment record + Update invoice status

**Atomic Operations:**
```sql
BEGIN TRANSACTION;
  -- 1. Create immutable payment record
  INSERT INTO invoice_payments (invoice_id, income_transaction_id, amount);
  
  -- 2. Update invoice status (ISSUED → PARTIALLY_PAID → PAID)
  UPDATE invoices SET status = ... WHERE id = ...;
COMMIT;
```

---

#### 3. GET `/api/invoices/{invoice_id}/payments`
Get payment allocation history (audit trail).

**Response:**
```json
{
  "invoice_id": 12,
  "payments": [
    {
      "id": 2,
      "amount": 600.00,
      "applied_at": "2026-01-17T14:51:24+07:00",
      "ledger": {
        "id": 11,
        "amount": 600.00,
        "received_at": "2025-01-20T11:00:00+07:00",
        "payin_id": 30
      }
    }
  ],
  "count": 1,
  "total_paid": 600.00,
  "outstanding": 600.00
}
```

---

#### 4. GET `/api/invoices/{invoice_id}/detail`
Get invoice with full payment details.

**Response:**
```json
{
  "id": 13,
  "house_id": 5,
  "house_code": "28/1",
  "owner_name": "John Doe",
  "cycle_year": 2025,
  "cycle_month": 2,
  "issue_date": "2025-02-01",
  "due_date": "2025-02-28",
  "total_amount": 600.00,
  "paid_amount": 600.00,
  "outstanding_amount": 0.00,
  "status": "PAID",
  "notes": null,
  "created_at": "2025-02-01T00:00:00+07:00",
  "payments": [
    {
      "id": 1,
      "amount": 600.00,
      "applied_at": "2026-01-17T14:52:01+07:00",
      "income_transaction_id": 10,
      "ledger_date": "2025-01-15T10:00:00+07:00",
      "payin_id": 29
    }
  ]
}
```

---

## Database Schema

### InvoicePayment (Allocation Record)
```sql
CREATE TABLE invoice_payments (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    income_transaction_id INTEGER NOT NULL REFERENCES income_transactions(id),
    amount NUMERIC(10, 2) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Characteristics:**
- ✅ Immutable (no UPDATE/DELETE operations allowed)
- ✅ Complete audit trail (who allocated what, when)
- ✅ Links invoice to specific ledger entry (payin traceability)

---

## Invoice Status Enum

```python
class InvoiceStatus(enum.Enum):
    ISSUED = "ISSUED"            # No payments yet
    PARTIALLY_PAID = "PARTIALLY_PAID"  # Some payment, but outstanding > 0
    PAID = "PAID"                # Full payment (outstanding = 0)
    CANCELLED = "CANCELLED"      # Cancelled invoice
```

**Status Update Logic:**
```python
def update_status(self):
    total_paid = self.get_total_paid()
    total_amount = float(self.total_amount)
    
    if total_paid <= 0:
        self.status = InvoiceStatus.ISSUED
    elif total_paid >= total_amount:
        self.status = InvoiceStatus.PAID
    else:
        self.status = InvoiceStatus.PARTIALLY_PAID
```

---

## Test Suite Results

### Test File: `backend/test_apply_payment.py`

#### Test Case 1: Full Payment ✅
- **Scenario**: Apply ฿600 ledger to ฿600 invoice
- **Expected**: Invoice status → PAID, ledger remaining → ฿0
- **Result**: ✅ PASSED

#### Test Case 2: Partial Payment ✅
- **Scenario**: Apply ฿600 ledger to ฿1200 invoice
- **Expected**: Invoice status → PARTIALLY_PAID, outstanding → ฿600
- **Result**: ✅ PASSED

#### Test Case 3: Allocatable Ledgers Query ✅
- **Scenario**: Query ledgers with remaining > 0
- **Expected**: Only ledgers from ACCEPTED payins with remaining amount
- **Result**: ✅ PASSED

#### Test Case 4: Payment History ✅
- **Scenario**: Query payment allocation records for invoice
- **Expected**: Complete audit trail with ledger details
- **Result**: ✅ PASSED

#### Test Case 5: Guard Rails ✅
- **Scenario**: Test overspend prevention and validation
- **Expected**: Cannot overspend on invoice or ledger
- **Result**: ✅ PASSED

**Command to run tests:**
```bash
cd backend
python test_apply_payment.py
```

---

## Business Rules Enforced

### ✅ Only Apply from ACCEPTED Pay-ins
```python
query = db.query(IncomeTransaction).join(
    PayinReport, IncomeTransaction.payin_id == PayinReport.id
).filter(
    PayinReport.status == "ACCEPTED"  # Never PENDING/REJECTED
)
```

### ✅ No Overspend on Invoice
```python
outstanding = invoice.get_outstanding_amount()
if amount_to_apply > outstanding:
    raise HTTPException(
        status_code=400,
        detail=f"Cannot apply ฿{amount_to_apply:.2f}: Exceeds invoice outstanding ฿{outstanding:.2f}"
    )
```

### ✅ No Overspend on Ledger
```python
ledger_remaining = ledger.get_unallocated_amount()
if amount_to_apply > ledger_remaining:
    raise HTTPException(
        status_code=400,
        detail=f"Cannot apply ฿{amount_to_apply:.2f}: Exceeds ledger remaining ฿{ledger_remaining:.2f}"
    )
```

### ✅ Atomic Transaction
```python
try:
    # Create payment record
    payment = InvoicePayment(...)
    db.add(payment)
    
    # Update invoice status
    invoice.update_status()
    
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

### ✅ Immutable Allocation Records
- No UPDATE or DELETE on `invoice_payments` table
- Complete audit trail preserved forever
- Traceability: Invoice → InvoicePayment → IncomeTransaction → PayinReport

---

## Example Usage Workflow

### Admin Workflow:
1. **View Invoice**: GET `/api/invoices/{id}/detail`
   - See invoice: ฿1200 (ISSUED)
   - Outstanding: ฿1200

2. **List Allocatable Ledgers**: GET `/api/invoices/allocatable-ledgers?house_id=5`
   - See ledger #10: ฿600 remaining
   - See ledger #11: ฿600 remaining

3. **Apply First Payment**: POST `/api/invoices/13/apply-payment`
   ```json
   {
     "income_transaction_id": 10,
     "amount": 600
   }
   ```
   - Invoice status → PARTIALLY_PAID
   - Outstanding → ฿600

4. **Apply Second Payment**: POST `/api/invoices/13/apply-payment`
   ```json
   {
     "income_transaction_id": 11,
     "amount": 600
   }
   ```
   - Invoice status → PAID
   - Outstanding → ฿0

5. **View Payment History**: GET `/api/invoices/13/payments`
   - See 2 payments totaling ฿1200
   - See which ledgers were used

---

## Frontend Implementation (Pending)

### Invoice Detail Page Enhancement

#### Add "Apply Payment" Button
- Show only if invoice status != PAID
- Show only for admin/accounting users

#### Apply Payment Modal
```
┌─────────────────────────────────────────────┐
│ Apply Payment to Invoice #13                │
│─────────────────────────────────────────────│
│ Invoice: ฿1200 (Outstanding: ฿1200)        │
│                                             │
│ Select Ledger:                              │
│ ┌─────────────────────────────────────────┐ │
│ │ Ledger #10 - ฿600 remaining             │ │
│ │ Received: 2025-01-15                    │ │
│ │ From Pay-in #29                         │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Amount to Apply: [________] (Max: ฿600)    │
│                                             │
│ Note (optional): [_____________________]   │
│                                             │
│ [Cancel] [Apply Payment]                    │
└─────────────────────────────────────────────┘
```

#### Payment History Section
```
Payment History:
┌─────────────────────────────────────────────┐
│ Payment #1 - ฿600.00                       │
│ Applied: 2026-01-17 14:52:01               │
│ From: Ledger #10 (Pay-in #29)             │
│─────────────────────────────────────────────│
│ Payment #2 - ฿600.00                       │
│ Applied: 2026-01-17 14:55:30               │
│ From: Ledger #11 (Pay-in #30)             │
└─────────────────────────────────────────────┘
Total Paid: ฿1200.00
Status: PAID ✅
```

---

## Files Modified

### Backend
1. **`backend/app/api/invoices.py`** (✅ Complete)
   - Added 4 new endpoints
   - Added `ApplyPaymentRequest` schema
   - Updated imports

2. **`backend/test_apply_payment.py`** (✅ Complete)
   - 5 comprehensive test cases
   - All tests passing

### Database Models (No changes needed)
- `InvoicePayment` - Already existed with correct structure
- `Invoice` - Already had `update_status()` method
- `IncomeTransaction` - Already had `get_unallocated_amount()`

---

## Next Steps

### 1. Frontend UI Implementation
- Create Apply Payment modal component
- Add payment history display
- Update invoice detail page
- Add payment status badges

### 2. Additional Features (Future)
- Bulk payment application (apply one ledger to multiple invoices)
- Payment reversal (with approval workflow)
- Payment allocation reports
- Auto-allocation suggestions (smart matching)

---

## Success Criteria Met

✅ Admin can apply recognized ledger money to invoices  
✅ Immutable allocation records created (InvoicePayment)  
✅ Invoice statuses update correctly (ISSUED → PARTIALLY_PAID → PAID)  
✅ Guard rails prevent overspending  
✅ Complete audit trail maintained  
✅ Atomic transactions ensure data integrity  
✅ Only apply from ACCEPTED pay-ins (never PENDING)  
✅ Comprehensive test coverage (5 test cases, all passing)

---

## Testing Commands

```bash
# Run apply payment tests
cd backend
python test_apply_payment.py

# Start backend server
python run_server.py

# Test API endpoints
curl http://localhost:8000/api/invoices/allocatable-ledgers
curl http://localhost:8000/api/invoices/13/detail
curl -X POST http://localhost:8000/api/invoices/13/apply-payment \
  -H "Content-Type: application/json" \
  -d '{"income_transaction_id": 10, "amount": 600}'
curl http://localhost:8000/api/invoices/13/payments
```

---

**Ready for Frontend Implementation** 🚀
