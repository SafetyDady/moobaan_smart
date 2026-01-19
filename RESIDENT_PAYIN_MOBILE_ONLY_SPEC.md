# Resident Pay-in — Mobile-only UX Specification

**Document Version:** 1.0  
**Date:** 2026-01-19  
**Status:** AUTHORITATIVE  
**Scope:** Resident Pay-in behavior, UI rules, and mobile-only policy

---

## 1. Purpose

This document defines the complete behavior and UX rules for the Resident Pay-in system in Moobaan Smart – Village Accounting.

This specification governs:
- Platform policy (mobile-only)
- Allowed resident actions by status
- UI/UX principles
- Detail view requirements
- Acceptance criteria

---

## 2. Platform Policy

### 2.1 Non-Negotiable Statement

> **Resident Desktop UI is intentionally removed by design.**

### 2.2 Platform Rules

| User Type | Platform | Policy |
|-----------|----------|--------|
| Resident | Mobile | ✅ Primary and ONLY supported experience |
| Resident | Desktop Browser | ✅ Allowed, but displays mobile layout only |
| Admin | Desktop | ✅ Primary experience |
| Accounting | Desktop | ✅ Primary experience |

### 2.3 Resident Platform Enforcement

- Resident users access the system **100% via mobile** in practice
- If a Resident accesses from a desktop browser:
  - They **MUST** see the same mobile-responsive layout
  - **NO** desktop-specific layouts are permitted
  - **NO** tables with horizontal scroll
  - **NO** hover interactions
  - **NO** multi-column desktop grids

### 2.4 Desktop Fallback Behavior

When Resident accesses from desktop browser:
- Layout remains single-column mobile view
- Max-width constraint applies (e.g., 480px centered)
- All tap targets remain mobile-sized (min 44×44px)
- No additional features appear

---

## 3. Resident User Context

### 3.1 Real-World Behavior

Resident users:
- Use mobile phones exclusively
- Often forget login credentials
- Frequently send payment slips via LINE
- Have low technical literacy
- Expect simple, obvious interfaces

### 3.2 Authentication Note

> **OUT OF SCOPE:** Auth changes (OTP, SMS, email unification) are explicitly excluded from this phase.

Current auth remains username/password. Future auth improvements are separate initiatives.

---

## 4. Resident Responsibilities

### 4.1 What Residents ARE Responsible For

| Responsibility | Description |
|----------------|-------------|
| Submit Payment Information | Create Pay-in with amount, date, slip |
| Correct Rejected Submissions | Edit and resubmit when Admin rejects |
| View Payment Status | Check current state of their Pay-ins |
| View Payment Details | Access full detail including rejection reasons |

### 4.2 What Residents Are NOT Responsible For

| NOT Resident's Job | Handled By |
|--------------------|------------|
| Matching Pay-in to Bank Transaction | Admin / System |
| Accepting Pay-in | Admin |
| Accounting Decisions | Accounting |
| Invoice Logic | System / Accounting |
| Ledger Entries | System / Accounting |
| Reconciliation | Admin / System |

**Principle:** Residents report payments. Everything else is handled by Admin or the system.

---

## 5. Pay-in Status Definitions

### 5.1 Status Enum

| Status | Thai Label | Description |
|--------|------------|-------------|
| `DRAFT` | แบบร่าง | Saved but not submitted (optional state) |
| `PENDING` | รอตรวจสอบ | Legacy: Submitted, awaiting review |
| `SUBMITTED` | ส่งแล้ว | Submitted, awaiting Admin review |
| `REJECTED_NEEDS_FIX` | ถูกปฏิเสธ - กรุณาแก้ไข | Admin rejected, Resident must fix |
| `ACCEPTED` | ยืนยันแล้ว | Admin accepted, final state |

### 5.2 Status Flow (Resident Perspective)

```
[Create] → DRAFT → [Submit] → SUBMITTED
                                  ↓
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
            REJECTED_NEEDS_FIX              ACCEPTED
                    ↓                        (Final)
              [Edit & Resubmit]
                    ↓
               SUBMITTED
```

---

## 6. Allowed Actions by Status

### 6.1 Editable States

Residents **CAN** edit and delete Pay-in when status is:

| Status | Edit | Delete | Resubmit |
|--------|------|--------|----------|
| `DRAFT` | ✅ | ✅ | ✅ (becomes SUBMITTED) |
| `PENDING` | ✅ | ✅ | N/A (already submitted) |
| `REJECTED_NEEDS_FIX` | ✅ | ✅ | ✅ (becomes SUBMITTED) |

