# Month-End Reporting Features (Phase 2.3-2.5) - Implementation Guide

## Overview

This document explains the implementation of comprehensive month-end reporting features that provide reliable "as of end-of-month" financial views following strict accounting principles.

## Core Principles (UNCHANGED)

- **Balance is DERIVED, never stored**: All calculations are performed in real-time
- **Month-end basis**: All reports work on month-end cutoff dates  
- **Same logic as Excel month-end closing**: Familiar accounting workflow
- **Auditable and reproducible**: Same input always produces same output
- **RBAC compliant**: Proper role-based access control

## Phase 2.3: Month-End Financial Snapshot

### Purpose
Provides a reliable "as of end-of-month" financial view for accounting, statements, aging reports, and exports.

### Service Function
```python
AccountingService.calculate_month_end_snapshot(
    db=db, 
    house_id=house_id, 
    year=2024, 
    month=1
)
```

### Cutoff Date Logic
All calculations use strict month-end cutoffs:
- `Invoice.issue_date <= last_day_of_month`
- `IncomeTransaction.received_at <= last_day_of_month`  
- `CreditNote.created_at <= last_day_of_month`

### Output Structure
```json
{
    "house_id": 2,
    "house_code": "28/15", 
    "owner_name": "John Smith",
    "period": "2024-01",
    "period_end": "2024-01-31",
    "opening_balance": 1200.00,
    "invoice_total": 600.00,
    "payment_total": 800.00,
    "credit_total": 100.00,
    "closing_balance": 900.00
}
```

### Balance Calculation Logic
```
Opening Balance = Previous month's closing balance (calculated, not stored)
Closing Balance = Opening Balance + Invoice Total - Payment Total - Credit Total
```

### API Endpoint
```
GET /api/accounting/snapshot/{house_id}?year=2024&month=1
```

**Access Control:**
- Residents: Only own house AND house_status == ACTIVE
- Accounting/Admin: Any house

## Phase 2.4: House Financial Statement

### Purpose
Replace Excel + Word workflow for accounting with bilingual, downloadable statements that are legally explainable.

### Service Function
```python
AccountingService.generate_house_statement(
    db=db,
    house_id=house_id,
    year=2024,
    month=1
)
```

### Statement Content

#### 1. Header Information
- House code and owner name
- House status
- Period in both Thai and English  
- Closing balance (highlighted)

#### 2. Bilingual Summary Table (Ledger Style)
| Thai | English | Amount |
|------|---------|--------|
| ยอดยกมา | Opening Balance | 1,200.00 |
| ใบแจ้งหนี้เดือนนี้ | Invoices This Month | 600.00 |
| รับชำระ | Payments Received | (800.00) |
| ลดหนี้ | Credit Notes | (100.00) |
| ยอดคงเหลือปลายเดือน | Closing Balance | 900.00 |

#### 3. Transaction Timeline
- Strict chronological order
- Running balance calculation
- Transaction types: Invoice / Payment / Credit Note
- Reference numbers and descriptions
- Final running balance matches closing balance

### Output Formats
- **JSON**: API response with complete data structure
- **PDF**: For sending to residents (placeholder implementation)
- **Excel**: For internal accounting (placeholder implementation)

### API Endpoint
```
GET /api/accounting/statement/{house_id}?year=2024&month=1&format=json|pdf|xlsx
```

**Access Control:**
- Residents: Only own house AND house_status == ACTIVE
- Accounting/Admin: Full access

### Sample Statement Structure
```json
{
    "header": {
        "house_code": "28/15",
        "owner_name": "John Smith", 
        "house_status": "ACTIVE",
        "period": "2024-01",
        "period_th": "เดือน 1 ปี 2567",
        "period_en": "January 2024",
        "closing_balance": 900.00
    },
    "summary": {
        "opening_balance": {"th": "ยอดยกมา", "en": "Opening Balance", "amount": 1200.00},
        "invoices": {"th": "ใบแจ้งหนี้เดือนนี้", "en": "Invoices This Month", "amount": 600.00},
        "payments": {"th": "รับชำระ", "en": "Payments Received", "amount": -800.00},
        "credit_notes": {"th": "ลดหนี้", "en": "Credit Notes", "amount": -100.00},
        "closing_balance": {"th": "ยอดคงเหลือปลายเดือน", "en": "Closing Balance", "amount": 900.00}
    },
    "transactions": [
        {
            "date": "2024-01-01",
            "type": "invoice",
            "type_th": "ใบแจ้งหนี้",
            "type_en": "Invoice", 
            "reference": "INV-2024-01",
            "description": "Monthly fee 2024-01",
            "amount": 600.00,
            "is_debit": true,
            "running_balance": 1800.00
        }
    ]
}
```

