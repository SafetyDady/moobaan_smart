# Resident report access and monthly download follow-up

Final review correction: the isolated router test below did not validate the production app mount. See [release candidate review](2026-09-09-release-candidate.md) for the fixed canonical `/api/accounting` read-router registration and a rerun through `app.main` (2,261 checks). The earlier test results are preserved here for chronology.

Completed locally under owner authorization on 2026-09-09. No production writes, migrations, allocation repairs, commit, push or deployment. Previous work remains in the working tree; HEAD is still `f367d8832c266ad9c9010bd1fb04a1b0fcafcab6`.

## Resulting behavior

Monthly downloads previously sent year/month/format to the date-range route, which requires start/end dates. The active Houses page now calls `/api/accounting/statement/house/{id}` and chooses the current month using Bangkok time. The downloaded response remains a Blob; success and failure both clear the busy indicator, and successful downloads revoke their object URLs.

Six house-scoped accounting read endpoints now use `require_report_house_access`: balance, financial summary, both snapshot aliases, monthly statement (JSON/PDF/XLSX), and date-range statement. Admin/accounting can read any house. Residents must have a valid authenticated session, matching selected house, ACTIVE `ResidentMembership`, and an ACTIVE house. The database is not used to infer a selected house. Membership deactivation is checked for every read, including already-issued sessions. This replaces the obsolete HouseMember checks only for these report routes; global auth and other legacy endpoints are unchanged.

The legacy monthly PDF now embeds bundled Sarabun regular/bold instead of silently falling back to Helvetica. Table headers repeat across pages, page numbers reflect actual pages, owner names wrap and escape markup, and the closing amount has sufficient height. Generated timestamps are Bangkok; negative balances are described as prepaid funds. The PDF and Excel both describe the cash statement produced by the shared report calculation. Download filenames use numeric house IDs, avoiding slashes in house codes.

## Evidence

Tested against the same pristine restored PG17 snapshot (`steps12_20260908_185825`, SHA256 `1b5f58eb0bb2dc3d3e107f57e933de8580a04c66dddefe9c57234cf90ed27063`). Sessions enforce read-only and UTC. Signing keys were generated only for the local test process, not copied from production. The real auth and house-selection handlers executed against copied user/membership records through FastAPI TestClient; only the database dependency was replaced.

| Check | Result |
|---|---|
| Admin monthly JSON, PDF and XLSX | Each format passes for all 157 houses (May 2026) |
| Persisted resident membership records | 114 checked; 111 eligible selections succeed; ineligible report access denied |
| Six report routes across membership records | 684 expected access outcomes pass |
| Eligible resident PDF/XLSX | 222 successful downloads |
| Resident/Admin statement content | 111 matching responses |
| Full restored-data HTTP/download matrix | 2,259 checks pass, zero failures |
| Public-table fingerprints and counts | Unchanged from original census |
| PostgreSQL regression | 32 tests pass (25 settlement + 7 report/access/download) |
| Canonical status / last receipt / invoice export | 12 / 7 / 8 pass; total regression 59 |
| Production frontend source handler harness | PDF/XLSX URL, Blob, filename, busy/error cleanup and Bangkok month pass under UTC/New York/Tokyo |
| Frontend production build / diff whitespace | Pass |

Signed-session regression exercises no login, missing selected house, selection/re-selection via current `/api/auth/select-house`, another owned house without switching, revoked membership, revoked session and expired token. No production key or token is saved. The frontend harness executes the actual source client and download handler with browser/network I/O replaced; it is not an interactive browser test.

Rendered and visually checked the actual May 28/95 PDF and every page of a synthetic three-page Thai/long-owner-name report after the final layout change. May shows invoice 881 and actual receipt 187/600 THB, with cash closing zero. This is not a change to production invoice allocation. The synthetic report is solely pagination QA, not household evidence.

Private test evidence and rendered QA files are outside Git/OneDrive in `C:\Users\sanch\moobaan-db-backups\20260909-2895\steps12-20260908T185813Z`: `report-access-validation.private.json` and `report-download-qa`. Runner: `validate_report_access.py` in the parent directory. Repo regression command: `python -B -m unittest test_credit_settlement_postgres test_accounting_reads_postgres`; explicit localhost `CREDIT_TEST_DATABASE_URL` is required. Frontend harness: `node test-statement-download.cjs`.

## Release boundary

This completes the local resident report/download integration proposed in the previous review. A real LINE OAuth round trip, mobile browser cookie behavior, production startup and post-deploy smoke checks are still not validated by this test matrix. The deprecated desktop resident dashboard and unrelated legacy endpoints are not covered or restored to service. No new migration is required.

Next action is a review of the accumulated code diff and a separately authorized code release, with rollback at the existing deployed commit and read-only post-deploy verification. Do not bundle the 28/95 repair or a bulk 62-house allocation into that release. Any later data correction needs a fresh backup and checked allocation preconditions; preserve original receipt/Statement evidence and pending-slip visibility.
