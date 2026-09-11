# Resident invoice table: all columns visible on mobile

Status: application commit `dbad6bb5145d842f0f4428266733949162581412` released and verified at 2026-09-11 13:04 Bangkok. Earlier local-only statements below record the state during testing.

## Request and scope

The owner accepted the data but found column proportions unsuitable on mobile. All five columns must be visible together; the billing cycle must not crowd the other cells.

Only application file changed: `frontend/src/pages/resident/mobile/InvoiceTable.jsx`. No financial calculations, allocation order, source timestamps, API, backend, database or production settings changed. Existing production release remains `06b611e` with documentation follow-up `2c5922e`.

## Implementation

- Removed the 520px minimum width and used one five-column minmax grid for headers and rows, with narrower billing cycle and compact spacing.
- Mobile billing cycle displays Thai month/Buddhist year (for example ส.ค. 69); desktop retains 2026-08. Special bills display พิเศษ.
- Mobile dates use compact numeric Thai dates; desktop retains short Thai month names. Both use existing Bangkok helpers. Latest payment retains date plus HH:mm and '-' when absent.
- Amounts remain complete, including fractional currency; status badges wrap when needed. Existing labels/colors and newest-first sorting remain.
- Vertical scrolling, sticky header, keyboard focus and pull-to-refresh isolation remain.

## Verification

Actual InvoiceTable and PullToRefresh components were bundled into a local fixture with 24 frozen synthetic invoices, no API client or database connection. Chrome browser requests were restricted to localhost.

- 47 browser checks passed at widths 320, 360, 390, 430 and 768px, with 16px outer margins. Assertions cover no horizontal page/table overflow, text bounds within cells, all five columns inside the container, large amounts up to 999,999.99, status labels, date/timezone, sorting across years/manual bills/ties, null dates, empty state, sticky header and refresh gestures.
- 7 native input checks passed: horizontal swipes preserve full-width fit and vertical touch scrolling works without parent refresh at 320/360/390px; keyboard PageDown scrolls the focused region.
- Screenshots at 320px and 390px inspected visually. At the smallest width, long statuses and month/year can occupy two lines.
- Frontend production build passed; existing Browserslist age and bundle-size warnings remain.
- Physical phones, Safari and authenticated production integration were not tested in this follow-up.

Local evidence: `C:\Users\sanch\moobaan-ui-checks\20260911-invoice-table` — `check-fit.cjs`, `fit-results.json`, `fit-*-left.png`, `native-fit.cjs`, `native-fit-results.json`. Local synthetic preview: http://127.0.0.1:5176.

This supersedes the previous acceptance of horizontal scrolling for narrow screens; historical release and test records remain intact.

## Follow-up: start at the first row on opening

Owner additionally requested initial table position at its first row. A stable callback ref sets the table's scrollTop to zero when attached, including when invoices arrive after the empty state. It does not reset on ordinary parent rerenders or invoice array refreshes, allowing residents to keep scrolling through older bills. Page layout and financial data are unchanged.

Local Chrome `first-row.cjs` verified initial position, manual scroll, reload and empty-to-loaded rendering. The 47 mobile-fit checks were rerun successfully (`first-row-results.json`); production build passed. Still not committed, pushed or deployed.

## Approved publication preparation

Owner authorized push. Code rollback point: `2c5922e750ebe6575f8bbd40777ae2e982efae99`. Fresh read-only production DB backup at 2026-09-11 13:02 Bangkok restored into a separate local database; all 26 table hashes/counts and Alembic revision matched. Snapshot SHA256: `78fede79292fa9be393c8497c3476331fffd5d99171fd99a9a740a0a8b9b5e04`. Private backup directory: `C:\Users\sanch\moobaan-db-backups\20260909-2895\resident-fit-release-20260911T060213Z`. Backup contains DB records/object keys, not R2 image bytes. Production reads only; no DB restoration or financial writes. Deployment outcome will be recorded after verification.

## Production result

- Application commit `dbad6bb5145d842f0f4428266733949162581412` pushed to master. Railway deployment `842e8bd2-fae5-4576-8916-96355ee57650` and Vercel deployment `FZ7FpC3UpbdWmHQ4quwLNmu36WL1` succeeded.
- At 13:04 Bangkok both `moobaan-smart.vercel.app` and `app.moobaan.app` served `/assets/index-55NVIdHG.js`, SHA256 `c0ead929a4f1ba5fa63ce5175cfdb83e6eb0652c8054aa0a66f6dd289e928576`, with compact-grid/first-row-reset markers. Published `/assets/index-BqDGT5Q6.css` matches the reviewed local build byte-for-byte.
- Health and readiness returned 200; all 15 anonymous invoice endpoint requests returned 401 as expected.
- Read-only production comparison found all 26 table hashes/counts unchanged from the pre-push backup; Alembic remains `p5_1_notifications`. Startup seed/reset flags were both false before publishing.
- Private evidence: `resident-fit-release-state.json`, `resident-fit-deployment-latest.json`, `resident-fit-postdeploy-checks.json`, `resident-fit-assets-verified.json` in the backup root. Documentation follow-up preserves application code.
- Physical-device/Safari and authenticated production UI were not checked. Code rollback uses the recorded Git base, not an old DB restore.
