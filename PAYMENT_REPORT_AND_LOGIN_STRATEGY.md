# Payment Report and Login Strategy
## System Alignment Document

**Document Version:** 1.0  
**Created:** January 18, 2026  
**Status:** Approved for Implementation  

---

## 1. Background and Scope

### 1.1 System Overview

Moobaan Smart is a Village Accounting system designed for Thai housing estates (หมู่บ้านจัดสรร). The system manages:

- Monthly fee collection from residents
- Bank reconciliation
- Invoice generation and tracking
- Payment verification

### 1.2 Accounting Lifecycle (Already Implemented and Correct)

The core accounting flow has been implemented and verified:

```
Bank Statement → Match with Pay-in → Accept → Create Ledger → Apply to Invoice
```

Key principles:
- Bank statement is the source of truth for cash received
- No ledger creation without explicit Accept decision
- No invoice settlement without ledger allocation
- Full audit trail maintained

### 1.3 Scope of This Document

This document addresses **behavioral and process problems**, not accounting logic. The accounting lifecycle is correct and must not be modified. Remaining issues are:

- User friction in submitting payment reports
- Process gaps when money arrives without proper reporting
- Login barriers that prevent system adoption

---

## 2. User Behavior Assumptions (Locked Facts)

### 2.1 Residents

| Assumption | Detail |
|------------|--------|
| Device usage | 100% mobile users |
| Multi-device | Approximately 10% use both mobile and desktop |
| Authentication memory | Often forget email and password |
| Communication preference | Prefer LINE over logging into systems |
| Technical literacy | Varies widely; system must accommodate low-tech users |

### 2.2 Admin and Accounting Staff

| Assumption | Detail |
|------------|--------|
| Device usage | Desktop only |
| Responsibility | Accounting correctness and compliance |
| Workload constraint | Must not bear unnecessary manual workload |
| Access frequency | Daily during business hours |

---

## 3. Payment Report Problems (Current Reality)

### 3.1 Case A: Resident Submits Pay-in with Incorrect Data

**Scenario:**
- Resident submits Pay-in report
- Amount, date, or time is entered incorrectly
- Admin rejects the Pay-in
- Resident does not attempt to fix after rejection
- Pay-in remains in rejected state indefinitely

**Impact:**
- Admin review time wasted
- Bank transaction remains unmatched
- Revenue recognition delayed
- Resident may re-transfer money, creating duplicates

**Root behavior:**
- Residents do not understand the importance of accurate data
- No incentive or enforcement to correct rejected submissions
- Login friction prevents residents from returning to fix issues

### 3.2 Case B: Resident Transfers Money but Never Submits Pay-in

**Scenario:**
- Resident transfers money to village bank account
- Resident sends slip image via LINE to admin
- No Pay-in report is created in the system
- Bank statement shows credit with no matching Pay-in

**Impact:**
- System cannot reconcile the transaction
- Admin must manually investigate LINE messages
- Revenue recognition blocked or requires manual intervention
- Audit trail incomplete

**Root behavior:**
- Residents view LINE message as sufficient notification
- Login friction prevents residents from using the system
- No structured path for admin to formalize LINE-based evidence

### 3.3 Why These Are Systemic Risks

Both cases are not isolated user mistakes. They are predictable outcomes of:

- System design that assumes users will always log in
- Lack of quality gates before accounting review
- No fallback process for external evidence (LINE slips)
- Authentication method unsuitable for target users

---

## 4. Root Cause Analysis

### 4.1 Primary Root Cause: Login Friction

Email and password authentication is unsuitable for residents because:

- Residents rarely use email for daily communication
- Password recovery requires email access
- Mobile users expect app-like simplicity
- Each login attempt increases abandonment probability

### 4.2 Secondary Root Causes

| Root Cause | Effect |
|------------|--------|
| No quality gate before review | Admin wastes time on obviously incorrect submissions |
| No structured path for LINE evidence | Valid payments cannot enter the system cleanly |
| Binary Pay-in states | No mechanism for resident to fix and resubmit |
| No admin-initiated Pay-in | Money received outside system has no entry path |

---

## 5. Agreed Solutions (Conceptual)

### 5.1 Pay-in Quality Control

Introduce clear Pay-in lifecycle states:

