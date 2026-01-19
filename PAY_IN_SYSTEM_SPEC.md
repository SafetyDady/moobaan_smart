# Pay-in System Specification

**Project:** Moobaan Smart – Village Accounting  
**Document Type:** Authoritative System Specification  
**Version:** 1.0  
**Created:** January 19, 2026  
**Status:** LOCKED – Production Reference  

---

## 1. Purpose of This Document

This document defines the **final, agreed system behavior** for the Pay-in / Payment reporting system in Moobaan Smart.

**This document:**
- Prevents future misunderstanding between stakeholders
- Locks UX and Role boundaries
- Reduces development scope creep
- Serves as the single source of truth for Admin, Accounting, and Developers

**Authority:** If behavior is not described in this document, it is not implemented.

---

## 2. User Platform Policy

### 2.1 Platform Assignment by Role

| Role | Platform | Rationale |
|------|----------|-----------|
| **Resident** | Mobile ONLY | 100% of residents use mobile devices |
| **Admin** | Desktop ONLY | Administrative tasks require full screen |
| **Accounting** | Desktop ONLY | Financial review requires detailed views |

### 2.2 Explicit Platform Restrictions

#### Resident Platform Policy

> **THERE IS NO RESIDENT DESKTOP UI.**

- Desktop access by Resident is **unsupported by design**
- If a Resident accesses the system via desktop browser, they will see the **mobile UI**
- No desktop-specific features (hover states, wide tables, keyboard shortcuts) exist for Residents
- This is an intentional product decision, not a bug

#### Admin/Accounting Platform Policy

- Admin and Accounting roles use **desktop-only** interfaces
- Mobile access for Admin/Accounting is not supported
- UI assumes mouse, keyboard, and large screen

---

## 3. Resident Capabilities (Mobile-Only)

### 3.1 What Residents CAN Do

| Capability | Conditions |
|------------|------------|
| View Pay-in list | All statuses visible |
| View Pay-in details | All statuses (read-only for non-editable) |
| Create new Pay-in | Only if no open Pay-in exists (single-open rule) |
| Edit Pay-in | Only when status is: `PENDING`, `REJECTED_NEEDS_FIX`, `DRAFT` |
| Delete Pay-in | Only when status is: `REJECTED_NEEDS_FIX`, `DRAFT` **(NOT PENDING)** |
| Upload/replace payment slip | Only when Pay-in is editable |
| View rejection reason | Read-only, shown prominently |
| View admin notes | Read-only |

> **A.1.x Rule:** PENDING status is editable but NOT deletable. Resident must edit to fix mistakes.

### 3.2 What Residents CANNOT Do

| Prohibited Action | Reason |
|-------------------|--------|
| Edit or delete `ACCEPTED` Pay-in | Terminal state, immutable |
| Edit or delete `SUBMITTED` Pay-in (post-review) | Under review, locked |
| Perform bank statement matching | Admin-only function |
| Accept or reject Pay-ins | Admin-only function |
| Access Ledger records | Admin/Accounting only |
| Access Invoice records | Admin/Accounting only |
| Use desktop-specific UI elements | Mobile-only platform |

### 3.3 Resident UI Design Principles

| Principle | Implementation |
|-----------|----------------|
| Card-based layout | Each Pay-in displayed as a card |
| Touch-first | All interactions via tap, no hover |
| Modal/bottom-sheet details | Detail views overlay main screen |
| Large touch targets | Minimum 44x44px tap areas |
| No tables | Use stacked key-value pairs |
| No hover states | No tooltip-dependent information |

---

## 4. Admin & Accounting Capabilities (Desktop-Only)

### 4.1 What Admin/Accounting CAN Do

| Capability | Description |
|------------|-------------|
| Review Pay-in queue | See all pending submissions |
| Filter Pay-ins by status | SUBMITTED, REJECTED_NEEDS_FIX, ACCEPTED, etc. |
| Match Pay-in with Bank Statement | 1:1 manual matching |
| Unmatch Pay-in | Remove incorrect match (if not accepted) |
| Accept Pay-in | Creates Ledger entry (requires match first) |
| Reject Pay-in | Returns to Resident with reason |
| View slip images | Full-size image viewer |
| Create Pay-in manually | When Resident did not submit |
| View audit trail | Who did what, when |
| Create Ledger entries | Via Accept action |
| Apply Ledger to Invoice | Settle outstanding invoices |

### 4.2 Admin-Created Pay-in Rules

Admin may create a Pay-in on behalf of a Resident when:
- Resident transferred money but did not submit payment report
- Slip was sent via LINE or other external channel
- Bank statement shows credit with no matching Pay-in

**Admin-created Pay-in MUST:**

