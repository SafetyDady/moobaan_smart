# Phase A.1: Hardening – Unidentified Receipts & Resident Payment Detail

**Project:** Moobaan Smart – Village Accounting  
**Phase:** A.1 (Hardening)  
**Status:** Specification  
**Created:** January 19, 2026  

---

## 1. Goal of Phase A.1 (Hardening)

### 1.1 Purpose

Phase A.1 is a **polish and hardening phase**, not a redesign. The core accounting rules and state machine from Phase A remain unchanged. This phase addresses usability gaps and audit requirements discovered during real-world UI testing.

### 1.2 Primary Objectives

1. **Make Unidentified Receipts operational** for Admin/Accounting staff
   - Fix critical date display bug that renders the page unusable
   - Enable slip attachment for audit trail completeness

2. **Provide Resident read-only payment detail view**
   - Allow residents to review their payment submissions clearly
   - Show admin feedback (rejection reason, notes) in accessible format

### 1.3 Success Criteria

- Admin can use Unidentified Receipts page without "Invalid Date" errors
- Admin-created Pay-ins have audit-compliant slip evidence attachment
- Residents can view full payment details in read-only mode after submission

---

## 2. Problems Observed (from Real UI)

### 2.1 Critical: Invalid Date Display

**Location:** `/admin/unidentified-receipts` and `/accounting/unidentified-receipts`

**Symptom:**
- All rows in the Unidentified Receipts table show "Invalid Date" in the date column
- This makes the page unusable for Admin/Accounting staff

**Impact:** High – Cannot identify which bank transactions need attention

**Likely Causes:**
1. Backend returns field name mismatch (e.g., `effective_at` vs `transaction_date`)
2. Backend returns timestamp in unexpected format
3. Frontend attempts `new Date()` on null/undefined value
4. Frontend references wrong field name from API response

### 2.2 Audit Gap: No Slip Attachment for Admin-Created Pay-ins

**Location:** Create Pay-in modal in Unidentified Receipts

**Symptom:**
- When Admin creates Pay-in from unidentified bank credit, there is no way to attach slip evidence
- Pay-ins created this way have `slip_url = null`

**Impact:** Medium – Audit trail incomplete; no evidence linking bank transaction to resident payment

**Business Context:**
- Admin often receives slip via LINE or email
- This evidence should be attached to the Pay-in record for compliance

### 2.3 UX Gap: Resident Cannot View Payment Details

**Location:** Resident Dashboard → Payment History

**Symptom:**
- Resident can see payment list with status badges
- No way to tap/click into a payment to see full details
- Cannot easily read rejection reason or admin notes

**Impact:** Medium – Poor user experience; residents cannot understand why payment was rejected

---

## 3. Non-Goals / Constraints

### 3.1 Do NOT Change Reconciliation Core Rules

The following rules are **immutable** in this phase:

| Rule | Description |
|------|-------------|
| Accept requires matched statement | Pay-in can only be accepted after matching with bank statement |
| 1:1 matching | One bank transaction matches exactly one Pay-in |
| No auto-accept | Accept is always a manual admin action |
| Ledger on accept only | IncomeTransaction created only when Accept is clicked |

### 3.2 Do NOT Redesign Database

- Prefer using existing columns and relationships
- Only add new columns if absolutely necessary
- No schema migrations that break existing data

### 3.3 Minimal Additive Changes

- Fix bugs with minimal code changes
- Reuse existing components where possible
- Avoid introducing new dependencies

---

## 4. Required Changes (Detailed)

### 4.1 Fix Invalid Date Display

#### 4.1.1 Root Cause Analysis

**Backend API:** `GET /api/payin-state/unidentified-bank-credits`

**Current Response Format (suspected):**
```json
{
  "transactions": [
    {
      "id": "uuid",
      "effective_at": "2025-12-27T05:37:00+07:00",
      "amount": 4200.00,
      "description": "...",
      ...
    }
  ]
}
```