**Editable Fields:**
- Amount
- Transfer date
- Transfer time
- Slip image (replace)

### 6.2 Read-Only States

Residents **CANNOT** edit or delete Pay-in when status is:

| Status | Edit | Delete | Reason |
|--------|------|--------|--------|
| `SUBMITTED` | ❌ | ❌ | Under Admin review |
| `ACCEPTED` | ❌ | ❌ | Permanent accounting record |

### 6.3 Always-Available Actions

Regardless of status, Residents **CAN** always:

| Action | Available |
|--------|-----------|
| View Pay-in detail | ✅ Always |
| View slip image | ✅ Always |
| View current status | ✅ Always |
| View rejection reason | ✅ When rejected |
| View source indicator | ✅ Always |

---

## 7. Mobile UX Principles

### 7.1 Layout Rules

| Rule | Requirement |
|------|-------------|
| Column layout | Single column only |
| List display | Card-based, no tables |
| Button size | Minimum 44×44px tap target |
| Spacing | Generous padding (16px minimum) |
| Font size | Minimum 16px for body text |

### 7.2 Interaction Rules

| Interaction | Mobile | Desktop |
|-------------|--------|---------|
| Tap | ✅ Primary | ✅ Click |
| Hover | ❌ Forbidden | ❌ Forbidden |
| Swipe | ✅ Optional | ❌ Not expected |
| Long press | ❌ Avoid | ❌ Avoid |

### 7.3 Navigation Patterns

| Pattern | Usage |
|---------|-------|
| Bottom sheet | Quick actions, confirmations |
| Modal | Detail view, forms |
| Full page | Edit form, create form |
| Back button | Standard mobile navigation |

### 7.4 Critical UX Rule

> **If an action is available on desktop but not visible on mobile, it is considered a BUG.**

All features must be mobile-first. Desktop is a viewport variation only.

---

## 8. Pay-in List View (Mobile)

### 8.1 Card Layout

Each Pay-in card displays:

```
┌─────────────────────────────────────┐
│ ฿ 5,000.00                    [สถานะ] │
│ 15 ม.ค. 2026, 14:30                  │
│ ────────────────────────────────────│
│ [ดูรายละเอียด]            [แก้ไข] │
└─────────────────────────────────────┘
```

### 8.2 Card Elements

| Element | Display |
|---------|---------|
| Amount | Large, prominent (฿ prefix) |
| Date/Time | Thai format, readable |
| Status | Color-coded badge |
| Actions | Buttons at bottom |

### 8.3 Status Badge Colors

| Status | Color | Background |
|--------|-------|------------|
| DRAFT | Gray | Light gray |
| PENDING | Orange | Light orange |
| SUBMITTED | Blue | Light blue |
| REJECTED_NEEDS_FIX | Red | Light red |
| ACCEPTED | Green | Light green |

### 8.4 Action Button Visibility

| Status | View Detail | Edit | Delete |
|--------|-------------|------|--------|
| DRAFT | ✅ | ✅ | ✅ |
| PENDING | ✅ | ✅ | ✅ |
| SUBMITTED | ✅ | ❌ Hidden | ❌ Hidden |
| REJECTED_NEEDS_FIX | ✅ | ✅ | ✅ |
| ACCEPTED | ✅ | ❌ Hidden | ❌ Hidden |

---

## 9. Pay-in Detail View (Resident)

### 9.1 Required Fields

| Field | Display | Always Visible |
|-------|---------|----------------|
| Amount | ฿ X,XXX.XX | ✅ |
| Transfer Date | DD MMM YYYY (Thai) | ✅ |
| Transfer Time | HH:MM | ✅ |
| Status | Thai label + badge | ✅ |
| Status (English) | English label | ✅ |
| Slip Preview | Thumbnail + tap to expand | ✅ |
| Source | Resident / Admin / LINE | ✅ |
| Rejection Reason | Admin's reason | When rejected |
| Created At | Timestamp | ✅ |
| Updated At | Timestamp | ✅ |

### 9.2 Source Indicator

| Source | Thai Label | Display |
|--------|------------|---------|
| `RESIDENT` | สร้างโดยลูกบ้าน | Default |
| `ADMIN_CREATED` | สร้างโดยผู้ดูแล | Badge |
| `LINE_RECEIVED` | รับจาก LINE | Badge |