| Requirement | Description |
|-------------|-------------|
| House selection | Admin must select which house |
| Source recording | Must specify: `ADMIN_CREATED`, `LINE_RECEIVED` |
| Slip attachment | Optional but recommended for audit |
| Admin note | Optional explanation |
| Bank transaction link | Reference to originating bank credit |
| Visibility to Resident | Resident can see (read-only if accepted) |

**Admin-created Pay-in workflow:**
1. Admin sees unidentified bank credit
2. Admin clicks "Create Pay-in"
3. Admin selects house, attaches slip (if available), adds note
4. Pay-in created with status `SUBMITTED` and auto-matched to bank transaction
5. Admin reviews and accepts (creates Ledger)

---

## 5. Pay-in State Machine

### 5.1 States

| State | Description | Resident Editable | Resident Deletable |
|-------|-------------|-------------------|-------------------|
| `DRAFT` | Started but not submitted | ✅ Yes | ✅ Yes |
| `PENDING` | **Primary state**: Resident submitted, awaiting review | ✅ Yes | ❌ **No** |
| `SUBMITTED` | Admin queue state (legacy, read-only) | ❌ No | ❌ No |
| `REJECTED_NEEDS_FIX` | Admin rejected, needs correction | ✅ Yes | ✅ Yes |
| `ACCEPTED` | Approved, Ledger created | ❌ No | ❌ No |

> **A.1.x Implementation Note (2026-01-19):**
> - Resident Create → **PENDING** (skips DRAFT)
> - PENDING = editable, **NOT deletable**
> - Edit keeps status as PENDING until Admin accepts/rejects
> - Single-open rule: Only one DRAFT/PENDING/REJECTED_NEEDS_FIX/SUBMITTED allowed per house

**Legacy State Mapping (backward compatibility):**

| Legacy State | Current State | Notes |
|--------------|---------------|-------|
| `PENDING` | `PENDING` | Now the primary editable state |
| `REJECTED` | `REJECTED_NEEDS_FIX` | Renamed for clarity |

### 5.2 State Transition Rules

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  [Resident Creates]                                         │
│         │                                                   │
│         ▼                                                   │
│      DRAFT ◄──────────────────────────────────────┐        │
│         │                                          │        │
│         │ (Resident submits)                       │        │
│         ▼                                          │        │
│    SUBMITTED ─────────────────────────────┐       │        │
│         │                                  │       │        │
│         ├── (Admin accepts) ──► ACCEPTED  │       │        │
│         │                        (terminal)│       │        │
│         │                                  │       │        │
│         └── (Admin rejects) ──► REJECTED_NEEDS_FIX │        │
│                                      │             │        │
│                                      │ (Resident   │        │
│                                      │  fixes &    │        │
│                                      │  resubmits) │        │
│                                      └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 State Transition Table

| From State | Action | To State | Actor | Conditions |
|------------|--------|----------|-------|------------|
| `DRAFT` | Submit | `SUBMITTED` | Resident | Required fields filled |
| `DRAFT` | Delete | (deleted) | Resident | None |
| `SUBMITTED` | Accept | `ACCEPTED` | Admin | Must be matched with bank statement |
| `SUBMITTED` | Reject | `REJECTED_NEEDS_FIX` | Admin | Must provide rejection reason |
| `REJECTED_NEEDS_FIX` | Edit & Resubmit | `SUBMITTED` | Resident | None |
| `REJECTED_NEEDS_FIX` | Delete | (deleted) | Resident | None |
| `ACCEPTED` | (none) | (immutable) | - | Terminal state |

### 5.4 Rejection Reason Requirements

When Admin rejects a Pay-in, they MUST:
1. Select a preset rejection reason code
2. Optionally add custom note

**Preset Rejection Reasons:**

| Code | Thai Label | English Label |
|------|------------|---------------|
| `WRONG_AMOUNT` | จำนวนเงินไม่ตรง | Amount mismatch |
| `WRONG_DATE` | วันที่/เวลาไม่ตรง | Date/time mismatch |
| `UNREADABLE_SLIP` | สลิปไม่ชัด | Unreadable slip |
| `DUPLICATE` | ซ้ำกับรายการอื่น | Duplicate entry |
| `WRONG_ACCOUNT` | โอนผิดบัญชี | Wrong bank account |
| `OTHER` | อื่นๆ | Other |

---

## 6. Unidentified Receipts (Bank-First Reality)

### 6.1 What Are Unidentified Receipts?

**Definition:** Bank CREDIT transactions that have no corresponding Pay-in report.

**Real-world scenarios:**
1. Resident transferred money but forgot to submit payment report
2. Resident sent slip via LINE instead of using the system
3. Resident does not use the app at all
4. Multiple family members transferred without coordination

### 6.2 Why Unidentified Receipts Exist

