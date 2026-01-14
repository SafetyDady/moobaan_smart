# Accounting System Implementation Guide

## Overview

This document explains the complete implementation of the accounting system for the moobaan_smart project. The system follows strict accounting principles to ensure data integrity and auditability.

## Core Principles (IMMUTABLE)

1. **Balance is DERIVED, never stored**: House balance = SUM(invoices) - SUM(credit_notes) - SUM(applied_payments)
2. **Never delete invoices**: Historical invoices must remain for audit trail
3. **Never silently modify invoice amounts**: All changes must be traceable
4. **All balance changes must be explainable**: Every transaction affects balance in a traceable way

## Database Schema

### House Model Updates
```sql
-- New fields added to houses table
house_code VARCHAR(20) UNIQUE NOT NULL  -- "28/1" to "28/158"
house_status ENUM('ACTIVE', 'BANK_OWNED', 'VACANT', 'ARCHIVED', 'SUSPENDED') NOT NULL DEFAULT 'ACTIVE'
owner_name VARCHAR(255) NOT NULL  -- For accounting reference
```

**House Status Rules:**
- ALL statuses auto-generate monthly invoices
- ONLY ACTIVE status allows resident login and payment submission
- Accounting/Admin always have access regardless of status

### New Tables

#### 1. Invoices (Redesigned)
```sql
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    house_id INTEGER REFERENCES houses(id) ON DELETE CASCADE,
    cycle_year INTEGER NOT NULL,  -- e.g., 2024
    cycle_month INTEGER NOT NULL, -- 1-12  
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status invoice_status NOT NULL DEFAULT 'ISSUED',
    notes TEXT,  -- For discount explanations, etc.
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(house_id, cycle_year, cycle_month)  -- One invoice per house per month
);
```

**Invoice Status:**
- `ISSUED`: New invoice, unpaid
- `PARTIALLY_PAID`: Some payments received but not full amount
- `PAID`: Full amount received
- `CANCELLED`: Invoice cancelled (rare, for corrections)

