# Finance read/report release candidate — accumulated diff review

**Subsequent advisor review:** the full R1 release recommendation is on hold pending the corrections and qualifications in [advisor adjudication](2026-09-09-advisor-adjudication.md). R1 remains historical review evidence; do not publish its full patch unchanged under the earlier readiness statement below.

Review completed locally on 2026-09-09. Code is prepared for release approval, not deployed. Baseline and GitHub `refs/heads/master` both verified at `f367d8832c266ad9c9010bd1fb04a1b0fcafcab6`. No commit, push, production mutation, migration execution or invoice allocation was performed.

## Final review finding and correction

**Blocking integration defect found and fixed:** the prior isolated HTTP test mounted the accounting router under `/api`, but production `app.main` mounted it only at `/accounting`. The frontend's corrected monthly URL would therefore still return 404 in the real app. Six read-only report routes now have a dedicated `/api/accounting` router mounted by `app.main`. Legacy `/accounting` paths are retained. No legacy payment/credit writer endpoint was exposed under the new prefix.

Added a regression using the real application, middleware and signed auth. It verifies all six canonical/legacy route pairs, unauthorized access, PDF/XLSX and absence of a new `/api/accounting/payments/apply` route. Re-ran the restored-data access/download matrix against `app.main`, without manually adding prefixes. All 2,261 checks pass, including `/health` and `/ready`; table fingerprints remain unchanged. This supersedes the prior isolated-router result for deployment routing.

No other unresolved blocking defect was identified in the accumulated changes reviewed. This is a bounded code review, not a guarantee that every existing system feature is correct.

## Exact release scope

| Area | Change and purpose |
|---|---|
| Invoice detail / audit | Actual amounts, canonical status, manual-invoice fields and receipt date; reversed allocations remain visible and explicitly labeled |
| Allocatable receipts / Admin invoice list | POSTED-only unused money, visible reconciliation notice, race-safe loading and export filters matching the loaded results |
| Dashboard | Debt/counts derived from ACTIVE allocations and applied credits; pending/submitted slips counted separately from confirmed money |
| Cash Flow / date display | Bangkok period boundaries and receipt display |
| Legacy accounting reads | Actual credit schema, shared Decimal cash opening/period/closing, exact dates, no zero fallback on failure |
| Report access | Selected-house session plus current ACTIVE ResidentMembership/house for residents; Admin/accounting retain access |
| Downloads | Correct monthly URL; bundled Thai font, pagination, Bangkok generated dates; numeric Excel money fields |
| Tests and context | Regression tests, source-handler harness and review evidence |

All financial writer methods in the changed invoice API/accounting API/accounting service retain their original ASTs. No DB model, Alembic migration, dependency manifest, Dockerfile, startup script, production environment file or deployment configuration was changed. The large accounting.py deletion consolidates duplicate/obsolete read implementations; it does not remove financial writers. Existing Docker COPY instructions include the added app modules and tracked Sarabun assets.

The only change to the legacy aging method is exclusion of REVERSED allocations. Its pre-existing credit/date/status limitations are still outside certification; it was not added to the new report router. Other unrelated legacy routes/writers and deprecated desktop screens are not certified by this release.

## Validation and limits

- Regression: 60 tests (PostgreSQL33 including ten blocking races, canonical status12, paid-at7, invoice export8). The 33 PostgreSQL tests were rerun after the final routing fix.
- Real app/restored-data matrix:2,261 checks pass; 157-house JSON/PDF/XLSX,114 membership records,111 eligible resident selections and matching Admin statements.
- Earlier unchanged financial-code matrices:22,597 checks and13,806 independent SQL comparisons pass, including1,413 house-months and471 ranges.
- Frontend build and production-source download handler harness pass; invoice loading/export harness passed in the earlier review. No frontend change was added in this final review.
- PDF visual QA covered May28/95 and every page of a synthetic three-page Thai report. This release review made no PDF layout change.
- Restored Alembic revision and repository head are both `p5_1_notifications`; this candidate adds no migration.
- Full application import, middleware routing, health and database readiness passed on localhost. Docker build could not be executed: installed Docker Desktop reports that it cannot start. Do not describe this as a successful container build.
- Real LINE OAuth/mobile-browser cookie behavior, production startup/environment and post-deploy behavior remain live verification steps. Existing startup may run migrations/optional seed; no inference that those are disabled follows from code-only scope.

Private reproducible evidence remains under `C:\Users\sanch\moobaan-db-backups\20260909-2895`. Candidate package directory: `release-candidate-20260909-r1`. It contains a full patch including new files, changed source files, a per-file SHA256 manifest and a reviewed Git tree ID. The tree is created using a private temporary index; the user's Git index/branch are not staged or committed. Revalidate hashes and the remote baseline if anything changes before release.

## Proposed release and rollback

Proposed single commit title: `fix(finance): reconcile receipt reporting and household statement access`.

1. Review/approve the exact candidate manifest and diff. Keep data correction scripts, private backups and evidence exports outside Git.
2. Before the authorized push, recheck remote master, latest backup availability, live Alembic revision and live `RUN_PROD_SEED` / `PROD_RESET_ADMIN_PASSWORD` settings. No new migration or seeding is intended. Those current live flags have not been verified in this review.
3. Commit the reviewed code/tests/context only, record the resulting commit and push once approved. Railway and Vercel build/deploy independently from GitHub; record both deployed revisions and wait for both to complete. If builds fail, stop and inspect logs instead of modifying financial data.
4. Read-only smoke checks: backend health/readiness; Admin invoice amounts/status/filter/export; 28/95 unused May receipt notice; monthly downloads; resident LINE login, selected house, pending slip visibility and receipt/statement parity. Do not test by creating/deleting payments in production.
5. If release checks fail, redeploy the previous backend/frontend artifacts or revert the exact release commit on top of the then-current branch and push through normal review. **Do not reset/force-push and do not restore the old database for a code rollback.** New legitimate payments may have arrived since the backup. A code rollback returns the known old report limitations, so pause disputed report decisions until corrected.

The 28/95 allocation repair and the62-house reconciliation queue are excluded. A later evidence-approved data repair requires a fresh backup and transactional preconditions, preserving Statement/pay-in/ledger records and reversal audit rows.