| Reality | System Response |
|---------|-----------------|
| Bank statement is source of truth | Money is received regardless of Pay-in |
| Residents are not always compliant | System must accommodate non-submission |
| LINE is preferred communication | Admin receives evidence outside system |
| Accounting must close books | Cannot wait indefinitely for Pay-in |

### 6.3 Unidentified Receipt Workflow

```
Bank Statement Import
        │
        ▼
┌───────────────────┐
│ CREDIT Transaction│
│ (money received)  │
└───────────────────┘
        │
        ▼
┌───────────────────┐     ┌───────────────────┐
│ Has matching      │ YES │ Normal matching   │
│ Pay-in?           │────►│ workflow          │
└───────────────────┘     └───────────────────┘
        │ NO
        ▼
┌───────────────────┐
│ UNIDENTIFIED      │
│ RECEIPT           │
└───────────────────┘
        │
        ▼
Admin investigates
(check LINE, call resident)
        │
        ▼
┌───────────────────┐
│ Admin creates     │
│ Pay-in from bank  │
│ transaction       │
└───────────────────┘
        │
        ▼
Auto-matched to bank tx
        │
        ▼
Admin reviews & accepts
        │
        ▼
Ledger created
```

### 6.4 Audit Trail for Admin-Created Pay-ins

| Field | Value |
|-------|-------|
| `source` | `ADMIN_CREATED` or `LINE_RECEIVED` |
| `created_by_admin_id` | User ID of Admin who created |
| `reference_bank_transaction_id` | UUID of bank CREDIT |
| `admin_note` | Explanation (e.g., "Received slip via LINE") |
| `submitted_at` | Timestamp of creation |

---

## 7. Date & Time Handling

### 7.1 Core Principle

> **"Invalid Date" MUST NEVER appear in any UI.**

### 7.2 Date Source Priority

| Priority | Field | Description |
|----------|-------|-------------|
| 1 | `effective_at` | Bank transaction datetime |
| 2 | `transfer_date` + `transfer_hour` + `transfer_minute` | Pay-in reported datetime |
| 3 | `created_at` | Record creation datetime |
| 4 | `-` | Display dash if all unavailable |

### 7.3 Date Format Requirements

| Context | Format | Example |
|---------|--------|---------|
| Thai locale | `DD/MM/BBBB` | 27/12/2568 |
| Time | `HH:mm` | 05:37 |
| Full datetime | `DD/MM/BBBB HH:mm` | 27/12/2568 05:37 |
| ISO (API) | ISO 8601 with timezone | 2025-12-27T05:37:00+07:00 |

### 7.4 Frontend Date Handling

```javascript
// CORRECT: Defensive parsing with fallback
const txDate = tx.effective_at || tx.transfer_date || tx.created_at;
const displayDate = txDate 
  ? new Date(txDate).toLocaleDateString('th-TH')
  : '-';

// WRONG: Direct parsing without fallback
new Date(tx.transaction_date).toLocaleDateString('th-TH')  // May show "Invalid Date"
```

---

## 8. Accounting & Audit Principles

### 8.1 Ledger Creation Rules

| Rule | Description |
|------|-------------|
| Ledger only after ACCEPTED | No Ledger entry until Admin explicitly accepts |
| Accept requires match | Pay-in must be matched with bank statement first |
| One Ledger per Pay-in | 1:1 relationship, no duplicates |
| Ledger is immutable | Once created, cannot be modified |

### 8.2 Invoice Payment Rules

| Rule | Description |
|------|-------------|
| Pay via Ledger only | Invoice can only be paid by applying Ledger |
| No direct payment | Cannot mark Invoice paid without Ledger |
| Partial payment supported | Ledger can be split across invoices |
| Overpayment tracked | Excess becomes credit balance |

### 8.3 Audit Trail Requirements

Every action MUST record:

| Field | Description |
|-------|-------------|
| Actor | User ID of who performed action |
| Timestamp | When action was performed |
| Action | What was done (create, edit, accept, reject) |
| Source | Where evidence came from |
| Evidence | Reference to slip image or bank transaction |

### 8.4 Traceability Chain

```
Bank Statement
     │
     ▼
Bank Transaction (CREDIT)
     │
     ▼
Pay-in Report ◄─── Slip Image
     │
     ▼
Ledger Entry (IncomeTransaction)
     │
     ▼
Invoice Payment
```

---

## 9. Scope Guardrails

### 9.1 Explicitly OUT OF SCOPE

| Item | Status | Reason |
|------|--------|--------|
| Resident Desktop UI | ❌ Not implemented | Mobile-only platform decision |
| Automatic bank reconciliation | ❌ Future phase | Requires AI/ML, out of current scope |
| Automatic Pay-in matching | ❌ Not implemented | Manual matching is intentional |
| Auto-accept Pay-ins | ❌ Prohibited | Admin decision required |
| Duplicate UI for different devices | ❌ Not implemented | One UI per role/platform |
| Bulk operations | ❌ Future phase | Out of current scope |
| Email notifications | ❌ Future phase | Out of current scope |
| LINE integration (automated) | ❌ Future phase | Manual process for now |

