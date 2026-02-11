# Phase A: Pay-in State Machine + Admin-created Pay-in (Bank-first)

## Implementation Summary

**Date:** Session implemented successfully

## 1. Pay-in State Machine

### New Status Enum
Located in `backend/app/db/models/payin_report.py`:

```python
class PayinStatusEnum(str, Enum):
    # Phase A states
    DRAFT = "DRAFT"                         # Saved but not submitted
    SUBMITTED = "SUBMITTED"                 # Pending admin review
    REJECTED_NEEDS_FIX = "REJECTED_NEEDS_FIX"  # Rejected, resident can fix & resubmit
    ACCEPTED = "ACCEPTED"                   # Approved by admin
    
    # Legacy (preserved for backward compatibility)
    PENDING = "PENDING"
    REJECTED = "REJECTED"
```

### State Transitions
```
[Resident creates] → DRAFT → SUBMITTED → [Admin reviews]
                                         ↓
                              ACCEPTED (done)
                                   or
                              REJECTED_NEEDS_FIX → [Resident edits] → SUBMITTED → ...
```

### New PayinSource Enum (Audit Trail)
```python
class PayinSource(str, Enum):
    RESIDENT = "RESIDENT"           # Created by resident via slip upload
    ADMIN_CREATED = "ADMIN_CREATED" # Created by admin from unmatched bank tx
    LINE_RECEIVED = "LINE_RECEIVED" # Future: Created via LINE webhook
```

### New Model Fields
- `source`: PayinSource enum
- `created_by_admin_id`: FK to users (for ADMIN_CREATED)
- `admin_note`: Optional note from admin
- `reference_bank_transaction_id`: Link to bank tx for admin-created
- `submitted_at`: Timestamp when resident submitted

## 2. Backend API Endpoints

New router: `backend/app/api/payin_state.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/payin-state/rejection-reasons` | GET | Get preset rejection reasons |
| `/api/payin-state/{payin_id}/submit` | POST | Resident submits DRAFT → SUBMITTED |
| `/api/payin-state/{payin_id}/reject` | POST | Admin rejects → REJECTED_NEEDS_FIX |
| `/api/payin-state/{payin_id}/save-draft` | PUT | Save DRAFT without submitting |
| `/api/payin-state/unidentified-bank-credits` | GET | List unmatched CREDIT bank txs |
| `/api/payin-state/admin-create-from-bank` | POST | Admin creates pay-in from bank tx |
| `/api/payin-state/{payin_id}/attach-slip` | POST | Upload slip to admin-created pay-in |
| `/api/payin-state/review-queue` | GET | List pay-ins for admin review |

### Preset Rejection Reasons
```python
REJECTION_REASONS = [
    {"code": "WRONG_AMOUNT", "label": "จำนวนเงินไม่ตรง / Amount mismatch"},
    {"code": "WRONG_DATE", "label": "วันที่/เวลาไม่ตรง / Date/time mismatch"},
    {"code": "UNREADABLE_SLIP", "label": "สลิปไม่ชัด / Unreadable slip"},
    {"code": "DUPLICATE", "label": "ซ้ำกับรายการอื่น / Duplicate entry"},
    {"code": "WRONG_ACCOUNT", "label": "โอนผิดบัญชี / Wrong bank account"},
    {"code": "OTHER", "label": "อื่นๆ / Other"},
]
```

## 3. Frontend Updates

### Admin Pay-ins Page (`frontend/src/pages/admin/Payins.jsx`)
- ✅ Status filter tabs: Needs Review, Needs Fix, Accepted, Draft, All
- ✅ Reject modal with preset reasons + custom note field
- ✅ Slip preview modal
- ✅ Source badge display (Resident/Admin Created/LINE)
- ✅ Status counts in tabs

### Unidentified Receipts Page (`frontend/src/pages/admin/UnidentifiedReceipts.jsx`)
- ✅ NEW PAGE for bank-first flow
- ✅ Lists unmatched CREDIT bank transactions
- ✅ Create Pay-in modal with:
  - House selection
  - Source choice (Admin Created / LINE)
  - Admin note field
- ✅ Links bank tx to new pay-in (reference_bank_transaction_id)

### Resident Dashboard (`frontend/src/pages/resident/Dashboard.jsx`)
- ✅ Updated status badges with Thai labels
- ✅ Clear state display: ร่าง (Draft), รอตรวจสอบ (In Review), ต้องแก้ไข (Needs Fix), รับแล้ว (Accepted)
- ✅ Edit allowed only for DRAFT and REJECTED_NEEDS_FIX
- ✅ Admin note display for rejected pay-ins

### Submit Payment Page (`frontend/src/pages/resident/SubmitPayment.jsx`)
- ✅ Handle REJECTED_NEEDS_FIX status with admin note display
- ✅ DRAFT status display
- ✅ Clear feedback for each state

### Navigation (`frontend/src/components/Layout.jsx`)
- ✅ Added "Unidentified Receipts" sidebar link for super_admin
- ✅ Added "Unidentified Receipts" sidebar link for accounting role

### Routes (`frontend/src/App.jsx`)
- ✅ `/admin/unidentified-receipts`
- ✅ `/accounting/unidentified-receipts`

## 4. Database Migration

Migration script: `backend/run_phase_a_migration.py`