| State | Description |
|-------|-------------|
| DRAFT | Resident started but not submitted |
| SUBMITTED | Awaiting initial review |
| REJECTED_NEEDS_FIX | Admin rejected; resident must correct and resubmit |
| PENDING_REVIEW | Corrected submission awaiting re-review |
| ACCEPTED | Approved; ledger created |

**Principles:**
- Admin reviews based on attached slip image
- Incorrect submissions must be fixed by resident before re-entering review queue
- System tracks rejection reason and fix history
- Prevents accumulation of stale rejected Pay-ins

### 5.2 Bank-First Handling for Missing Reports

For money received without Pay-in submission:

**Process:**
1. Bank statement import shows unmatched credit
2. Admin investigates (check LINE, contact resident)
3. Admin creates Pay-in on behalf of resident
4. Source marked as ADMIN_CREATED or LINE_RECEIVED
5. Normal Accept flow continues
6. Full audit trail maintained

**Principles:**
- Bank statement is the ultimate source of truth
- Unmatched bank credits are treated as unidentified receipts
- No automatic ledger creation for unmatched money
- Human decision required for every recognition
- LINE evidence attached but LINE is not a system of record

### 5.3 Login Simplification Strategy

Replace email and password for residents with Phone OTP:

**Primary method:** Phone OTP
- Resident enters phone number
- System sends SMS with one-time code
- Resident enters code to authenticate

**Secondary method:** PIN (optional)
- After OTP login, resident can set a 4-6 digit PIN
- PIN valid for quick access within defined period
- Falls back to OTP when PIN expires or fails

**Design constraints:**
- Mobile-first but desktop compatible
- Minimize OTP frequency to control SMS cost
- Must be testable in Local and Dev without real SMS
- Admin and Accounting staff retain email and password login

---

## 6. Accounting Safety Rules (Must Not Be Violated)

These rules are non-negotiable and must be preserved in all implementations:

1. **No revenue recognition without reconciliation**
   - Money in bank must be matched to a Pay-in before proceeding

2. **No ledger without Accept**
   - IncomeTransaction (Ledger) is only created when Admin explicitly accepts

3. **No invoice settlement without ledger allocation**
   - Invoice status changes to PAID only through Apply Payment from Ledger

4. **No auto-assignment of unidentified bank money**
   - Unmatched bank credits require human investigation and decision

5. **LINE is evidence, not a system of record**
   - LINE slip images can be attached as supporting documents
   - LINE messages do not create or modify accounting records

6. **Audit trail must be complete**
   - Every state change must be logged with timestamp and actor
   - No silent updates to financial records

---

## 7. What This Document Is and Is Not

### 7.1 This Document IS

- A shared mental model between stakeholders and AI agents
- A design contract that guides implementation
- A session migration anchor for continuity across conversations
- A reference for validating implementation correctness

### 7.2 This Document IS NOT

- A feature backlog or task list
- A coding specification or API design
- A UX mockup or wireframe
- A proposal for new accounting logic
- A timeline or project plan

---

## 8. Next Steps (Non-Technical)

### 8.1 After Document Approval

1. This document serves as the authoritative reference
2. Separate prompts will be issued for each implementation phase
3. Development will follow this document strictly
4. Implementation must not contradict any stated principle

### 8.2 Change Management

Any change to the agreed solutions requires:

1. Explicit discussion of the proposed change
2. Update to this document
3. Version increment and changelog entry
4. Re-approval before implementation proceeds

### 8.3 Implementation Phases (To Be Defined Separately)

- Phase A: Pay-in State Machine Enhancement
- Phase B: Admin-Created Pay-in Feature
- Phase C: Phone OTP Login for Residents
- Phase D: Optional PIN Quick Access

Each phase will have its own implementation prompt referencing this document.

---

## Appendix: Glossary

| Term | Definition |
|------|------------|
| Pay-in | Payment report submitted by resident with slip evidence |
| Ledger | IncomeTransaction record created upon Accept |
| Invoice | Monthly fee bill issued to a house |
| Match | Linking Pay-in to Bank Statement transaction |
| Accept | Admin approval that creates Ledger |
| Apply | Allocating Ledger amount to Invoice |
| OTP | One-Time Password sent via SMS |
| PIN | Personal Identification Number for quick access |

---

**End of Document**
