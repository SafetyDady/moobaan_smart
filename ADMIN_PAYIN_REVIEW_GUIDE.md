# Admin Guide: Pay-in Review Queue

## Quick Start

1. **Navigate to Pay-in Review Queue**
   - Log in as admin (super_admin role)
   - Click "Pay-in Reports" in the admin menu
   - Default view shows PENDING submissions

2. **Review a Payment Submission**

### Option 1: ACCEPT ✓
When the payment slip is valid and amount matches:
1. Click **"✓ Accept"** button
2. Confirm the action
3. System creates immutable ledger entry (`IncomeTransaction`)
4. Status changes to `ACCEPTED` (locked forever)
5. Payment now appears in house statement

### Option 2: REJECT ✗
When there's an issue with the submission:
1. Click **"✗ Reject"** button
2. Enter clear reason (e.g., "Wrong amount - slip shows ฿500 not ฿600")
3. Click **"Reject"**
4. Status changes to `REJECTED`
5. Resident receives reason and can edit & resubmit

### Option 3: CANCEL 🗑
For test data cleanup or duplicate mistakes:
1. Click **"🗑 Cancel"** button
2. Enter reason (e.g., "Test submission" or "Duplicate entry")
3. Click **"Delete"**
4. Pay-in is permanently removed
⚠️ **Warning:** Cannot cancel ACCEPTED payins (ledger is immutable)

## Filters

- **All Status** - Show all pay-ins
- **Pending Review** - Default, shows only items awaiting action
- **Accepted** - View payment history (ledger created)
- **Rejected** - See items returned to residents

## Important Rules

### ✅ Can Accept
- Only PENDING payins
- Creates permanent ledger entry
- Cannot be undone

### ✅ Can Reject
- Only PENDING payins
- Resident can edit and resubmit
- Provide clear reason for resident

### ✅ Can Cancel
- PENDING or REJECTED payins
- Permanently deletes the submission
- Cannot cancel ACCEPTED (ledger is immutable)

### ❌ Cannot
- Accept already accepted payin (protected by database)
- Edit accepted payin (immutable ledger)
- Cancel accepted payin (ledger integrity)

## Workflow Example

**Scenario:** Resident submits ฿600 payment slip

1. **Resident:** Uploads slip via mobile app → Status: PENDING
2. **Admin:** Reviews submission in Pay-in Queue
3. **Admin:** Checks slip image
4. **Admin Decision:**
   - ✅ Slip valid → Click Accept → Ledger created
   - ❌ Slip unclear → Click Reject → Enter "Please upload clearer image"
   - 🗑 Duplicate → Click Cancel → Enter "Duplicate submission"

## Tips

- **Review slip image** by clicking "📎 View" before accepting
- **Rejection reasons** should be actionable (tell resident what to fix)
- **Accept carefully** - creates immutable financial record
- **Filter by PENDING** to focus on items needing attention
- **Check house number** matches the slip details

## Technical Notes

- **Accepted payins** create `IncomeTransaction` records
- **Income transactions** appear in monthly statements
- **Duplicate prevention** - unique constraint on `income_transactions.payin_id`
- **Audit trail** - tracks who accepted and when

## Common Scenarios

### ✅ Good Rejection Reasons
- "Slip shows ฿500 but submitted ฿600"
- "Transfer date doesn't match slip (slip shows Jan 10, submitted Jan 5)"
- "Slip image is too blurry to verify"
- "Wrong house number on slip"

### ❌ Poor Rejection Reasons
- "Wrong" (not actionable)
- "Error" (not specific)
- "No" (not helpful)

### When to Cancel vs Reject
- **Reject:** Issue can be fixed by resident (wrong amount, date, etc.)
- **Cancel:** Test data, duplicate, or submission error requiring deletion

## Keyboard Shortcuts
- None currently (use mouse/touch)

## Support

If you encounter issues:
1. Check browser console for errors
2. Verify you have `super_admin` role
3. Ensure payin status is PENDING
4. Contact technical support if issue persists

---

**Last Updated:** January 15, 2026  
**Version:** 1.0