### 9.2 Guiding Principles for Scope

| Principle | Guideline |
|-----------|-----------|
| Reduce Admin workload | Any feature that increases manual work is rejected |
| Maintain audit integrity | Any feature that weakens audit trail is rejected |
| Mobile-first for Residents | Any desktop-specific Resident feature is rejected |
| Desktop-only for Admin | Any mobile Admin feature is rejected |
| No scope creep | Features not in this document are not implemented |

---

## 10. API Endpoint Reference

### 10.1 Pay-in State Machine Endpoints

| Method | Endpoint | Description | Actor |
|--------|----------|-------------|-------|
| GET | `/api/payin-state/rejection-reasons` | Get preset rejection reasons | Admin |
| POST | `/api/payin-state/{id}/submit` | Submit draft for review | Resident |
| POST | `/api/payin-state/{id}/reject` | Reject with reason | Admin |
| PUT | `/api/payin-state/{id}/save-draft` | Save draft changes | Resident |
| GET | `/api/payin-state/unidentified-bank-credits` | List unmatched credits | Admin |
| POST | `/api/payin-state/admin-create-from-bank` | Create Pay-in from bank tx | Admin |
| POST | `/api/payin-state/{id}/attach-slip` | Attach slip to Pay-in | Admin |
| GET | `/api/payin-state/review-queue` | Get review queue with counts | Admin |

### 10.2 Existing Pay-in Endpoints

| Method | Endpoint | Description | Actor |
|--------|----------|-------------|-------|
| GET | `/api/payin-reports` | List Pay-ins | All (filtered by role) |
| GET | `/api/payin-reports/{id}` | Get single Pay-in | All (with access control) |
| POST | `/api/payin-reports` | Create Pay-in | Resident |
| PUT | `/api/payin-reports/{id}` | Update Pay-in | Resident (if editable) |
| DELETE | `/api/payin-reports/{id}` | Delete Pay-in | Resident (if deletable) |
| POST | `/api/payin-reports/{id}/accept` | Accept Pay-in | Admin |
| POST | `/api/payin-reports/{id}/reject` | Reject Pay-in | Admin |

---

## 11. Data Model Reference

### 11.1 PayinStatus Enum

```python
class PayinStatus(Enum):
    DRAFT = "DRAFT"                         # Resident started, not submitted
    SUBMITTED = "SUBMITTED"                 # Awaiting admin review
    REJECTED_NEEDS_FIX = "REJECTED_NEEDS_FIX"  # Admin rejected, needs fix
    ACCEPTED = "ACCEPTED"                   # Approved, ledger created
    # Legacy (backward compatibility)
    PENDING = "PENDING"                     # Maps to SUBMITTED
    REJECTED = "REJECTED"                   # Maps to REJECTED_NEEDS_FIX
```

### 11.2 PayinSource Enum

```python
class PayinSource(Enum):
    RESIDENT = "RESIDENT"           # Created by resident
    ADMIN_CREATED = "ADMIN_CREATED"  # Admin created from unidentified
    LINE_RECEIVED = "LINE_RECEIVED"  # Admin created from LINE evidence
```

### 11.3 PayinReport Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `house_id` | Integer | FK to houses |
| `amount` | Decimal | Transfer amount |
| `transfer_date` | DateTime | When transfer occurred |
| `transfer_hour` | Integer | Hour (0-23) |
| `transfer_minute` | Integer | Minute (0-59) |
| `slip_url` | String | URL to slip image |
| `status` | Enum | Current state |
| `source` | Enum | How Pay-in was created |
| `rejection_reason` | Text | Admin rejection reason |
| `admin_note` | Text | Admin notes |
| `matched_statement_txn_id` | UUID | FK to bank transaction |
| `reference_bank_transaction_id` | UUID | Source bank tx (admin-created) |
| `created_by_admin_id` | Integer | Admin who created (if admin-created) |
| `submitted_at` | DateTime | When submitted for review |
| `accepted_at` | DateTime | When accepted |
| `accepted_by` | Integer | Admin who accepted |

---

## 12. Final Notes

### 12.1 Document Authority

> **This document is the authoritative reference for all future development.**

### 12.2 Implementation Rule

> **If behavior is not described here, it is not implemented.**

### 12.3 Change Management

> **Any change to system behavior requires explicit update to this document.**

Changes must be:
1. Discussed and agreed by stakeholders
2. Updated in this document with version increment
3. Reviewed before implementation begins

### 12.4 Document Versioning

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-19 | System Architect | Initial specification |

---

**END OF SPECIFICATION**