**Frontend Code (UnidentifiedReceipts.jsx):**
```jsx
<td>{new Date(tx.transaction_date).toLocaleDateString('th-TH')}</td>
```

**Problem:** Frontend references `tx.transaction_date` but backend returns `tx.effective_at`

#### 4.1.2 Required Backend Response Format

Standardize on ISO 8601 with timezone:

```json
{
  "count": 5,
  "transactions": [
    {
      "id": "dae414ee-1f29-4a43-8227-72b2e0274181",
      "effective_at": "2025-12-27T05:37:00+07:00",
      "amount": 4200.00,
      "description": "TRANSFER FROM ...",
      "channel": "MOBILE",
      "bank_account_id": "uuid",
      "created_at": "2025-12-27T06:00:00+07:00"
    }
  ]
}
```

#### 4.1.3 Required Frontend Fix

Option A (Preferred): Fix field name reference
```jsx
// Change from:
new Date(tx.transaction_date).toLocaleDateString('th-TH')

// To:
new Date(tx.effective_at).toLocaleDateString('th-TH')
```

Option B: Add defensive parsing with fallback
```jsx
const txDate = tx.effective_at || tx.transaction_date || tx.created_at;
const displayDate = txDate 
  ? new Date(txDate).toLocaleDateString('th-TH')
  : '-';
```

#### 4.1.4 Acceptance Criteria

- [ ] All rows in Unidentified Receipts show valid date in `DD/MM/YYYY` Thai format
- [ ] No "Invalid Date" text visible
- [ ] Date matches the `effective_at` from bank statement
- [ ] Works for both Admin and Accounting roles

---

### 4.2 Admin-Created Pay-in: Attach Slip

#### 4.2.1 UI Change

**Location:** Create Pay-in modal in UnidentifiedReceipts.jsx

**Current Modal Fields:**
- House selection (dropdown)
- Source selection (ADMIN_CREATED / LINE_RECEIVED)
- Admin note (textarea)