Added:
- PayinStatus enum values: DRAFT, SUBMITTED, REJECTED_NEEDS_FIX
- PayinSource enum with values: RESIDENT, ADMIN_CREATED, LINE_RECEIVED
- Columns: source, created_by_admin_id, admin_note, reference_bank_transaction_id, submitted_at

## 5. Key Design Decisions

### No Auto-Accept
- Accept is ALWAYS a manual admin action
- Even matched bank tx requires explicit Accept click

### Bank Data Untouched
- Bank transactions are read-only
- Creating pay-in from bank tx only stores reference_bank_transaction_id
- Actual bank transaction record is not modified

### No Ledger in Phase A
- Accept does NOT create ledger entries
- Ledger creation happens in later phase (Phase B)

### Audit Trail
- Every pay-in has `source` field
- Admin-created pay-ins have `created_by_admin_id`
- Bank reference preserved via `reference_bank_transaction_id`

## 6. Testing Checklist

### State Machine Flow
- [ ] Create pay-in as resident → DRAFT/SUBMITTED
- [ ] Admin rejects → REJECTED_NEEDS_FIX
- [ ] Resident edits and resubmits → SUBMITTED
- [ ] Admin accepts → ACCEPTED

### Admin-Created Pay-in from Bank
- [ ] Navigate to Unidentified Receipts
- [ ] See unmatched CREDIT transactions
- [ ] Create Pay-in from bank tx
- [ ] Verify house is assigned
- [ ] Verify bank tx is linked (reference_bank_transaction_id)
- [ ] Accept the created pay-in

### Resident UI
- [ ] Dashboard shows correct Thai status labels
- [ ] Can edit DRAFT pay-ins
- [ ] Can edit REJECTED_NEEDS_FIX pay-ins
- [ ] Cannot edit SUBMITTED or ACCEPTED pay-ins
- [ ] Admin note shown for rejected pay-ins

## 7. URLs

- Frontend: http://127.0.0.1:5173/
- Backend: http://127.0.0.1:8000/
- Admin Pay-ins: http://127.0.0.1:5173/admin/payins
- Unidentified Receipts: http://127.0.0.1:5173/admin/unidentified-receipts
- Resident Dashboard: http://127.0.0.1:5173/resident/dashboard

## 8. Files Modified/Created

### Backend
- `backend/app/db/models/payin_report.py` - Modified (enums + fields)
- `backend/app/api/payin_state.py` - Created (new router)
- `backend/app/api/payins.py` - Modified (use new enums)
- `backend/app/main.py` - Modified (register router)
- `backend/run_phase_a_migration.py` - Created (migration script)

### Frontend
- `frontend/src/pages/admin/Payins.jsx` - Modified (tabs + reject modal)
- `frontend/src/pages/admin/UnidentifiedReceipts.jsx` - Created
- `frontend/src/pages/resident/Dashboard.jsx` - Modified (status display)
- `frontend/src/pages/resident/SubmitPayment.jsx` - Modified (state handling)
- `frontend/src/components/Layout.jsx` - Modified (sidebar)
- `frontend/src/App.jsx` - Modified (routes)

## 9. Next Phase (Phase B)

After Phase A is validated:
- Add ledger entry creation on Accept
- Connect invoice payment tracking
- Add payment reconciliation reports
---

## 10. Phase A.1.x Hardening (2026-01-19)

### Overview
Phase A.1.x focuses on Resident Pay-in mobile UX with proper status-based action rules.

### Key Changes

#### 10.1 Status Flow Updated

| Before A.1.x | After A.1.x |
|-------------|-------------|
| Create → DRAFT → SUBMITTED | Create → **PENDING** directly |
| PENDING = legacy state | PENDING = **primary editable state** |
| Edit → SUBMITTED | Edit → **keeps PENDING** |

#### 10.2 Single-Open Rule
Only ONE open Pay-in per house at a time. Blocking statuses:
- DRAFT
- PENDING
- REJECTED_NEEDS_FIX
- SUBMITTED

Only `ACCEPTED` status allows creating a new Pay-in.

#### 10.3 PENDING Status Rules
| Action | Allowed |
|--------|---------|
| View | ✅ |
| Edit | ✅ |
| Delete | ❌ **No** |

> PENDING can be edited but NOT deleted. Resident must edit to correct mistakes.

#### 10.4 Backend Changes
- `backend/app/api/payins.py`:
  - Create endpoint: `status=PayinStatusEnum.PENDING`
  - Update endpoint: keeps `status=PayinStatusEnum.PENDING`
  - Single-open rule blocking check

#### 10.5 Frontend Changes
- `frontend/src/utils/payinStatus.js`:
  - `EDITABLE_STATUSES`: DRAFT, PENDING, REJECTED_NEEDS_FIX
  - `DELETABLE_STATUSES`: DRAFT, REJECTED_NEEDS_FIX (NOT PENDING)
  - `BLOCKING_STATUSES`: DRAFT, PENDING, REJECTED_NEEDS_FIX, SUBMITTED

#### 10.6 Migration Script
`backend/fix_submitted_to_pending.py` - Converts existing SUBMITTED → PENDING

### Testing Checklist A.1.x
- [x] Create Pay-in → status is PENDING
- [x] Edit Pay-in → status stays PENDING
- [x] Edit button visible for PENDING
- [x] Delete button NOT visible for PENDING
- [x] Cannot create new Pay-in if PENDING exists
- [x] ACCEPTED allows creating new Pay-in