### 9.3 Detail View Behavior

| Condition | Behavior |
|-----------|----------|
| Any status | Detail view accessible |
| Editable status | Show Edit button |
| Read-only status | Hide Edit button |
| ACCEPTED | Detail becomes permanently read-only |
| Has rejection reason | Show rejection reason prominently |

### 9.4 Slip Image Handling

| Action | Behavior |
|--------|----------|
| Thumbnail | Show in detail view |
| Tap thumbnail | Expand to full-screen viewer |
| Pinch zoom | Supported in full-screen |
| Download | Not required (view only) |

---

## 10. Pay-in Create/Edit Form (Mobile)

### 10.1 Form Fields

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| Amount | Number input | ✅ | > 0 |
| Transfer Date | Date picker | ✅ | ≤ Today |
| Transfer Time | Time picker | ✅ | Valid time |
| Slip | Image upload | ✅ | JPG/PNG, max 5MB |

### 10.2 Form UX

| Element | Behavior |
|---------|----------|
| Date picker | Native mobile picker |
| Time picker | Native mobile picker |
| Image upload | Camera or gallery |
| Submit button | Fixed at bottom |
| Validation | Inline error messages |

### 10.3 Edit Mode (Rejected Pay-in)

When editing a rejected Pay-in:
- Pre-fill all existing values
- Show rejection reason at top (read-only)
- Allow changing all editable fields
- Resubmit button changes status to SUBMITTED

---

## 11. Delete Confirmation

### 11.1 Delete Flow

```
[Tap Delete] → [Confirmation Modal] → [Confirm] → [Deleted]
```

### 11.2 Confirmation Modal Content

```
┌─────────────────────────────────────┐
│         ลบรายการชำระเงิน?            │
│                                     │
│  คุณต้องการลบรายการนี้หรือไม่?        │
│  การดำเนินการนี้ไม่สามารถย้อนกลับได้   │
│                                     │
│    [ยกเลิก]        [ลบ]             │
└─────────────────────────────────────┘
```

### 11.3 Delete Button Styling

- Color: Red / Destructive
- Requires explicit confirmation
- Not available for SUBMITTED or ACCEPTED

---

## 12. Error Handling (Mobile)

### 12.1 Error Display

| Error Type | Display Method |
|------------|----------------|
| Validation | Inline below field |
| Network | Toast notification |
| Server | Modal with retry |
| Permission | Modal with explanation |

### 12.2 Error Messages (Thai)

| Error | Thai Message |
|-------|--------------|
| Required field | กรุณากรอกข้อมูล |
| Invalid amount | จำนวนเงินไม่ถูกต้อง |
| Future date | วันที่ต้องไม่เกินวันนี้ |
| Upload failed | อัปโหลดรูปไม่สำเร็จ |
| Network error | ไม่สามารถเชื่อมต่อได้ |

---

## 13. Explicit Non-Goals

This specification does **NOT** include:

| Non-Goal | Reason |
|----------|--------|
| Auth redesign (OTP/SMS/email) | Explicitly out of scope for this phase |
| Desktop Resident UI | Intentionally removed by design |
| Automatic reconciliation | Admin responsibility |
| Admin features | Separate specification |
| Accounting features | Separate specification |
| Matching logic | System/Admin responsibility |
| Invoice management | Not resident responsibility |
| Ledger entries | Not resident responsibility |
| Multi-language support | Thai only for residents |
| Offline mode | Requires network connection |
| Push notifications | Future enhancement |

---

## 14. Acceptance Criteria

### 14.1 Mobile Experience Checklist

#### Create Pay-in
- [ ] Resident can create new Pay-in
- [ ] Amount field accepts numbers only
- [ ] Date picker shows native mobile picker
- [ ] Time picker shows native mobile picker
- [ ] Slip upload from camera works
- [ ] Slip upload from gallery works
- [ ] Submit creates Pay-in with SUBMITTED status
- [ ] Success feedback shown

#### Edit Pay-in (Editable States)
- [ ] Edit button visible for DRAFT
- [ ] Edit button visible for PENDING
- [ ] Edit button visible for REJECTED_NEEDS_FIX
- [ ] Edit form pre-fills existing values
- [ ] Slip can be replaced
- [ ] Save updates the Pay-in
- [ ] Resubmit changes status to SUBMITTED

