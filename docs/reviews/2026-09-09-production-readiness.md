# Production readiness — owner-authorized steps 1–2

Follow-up: the five legacy read-function failures documented below have since been corrected and retested locally. See [legacy read follow-up](2026-09-09-legacy-read-followup.md) for current results and remaining release gates. This document preserves the original steps 1–2 findings.

Status: audit/testing completed for this scope; **not a full-system release approval**. No production data correction, invoice reallocation, commit, push, migration or deployment was performed. The original 28/95 correction remains a separate proposal.

## Evidence and reproducibility

- Fresh full PostgreSQL17 custom snapshot restored successfully to an isolated password-protected localhost database: `steps12_20260908_185825`.
- Snapshot SHA256: `1b5f58eb0bb2dc3d3e107f57e933de8580a04c66dddefe9c57234cf90ed27063`.
- Deployed-code baseline: `f367d8832c266ad9c9010bd1fb04a1b0fcafcab6`, extracted with `git archive`; candidate: current uncommitted working tree.
- Both variants read the same pristine restored snapshot using database-enforced read-only transactions. All public-table fingerprints matched after the reads. Fingerprint serialization uses UTC consistently; client timezone must not be mistaken for a row change.
- Private backup, detailed reports, executable audit harnesses and raw results are outside Git/OneDrive under `C:\Users\sanch\moobaan-db-backups\20260909-2895`; latest output directory: `steps12-20260908T185813Z`.
- Open `review-report.html` for searchable household rows, evidence references and comparison results; `census.private.json`, `baseline-validation.private.json` and `candidate-validation.private.json` contain machine-readable detail.

## Step 1 — all-house reconciliation inventory

157 houses /1259 invoices /286 ledgers, of which283 are POSTED. All283 posted receipts match the original imported `raw_row` amount/time, bank transaction, confirmed statement batch, and accepted pay-in amount/house. This verifies stored source rows, not independently re-downloaded original CSV bytes or R2 image bytes.

| Measure | THB |
|---|---:|
| Billed | 763197.60 |
| Applied credit notes | 1600.00 |
| Confirmed receipts | 563619.10 |
| ACTIVE invoice allocations | 242800.50 |
| Confirmed money not allocated | 320818.60 |
| Outstanding invoices after allocations/credits | 518797.10 |
| Aggregate net due after all confirmed receipts | 197978.50 |
| PENDING/SUBMITTED slips (16, excluded from income) | 12599.19 |

The invoice outstanding amount and net cash balance are different quantities: `518797.10 - 320818.60 = 197978.50`. Admin/resident/report labels must preserve this distinction. Unallocated funds are not automatically evidence of corruption or authorization to apply them to arbitrary invoices.

| Household classification | Count |
|---|---:|
| Unallocated confirmed funds and outstanding invoices; review allocation intent | 62 |
| Unallocated funds with no outstanding invoice; advance-payment candidates | 2 |
| Outstanding invoices with no confirmed funds left to allocate | 90 |
| Neither outstanding invoices nor unallocated funds | 3 |

The62 review candidates split into53 whose unused funds can cover current invoices and9 with partial coverage;9 of the62 also have pending slips. All157 household rows include invoice IDs, unused receipt IDs, statement filenames, Bangkok receipt timestamps, and pending slip IDs. These are evidence-based categories; specific intended billing periods and refunds/advance-payment intent still need confirmation per household.

## Step 2 — deployed code versus candidate

Executed real API/service read functions with controlled Admin/resident house context against the snapshot. An independent census calculates expected values from database records. Monetary comparisons use Decimal cents. Covered all1259 invoices, all157 houses, all four canonical status filters, exports, audit totals/statuses, allocatable receipts, dashboard balances/counts, aging, Cash Flow monthly grouping, and five legacy accounting read functions.

Candidate passes22440 value comparisons/reads;1256 calls still fail in the five legacy accounting functions below. These are repeated cases across houses/months, **not22440 independent unit tests or1256 distinct bugs**. No candidate-only failure remains in this tested matrix. Baseline failures4606; candidate failures1256. Regression suites additionally pass52 tests: PostgreSQL25 (including10 blocking races), canonical status12, paid-at7, export8. Frontend build and loader/timezone harnesses pass.

Additional local fixes from this testing:

- Admin/resident invoice counts now derive from actual remaining amounts, not stale stored status; no invoice status rows are rewritten.
- Resident pending-slip count now includes PENDING/SUBMITTED while those amounts remain excluded from income.
- Village debt totals/counts now reuse the invoice Decimal calculation including ACTIVE payments and applied credit notes. Removing reversed payments alone had exposed the existing missing-credit bug; these defects happened to offset in the original aggregate. Both are handled together in the candidate.
- Cash Flow date bounds and period grouping use Bangkok. One house's receipt crossed the UTC month boundary, producing two incorrect monthly totals under UTC in deployed code; the candidate matches the source month.

## Remaining release blockers and limits

1. `AccountingService.calculate_house_balance`, `get_house_financial_summary`, `calculate_month_end_snapshot`, `generate_house_statement`, and `generate_statement` fail against current `CreditNote` schema (`amount`/`house_id` do not exist). Failures occur in both baseline and candidate. The snapshot function was exercised for Jan/May/Aug/Sep, each of157 houses. These paths need a dedicated read-report correction plus end-to-end amount/date tests; a mechanical field rename is insufficient because the old paths also mix ledger/allocated payments and contain incorrect date/fallback behavior.
2. Household reconciliation is classified but not authorized as a bulk mutation. The62 households must not all be processed using the 28/95 prescription.
3. No authenticated production-resident browser session, exhaustive UI/error-state validation, full permission audit, deployment startup test, all finance writer paths beyond the settlement regression suite, or R2 object-backup restore was performed. Do not generalize read-function parity into a guarantee for every system feature.
4. Snapshot results age as Admin/residents create new records. Any later production correction requires a fresh backup and transactional precondition checks.

Recommended next work: correct/test the legacy read-report functions and complete resident UI validation, then review the code release separately from evidence-approved data corrections. This document does not authorize either production step.