## Phase 2.5: Aging Report (Project Overview)

### Purpose
Give accounting and management clear receivables overview as-of month-end.

### Service Function
```python
AccountingService.generate_aging_report(
    db=db,
    year=2024,
    month=1,
    house_status_filter=["ACTIVE", "SUSPENDED"],
    min_outstanding=100.00
)
```

### Aging Buckets (LOCKED)
- **0–30 days overdue**: `due_date` between 0-30 days before month-end
- **31–90 days overdue**: `due_date` between 31-90 days before month-end  
- **>90 days overdue**: `due_date` more than 90 days before month-end

### Overdue Logic
```
Overdue = invoice.due_date < end_of_month AND invoice not fully paid as of month-end
```

### Output Structure (House-level)
```json
{
    "house_id": 2,
    "house_code": "28/15",
    "owner_name": "John Smith",
    "house_status": "ACTIVE",
    "bucket_0_30": 600.00,
    "bucket_31_90": 0.00, 
    "bucket_90_plus": 0.00,
    "total_outstanding": 600.00,
    "as_of_date": "2024-01-31"
}
```

### Filters Available
- **house_status**: Filter by specific house statuses
- **min_outstanding**: Only show houses with minimum outstanding amount

### API Endpoint
```
GET /api/accounting/aging?year=2024&month=1&house_status=ACTIVE&min_outstanding=100&export=xlsx
```

**Access Control:**
- Accounting/Admin only (no resident access)

### Export Format
- **Excel only** (accounting workflow)
- One row per house
- Summary totals included

## Key Features & Validation

### ✅ Deterministic Calculations
- Same input month always produces same output
- No randomness or time-dependent variations
- Results are reproducible for auditing

### ✅ Edge Case Handling
- Invalid dates (month 13, etc.) rejected gracefully
- Non-existent houses handled properly
- Future months supported (show projected data)
- Partial payments calculated correctly
- Overpayments handled (carry forward logic)

### ✅ Performance Optimizations
- Efficient SQL queries with proper indexing
- Minimal database calls
- Cached relationship loading where appropriate

### ✅ Safety & Validation
- No mutation of invoices/payments/credits during report generation
- Transactional integrity maintained
- Input validation for all parameters
- Clear error messages for invalid requests

## Real-World Usage Examples

### Monthly Closing Process
```python
# 1. Generate snapshots for all houses
for house in houses:
    snapshot = AccountingService.calculate_month_end_snapshot(db, house.id, 2024, 1)
    
# 2. Create aging report for management
aging_data = AccountingService.generate_aging_report(db, 2024, 1)

# 3. Generate statements for residents  
for active_house in active_houses:
    statement = AccountingService.generate_house_statement(db, active_house.id, 2024, 1)
```

### Resident Statement Download
```python
# Resident requests statement
GET /api/accounting/statement/15?year=2024&month=1&format=pdf
```

### Management Aging Analysis
```python
# Management reviews overdue accounts
GET /api/accounting/aging?year=2024&month=1&min_outstanding=1000&export=xlsx
```

## Implementation Notes

### Thai Language Support
- Buddhist year conversion (2024 → 2567)
- Proper Thai month names and formatting
- Bilingual field labels throughout

### Running Balance Verification
The system verifies that:
1. Transaction timeline is chronologically correct
2. Running balance calculations are accurate
3. Final running balance matches closing balance
4. All debits/credits are properly signed

### Month-End Date Calculation
```python
def _get_month_end_date(year: int, month: int) -> date:
    """Get the last day of the specified month"""
    last_day = monthrange(year, month)[1]
    return date(year, month, last_day)
```

## Testing Results

All features have been comprehensively tested:

- ✅ **Month-end snapshot**: Mathematically correct balance calculations
- ✅ **Financial statements**: Bilingual output, accurate running balances  
- ✅ **Aging reports**: Proper bucket calculations, filtering works
- ✅ **Edge cases**: Invalid inputs handled gracefully
- ✅ **Deterministic results**: Same input produces same output
- ✅ **RBAC compliance**: Access control working correctly

## API Security

All endpoints implement proper RBAC:
- JWT token validation
- Role-based access control
- House membership verification for residents  
- House status checks (ACTIVE only for residents)

## Future Enhancements

The placeholder file generation functions can be enhanced with:
- **PDF Generation**: Use ReportLab or WeasyPrint for professional PDFs
- **Excel Generation**: Use openpyxl for formatted Excel files with charts
- **Email Integration**: Automatic statement delivery
- **Template Customization**: Configurable statement formats

This month-end reporting system provides a complete, auditable, and user-friendly solution for all financial reporting needs while maintaining the strict accounting principles established in the core system.