#### Delete Pay-in (Editable States)
- [ ] Delete button visible for DRAFT
- [ ] Delete button visible for PENDING
- [ ] Delete button visible for REJECTED_NEEDS_FIX
- [ ] Confirmation modal appears
- [ ] Cancel returns without deleting
- [ ] Confirm deletes Pay-in
- [ ] Pay-in removed from list

#### View Detail (All States)
- [ ] Detail accessible for all statuses
- [ ] Amount displayed correctly
- [ ] Date/Time displayed in Thai format
- [ ] Status badge shows correct color
- [ ] Status label in Thai
- [ ] Slip thumbnail visible
- [ ] Tap slip opens full-screen viewer
- [ ] Rejection reason visible when rejected
- [ ] Source indicator visible

#### Read-Only States
- [ ] Edit button hidden for SUBMITTED
- [ ] Edit button hidden for ACCEPTED
- [ ] Delete button hidden for SUBMITTED
- [ ] Delete button hidden for ACCEPTED
- [ ] Detail view still accessible

### 14.2 Desktop Browser (Mobile Layout) Checklist

- [ ] Single-column layout maintained
- [ ] No horizontal scroll
- [ ] No hover states
- [ ] All mobile actions available
- [ ] Same visual appearance as mobile
- [ ] Max-width constraint applied
- [ ] Tap targets remain large

### 14.3 Edge Cases

- [ ] Empty state shown when no Pay-ins
- [ ] Loading state shown during fetch
- [ ] Error state shown on network failure
- [ ] Large slip images handled gracefully
- [ ] Long amounts display correctly
- [ ] Status transitions update UI immediately

---

## 15. Implementation Notes

### 15.1 CSS Requirements

```
/* Resident views MUST use mobile-first CSS */
/* Max-width constraint for desktop browsers */
.resident-container {
  max-width: 480px;
  margin: 0 auto;
  padding: 16px;
}

/* No hover states */
.resident-button:hover {
  /* Intentionally empty or same as default */
}

/* Touch-friendly tap targets */
.resident-button {
  min-height: 44px;
  min-width: 44px;
}
```

### 15.2 Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| All sizes | Same mobile layout |
| > 480px | Center with max-width |
| Landscape | Single column maintained |

### 15.3 Component Priority

| Priority | Component |
|----------|-----------|
| P0 | Pay-in list view |
| P0 | Pay-in detail view |
| P0 | Pay-in create form |
| P1 | Pay-in edit form |
| P1 | Delete confirmation |
| P2 | Status filter |
| P2 | Pull-to-refresh |

---

## 16. Final Authority Statement

> **This document defines the final behavior of Resident Pay-in.**

> **If behavior is not described here, it must not be implemented.**

> **Any change requires explicit update to this document.**

### Document Control

| Action | Requirement |
|--------|-------------|
| Add feature | Update this document first |
| Change behavior | Update this document first |
| Remove feature | Update this document first |
| Clarify ambiguity | Add to this document |

### Conflict Resolution

If implementation conflicts with this document:
1. This document is correct
2. Implementation must be fixed
3. Document wins

---

## Appendix A: Status Reference Card

| Status | Thai | Editable | Deletable | Resident Action |
|--------|------|----------|-----------|-----------------|
| DRAFT | แบบร่าง | ✅ | ✅ | Edit, Delete, Submit |
| PENDING | รอตรวจสอบ | ✅ | ✅ | Edit, Delete |
| SUBMITTED | ส่งแล้ว | ❌ | ❌ | View only |
| REJECTED_NEEDS_FIX | ถูกปฏิเสธ | ✅ | ✅ | Edit, Delete, Resubmit |
| ACCEPTED | ยืนยันแล้ว | ❌ | ❌ | View only (permanent) |

---

## Appendix B: Thai Label Reference

| English | Thai |
|---------|------|
| Pay-in | รายการชำระเงิน |
| Amount | จำนวนเงิน |
| Transfer Date | วันที่โอน |
| Transfer Time | เวลาโอน |
| Slip | สลิป |
| Status | สถานะ |
| Submit | ส่ง |
| Edit | แก้ไข |
| Delete | ลบ |
| Cancel | ยกเลิก |
| Confirm | ยืนยัน |
| View Detail | ดูรายละเอียด |
| Rejection Reason | เหตุผลที่ปฏิเสธ |
| Created by Resident | สร้างโดยลูกบ้าน |
| Created by Admin | สร้างโดยผู้ดูแล |
| Received from LINE | รับจาก LINE |

---

*End of Specification*
