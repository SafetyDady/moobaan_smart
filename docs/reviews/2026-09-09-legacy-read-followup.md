# Legacy accounting read-report follow-up

Subsequent local integration: the resident report-access and monthly-download issues below are addressed and tested in [report access/download follow-up](2026-09-09-report-access-download.md). The original findings here are preserved for chronology; real LINE/production smoke checks remain pending.

Owner-authorized scope: repair five legacy accounting read functions and validate the same pristine production restore. Completed locally on 2026-09-09. No production data writes, allocation repair, migration, commit, push or deployment. This is not approval to release the whole system.

## Changes

- `calculate_house_balance`: current invoice settlement totals use the model's Decimal methods, ACTIVE allocations and applied credits. Unallocated receipts remain separate from invoice payments.
- `get_house_financial_summary`: credit notes join through their invoice, use the actual schema, and recent invoice status is canonical. The resident response sums `credit_amount` rather than the absent `amount` key.
- `calculate_month_end_snapshot`, `generate_house_statement`, `generate_statement`: one read-only cash calculation in `accounting_reports.py`. Uses invoice issue dates, POSTED receipt `received_at` including unallocated money, and applied credit `created_at`/`credit_amount`. Allocation order does not move the receipt month. REVERSED ledgers and pending slips do not add income.
- Bangkok calendar-day bounds are inclusive, implemented with an exclusive next-day bound. A mid-month request gets its actual opening/closing, not a month-end substitute. Decimal is retained during calculations; existing JSON float fields are preserved at response boundaries. Aggregate month totals sum Decimal values.
- Opening + invoices − confirmed receipts − applied credits equals closing and every running row. Errors propagate rather than becoming plausible zero reports. Removed the shadowed duplicate snapshot implementation.
- Fixed two unawaited/wrong-argument house-access checks. Monthly JSON uses the existing shared house guard rather than nonexistent House fields and preserves HTTP 403/404. This does not redesign global identity/house-context rules.

These statements are **restated views of currently valid records dated into past periods**, not immutable period-close snapshots or a reconstruction of what was known at a historical cutoff. Invoice outstanding and net cash balance remain explicitly different measures. Financial writer methods in `AccountingService` have unchanged ASTs versus HEAD.

## Verification

Same PG17 snapshot as steps 1–2: SHA256 `1b5f58eb0bb2dc3d3e107f57e933de8580a04c66dddefe9c57234cf90ed27063`, localhost database `steps12_20260908_185825`. Test sessions enforce read-only and UTC. All public-table row counts and sorted-row fingerprints still match the original census.

| Evidence | Result |
|---|---|
| Previous all-house API/service matrix, 157 houses and 1,259 invoices | 22,597 checks pass; zero failures |
| Independent raw SQL cash oracle, PostgreSQL Bangkok conversion | 13,806 checks pass; zero failures |
| Monthly coverage Jan–Sep 2026 | 1,413 house-months, monthly summaries/source rows/running balances |
| Exact ranges including mid-month and a single day | 471 house-ranges; nine village monthly aggregates |
| PostgreSQL settlement regression, including ten blocking races | 25 tests pass |
| New isolated PostgreSQL read/HTTP tests | 5 tests pass |
| Canonical status / last receipt time / invoice export | 12 / 7 / 8 tests pass |

Counts in the first two rows are field/row comparisons, not independent test cases. Total regression tests: 57. New tests cover fractional currency, a 20,000 special invoice with 5,000 credit, unused cash, split allocations, reversed entries, pending slips, unapplied credits, Bangkok midnight/microseconds, invalid ranges and failure propagation. HTTP tests inject authenticated users and exercise the real router/shared HouseMember guard: permitted house, other house, suspended house and Admin. They do not test LINE login or real production tokens.

Private evidence remains outside Git/OneDrive under `C:\Users\sanch\moobaan-db-backups\20260909-2895\steps12-20260908T185813Z`: `candidate-validation.private.json` and `legacy-read-validation.private.json`. Independent oracle runner: `validate_legacy_reads.py` in the parent directory. Original steps 1–2 report remains historical evidence.

## House 28/95

The repaired May cash statement contains receipt ledger 187, 600 THB: opening 0 + invoice 600 − confirmed receipt 600 = closing 0. June similarly contains ledger 223. August contains ledger 269; July has no confirmed receipt dated within July. This is a receipt-date view, not an assertion of which invoice those receipts should settle.

The production allocation issue remains unchanged. No repair mapping was applied to this pristine snapshot or production. The September pending slip remains excluded from confirmed income; its existence must remain visible and must not prompt a duplicate-payment demand.

## Remaining release work

1. Verify actual resident login/selected-house membership and UI before release. These legacy endpoints still use the existing `HouseMember` guard; modern membership is separately represented by `ResidentMembership`. Test fixture success must not be generalized to modern resident access without that integration check.
2. Separate legacy monthly download integration needs attention: `housesAPI.downloadStatement` calls `/accounting/statement/{id}` with year/month/format, whereas that route requires start/end dates; the monthly endpoint is `/accounting/statement/house/{id}`. Legacy `StatementPDFGenerator` also falls back to Helvetica if `THSarabun.ttf` is absent. This round verified JSON/read amounts, not those downloadable PDF layouts. The previously tested invoice-export generator is a different implementation.
3. The 62-house reconciliation queue and the specific 28/95 allocation correction are separate from code release. No mass correction is implied. Refresh the backup and recheck transactional preconditions before any later production mutation.
4. Other legacy writers/aging routes, exhaustive permissions, deployment startup, full UI/error-state flows and R2-object restore are not certified by this read-report test matrix.

Next release gate: resident access and download/UI integration review, then review a concrete code-release diff separately from proposed database corrections.