#### 2. Income Transactions
```sql
CREATE TABLE income_transactions (
    id SERIAL PRIMARY KEY,
    house_id INTEGER REFERENCES houses(id) ON DELETE CASCADE,
    payin_id INTEGER REFERENCES payin_reports(id) ON DELETE CASCADE UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Purpose:** Immutable record of accepted payments. Created only when SUPER_ADMIN accepts a PayIn.

#### 3. Invoice Payments 
```sql
CREATE TABLE invoice_payments (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    income_transaction_id INTEGER REFERENCES income_transactions(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Purpose:** Links income to specific invoices. One income can pay multiple invoices, one invoice can receive multiple payments.

#### 4. Credit Notes
```sql
CREATE TABLE credit_notes (
    id SERIAL PRIMARY KEY,
    house_id INTEGER REFERENCES houses(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,  -- Positive number (reduces balance)
    reason TEXT NOT NULL,           -- Required explanation
    reference VARCHAR(255),         -- Optional reference number
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Purpose:** Handle debt reduction, discounts, corrections without deleting historical invoices.

### Updated PayIn Reports
```sql
-- New fields added
accepted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
accepted_at TIMESTAMP WITH TIME ZONE,
status payin_status NOT NULL DEFAULT 'PENDING'
```

**PayIn Status:**
- `PENDING`: Submitted by resident, waiting for admin approval
- `ACCEPTED`: Approved by SUPER_ADMIN, IncomeTransaction created
- `REJECTED`: Rejected by SUPER_ADMIN

## Core Services

### AccountingService Class

#### 1. auto_generate_invoices()
```python
AccountingService.auto_generate_invoices(
    db, year=2024, month=1, base_amount=Decimal("600.00")
)
```
- Creates monthly invoices for ALL houses regardless of status
- Idempotent: running twice won't create duplicates
- Default amount 600.00 per house per month

#### 2. accept_payin()
```python
AccountingService.accept_payin(db, payin_id=123, accepted_by_user_id=1)
```
- Only SUPER_ADMIN can accept payments
- Creates immutable IncomeTransaction
- Locks PayIn permanently (no edit/delete after acceptance)

#### 3. apply_payment_to_invoice()
```python
AccountingService.apply_payment_to_invoice(
    db, income_transaction_id=1, invoice_id=5, amount=Decimal("300.00")
)
```
- Applies specific amount from income to invoice
- Supports partial payments
- Auto-updates invoice status

#### 4. auto_apply_payments_fifo()
```python
AccountingService.auto_apply_payments_fifo(db, income_transaction_id=1)
```
- Auto-applies payment to oldest unpaid invoices
- FIFO (First In, First Out) method
- Convenient for regular monthly payments

#### 5. issue_credit_note()
```python
AccountingService.issue_credit_note(
    db, house_id=1, amount=Decimal("1000.00"), 
    reason="Debt negotiation settlement", created_by_id=1
)
```
- Only accounting/super_admin can issue
- Reduces balance without touching historical invoices
- Requires explanation for audit trail

#### 6. calculate_house_balance()
```python
balance = AccountingService.calculate_house_balance(db, house_id=1)
# Returns: {
#   "total_invoiced": Decimal("7200.00"),
#   "total_credited": Decimal("1000.00"), 
#   "total_paid": Decimal("5000.00"),
#   "outstanding_balance": Decimal("1200.00")
# }
```

## API Endpoints

All endpoints include proper RBAC (Role-Based Access Control):

### Invoice Management
- `POST /accounting/invoices` - Create manual invoice (accounting/admin only)
- `POST /accounting/invoices/bulk-generate` - Generate monthly invoices (accounting/admin only)  
- `GET /accounting/invoices/house/{house_id}` - Get house invoices (resident: own house only)

### Payment Processing
- `POST /accounting/payins/accept` - Accept PayIn (super_admin only)
- `POST /accounting/payments/apply` - Apply payment to invoice (accounting/admin only)
- `POST /accounting/payments/auto-apply` - Auto-apply payment FIFO (accounting/admin only)

### Credit Notes
- `POST /accounting/credit-notes` - Issue credit note (accounting/admin only)
- `GET /accounting/credit-notes/house/{house_id}` - Get house credit notes (accounting/admin only)

### Balance & Reporting
- `GET /accounting/balance/house/{house_id}` - Get balance (resident: own house if ACTIVE)
- `GET /accounting/financial-summary/house/{house_id}` - Comprehensive summary
- `GET /accounting/reports/balance-summary` - All houses summary (accounting/admin only)

## Real-World Scenarios

### Scenario 1: Regular Monthly Payment
```python
# 1. Resident submits PayIn for 600 THB
payin = PayinReport(house_id=1, amount=600, ...)

# 2. SUPER_ADMIN accepts payment
income_tx = AccountingService.accept_payin(db, payin.id, admin_user_id)

# 3. Auto-apply to oldest unpaid invoice
payments = AccountingService.auto_apply_payments_fifo(db, income_tx.id)
```

### Scenario 2: Lump-sum Prepayment with Discount
```python
# 1. Accounting creates special invoice for first month (discounted)
Invoice(house_id=1, cycle_year=2024, cycle_month=1, total_amount=400.00, 
        notes="12-month prepayment discount applied")

# 2. Generate normal invoices for remaining 11 months  
for month in range(2, 13):
    Invoice(house_id=1, cycle_year=2024, cycle_month=month, total_amount=600.00)

# 3. Resident pays 7000 THB for all 12 months
# 4. Admin applies payment to all 12 invoices
```

### Scenario 3: Debt Negotiation
```python
# House owes 20,000 THB from many invoices
# Negotiated settlement: pay only 5,000 THB

# 1. Issue credit note for 15,000 THB reduction
credit_note = AccountingService.issue_credit_note(
    db, house_id=1, amount=15000.00,
    reason="Debt settlement negotiation - reduced from 20,000 to 5,000 THB",
    reference="SETTLEMENT-2024-001"
)

# 2. Resident pays 5,000 THB
# 3. Apply payment to remaining balance
```

## Access Control Rules

### Residents
- ✅ Can view own house data ONLY if house_status == ACTIVE
- ✅ Can submit PayIns ONLY if house_status == ACTIVE
- ❌ Cannot see detailed credit notes (summary only)
- ❌ Cannot access other houses' data

### Accounting Role
- ✅ Full access to all houses regardless of status
- ✅ Can issue credit notes
- ✅ Can apply payments manually
- ✅ Can edit invoice amounts (with audit trail)
- ❌ Cannot accept PayIns (only SUPER_ADMIN)

### Super Admin
- ✅ Everything accounting can do
- ✅ Can accept PayIns (convert to IncomeTransaction)
- ✅ Full system access

## Balance Calculation Example

For House "28/15":
```
Invoices issued:
- 2023-01: 600 THB
- 2023-02: 600 THB  
- 2023-03: 600 THB
Total: 1,800 THB

Credit Notes:
- Debt reduction: -500 THB
Total: -500 THB

Payments Applied:
- Payment 1: -600 THB (applied to 2023-01)
- Payment 2: -300 THB (partial payment to 2023-02)
Total: -900 THB

Outstanding Balance: 1,800 - 500 - 900 = 400 THB
```

## Migration Applied

The system includes Alembic migration `580148e2242d_implement_accounting_system` which:
1. Updates house schema with new fields
2. Creates all new accounting tables
3. Migrates existing data safely
4. Handles enum type conversions properly

## Testing

Run the test script to verify everything works:
```bash
cd backend
python test_accounting.py
```

This accounting system ensures complete data integrity, full auditability, and handles all real-world scenarios including prepayments, discounts, debt negotiations, and partial payments.