**Add New Field:**
- Slip image upload (file input accepting image/*)
- Preview thumbnail after selection
- Optional: paste from clipboard support

**Wireframe:**
```
┌─────────────────────────────────────────┐
│ สร้าง Pay-in จากรายการธนาคาร            │
├─────────────────────────────────────────┤
│ วันที่: 27/12/2025                      │
│ จำนวนเงิน: ฿4,200                       │
│ รายละเอียด: TRANSFER FROM...           │
├─────────────────────────────────────────┤
│ บ้าน *                                  │
│ [▼ -- เลือกบ้าน --                    ] │
│                                         │
│ แหล่งที่มา                              │
│ [▼ Admin สร้าง                        ] │
│                                         │
│ แนบสลิป (ถ้ามี)                         │
│ [📎 เลือกไฟล์...] หรือ วางรูปที่นี่     │
│ ┌─────────┐                             │
│ │ preview │  (shows after selection)    │
│ └─────────┘                             │
│                                         │
│ หมายเหตุ (ถ้ามี)                        │
│ ┌─────────────────────────────────────┐ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│        [ยกเลิก]  [สร้าง Pay-in]         │
└─────────────────────────────────────────┘
```

#### 4.2.2 Backend Changes

**Option A (Preferred):** Modify existing endpoint to accept multipart/form-data

Endpoint: `POST /api/payin-state/admin-create-from-bank`

Current: JSON body
```json
{
  "bank_transaction_id": "uuid",
  "house_id": 6,
  "source": "LINE_RECEIVED",
  "admin_note": "..."
}
```

New: multipart/form-data
```
bank_transaction_id: uuid
house_id: 6
source: LINE_RECEIVED
admin_note: ...
slip: (binary file)
```

**Storage:** Reuse existing slip upload mechanism
- Store to same location as resident slip uploads
- Set `slip_url` field on PayinReport

**Option B:** Two-step process
1. Create Pay-in (returns payin_id)
2. Call existing `POST /api/payin-state/{payin_id}/attach-slip`

#### 4.2.3 Acceptance Criteria

- [ ] Modal shows file upload field for slip
- [ ] Admin can select image file (jpg, png, pdf)
- [ ] Preview shows before submission
- [ ] Created Pay-in has `slip_url` populated
- [ ] Slip is accessible via existing slip view mechanism
- [ ] Works without slip (optional field)

---

### 4.3 Resident Payment Detail View (Read-Only)

#### 4.3.1 UI Entry Points

**From Dashboard:**
- Payment history table row → Click/tap → Open detail view

**From Mobile Dashboard:**
- Same behavior, mobile-optimized layout

#### 4.3.2 Detail View Content

**Header:**
- Status badge (prominent)
- House number

**Main Content:**
| Field | Source |
|-------|--------|
| จำนวนเงิน (Amount) | `payin.amount` |
| วันที่โอน (Transfer Date) | `payin.transfer_date` |
| เวลาโอน (Transfer Time) | `payin.transfer_hour:transfer_minute` |
| สลิป (Slip) | Link to `payin.slip_url` if exists |
| สถานะ (Status) | `payin.status` with Thai label |
| เหตุผลที่ปฏิเสธ (Rejection Reason) | `payin.rejection_reason` (if REJECTED_NEEDS_FIX) |
| หมายเหตุจากแอดมิน (Admin Note) | `payin.admin_note` (if exists) |
| วันที่ส่ง (Submitted At) | `payin.submitted_at` |
| วันที่รับ (Accepted At) | `payin.accepted_at` (if ACCEPTED) |

**Actions (conditional):**

| Status | Available Actions |
|--------|-------------------|
| DRAFT | Edit, Delete, Submit |
| SUBMITTED | None (read-only) |
| REJECTED_NEEDS_FIX | Edit & Resubmit |
| ACCEPTED | None (read-only) |

#### 4.3.3 Editability Rules

```
DRAFT              → Editable (all fields)
SUBMITTED          → Read-only (pending review)
REJECTED_NEEDS_FIX → Editable (fix and resubmit)
ACCEPTED           → Read-only (terminal state)
```

#### 4.3.4 Implementation Approach

**Option A (Preferred):** Modal/Drawer
- Click row → Open modal with full details
- Simpler navigation, no new route

**Option B:** Dedicated page
- Click row → Navigate to `/resident/payment/{id}`
- Full page with back button

#### 4.3.5 Acceptance Criteria

- [ ] Resident can tap/click any payment row to see details
- [ ] All relevant fields displayed clearly
- [ ] Slip image opens in new tab/modal when clicked
- [ ] Rejection reason prominently displayed for REJECTED_NEEDS_FIX
- [ ] Edit button visible only for DRAFT and REJECTED_NEEDS_FIX
- [ ] No edit option for SUBMITTED or ACCEPTED
- [ ] Works on both desktop and mobile

---

## 5. Test Plan (Manual)

### 5.1 Test Case: Invalid Date Fix

**Precondition:** Bank statement imported with CREDIT transactions not yet matched

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as Admin | Dashboard loads |
| 2 | Navigate to Unidentified Receipts | Page loads without error |
| 3 | Observe date column | All dates show valid format (e.g., 27/12/2568) |
| 4 | Verify date accuracy | Dates match bank statement effective_at |
| 5 | Test with Accounting role | Same behavior |

### 5.2 Test Case: Admin Attach Slip

**Precondition:** Unidentified CREDIT exists

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click "สร้าง Pay-in" on unidentified row | Modal opens |
| 2 | Select house | House dropdown works |
| 3 | Click file upload | File picker opens |
| 4 | Select JPG image | Preview shows in modal |
| 5 | Fill admin note | Text accepted |
| 6 | Click "สร้าง Pay-in" | Success message |
| 7 | Navigate to Pay-ins review | New pay-in visible |
| 8 | Check slip column | Slip link present |
| 9 | Click slip link | Image opens correctly |

### 5.3 Test Case: Admin Create Without Slip

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open create modal | Modal opens |
| 2 | Select house only | House selected |
| 3 | Leave slip empty | No error |
| 4 | Click create | Success (slip optional) |

### 5.4 Test Case: Resident View Detail (Desktop)

**Precondition:** Resident has payments in various states

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as Resident | Dashboard loads |
| 2 | Scroll to payment history | List visible |
| 3 | Click SUBMITTED payment | Detail modal opens |
| 4 | Verify all fields shown | Amount, date, time, status visible |
| 5 | Verify no Edit button | Read-only for SUBMITTED |
| 6 | Close modal | Returns to dashboard |
| 7 | Click REJECTED_NEEDS_FIX payment | Detail opens |
| 8 | Verify rejection reason shown | Reason prominently displayed |
| 9 | Verify Edit button present | Can click to edit |

### 5.5 Test Case: Resident View Detail (Mobile)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open on mobile device/emulator | Mobile layout loads |
| 2 | Login as Resident | Mobile dashboard |
| 3 | Tap payment row | Detail view opens |
| 4 | Verify touch-friendly layout | All fields readable |
| 5 | Tap slip image | Opens full size |
| 6 | Test back navigation | Returns to dashboard |

### 5.6 Test Case: Regression – Matching Still Works

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create resident pay-in | Status = SUBMITTED |
| 2 | Admin opens Pay-ins | Pay-in visible |
| 3 | Click Match | Modal opens with candidates |
| 4 | Select matching bank tx | Match succeeds |
| 5 | Verify is_matched = true | Badge shows matched |
| 6 | Click Accept | Ledger entry created |
| 7 | Verify status = ACCEPTED | Pay-in locked |

### 5.7 Test Case: Regression – Accept Requires Match

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find unmatched SUBMITTED pay-in | Accept button disabled |
| 2 | Hover/click Accept | Tooltip: "Must match first" |
| 3 | Match the pay-in | Accept button enables |
| 4 | Accept | Success |

---

## 6. Rollback & Safety

### 6.1 Verification Checklist (Post-Deployment)

| Check | How to Verify |
|-------|---------------|
| Matching works | Create pay-in → Match → Verify is_matched |
| Accept creates ledger | Accept matched pay-in → Check income_transactions table |
| 1:1 constraint | Try matching same bank tx twice → Should fail |
| No auto-accept | Admin-created pay-in starts as SUBMITTED, not ACCEPTED |

### 6.2 Logs to Monitor

| Log Source | What to Watch |
|------------|---------------|
| Backend stdout | HTTP 500 errors on payin-state endpoints |
| Browser console | JavaScript errors on UnidentifiedReceipts |
| Database | Orphaned income_transactions (should not exist) |

### 6.3 Rollback Procedure

If critical issues found:

1. **Frontend rollback:** Revert to previous build
2. **Backend rollback:** Redeploy previous container/code
3. **Database:** No schema changes in A.1, so no DB rollback needed

### 6.4 Safe Deployment Order

1. Deploy backend changes first (backward compatible)
2. Test API endpoints directly
3. Deploy frontend changes
4. Run manual test plan
5. Monitor for 24 hours

---

## Appendix: File Reference

| Component | File Path |
|-----------|-----------|
| Unidentified Receipts UI | `frontend/src/pages/admin/UnidentifiedReceipts.jsx` |
| Unidentified API | `backend/app/api/payin_state.py` |
| Resident Dashboard | `frontend/src/pages/resident/Dashboard.jsx` |
| Mobile Dashboard | `frontend/src/pages/resident/mobile/MobileDashboard.jsx` |
| PayinReport Model | `backend/app/db/models/payin_report.py` |

---

**End of Specification**
