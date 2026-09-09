# Invoice ordering — verified production release

Owner approved commit/push. Application commit **`0f1913cd725acf433db32ada681e0e259e3309e6`** is deployed successfully on Railway and Vercel. Code rollback point: **`4c4c5a4a15645ef10c15cd25b5ac340f59a08ce5`**. Rolling code back does not reverse the separately approved 28/95 data correction.

## Behavior

- Shared invoice list explicitly orders monthly invoices by year/month ascending before pagination; manual bills use due date, and invoice ID breaks ties.
- Admin defaults to ascending billing cycle and uses actual API keys `cycle` and `house_number` for sorting.
- Resident dashboard consumes the ordered API response. Resident PaymentHistory keeps its separate intentional unpaid-first order.
- No financial writer, migration, environment setting, payment amount, receipt time, or allocation changed in this release.

## Verification

- Before publishing: compared deployed and new list handlers on restored data under READ ONLY. All 1,259 invoice payloads identical by ID; 157 house order checks, 28/95 January–August order, pagination boundaries, manual bill ordering pass. Frontend production build passes.
- Railway seed/reset flags both `false`, verified before publishing. Settings were not changed.
- Prepush DB backup **2026-09-09 15:24:02 Bangkok**, SHA256 `f51f4847d033ec5eca4c5e7afb3f42c69dd5574d92a3a9232df457c353e58af9`, 221,835 bytes. Restored successfully and compared all 26 table hashes/counts; matches verified final 28/95 state including readable audit notes and current memberships. R2 object bytes are not included.
- Railway deployment `bd525bf2-f329-4690-9d91-19e3808e11f7` SUCCESS; Vercel `Hy5PVNABD79o87YZwy4YEiKsqimm` SUCCESS, both for the application commit above.
- At **15:27:06 Bangkok**, health/ready 200; 15 anonymous invoice GET checks across direct backend and both frontend aliases return 401; all 26 production table hashes/counts unchanged from prepush backup. Alembic `p5_1_notifications` unchanged.
- Real Chrome Admin 28/95 reloaded: January–August ascending. Clicking cycle header produces August–January descending; restored ascending afterward.
- Real Chrome resident dashboard 28/95 reloaded: January–August ascending, January–July paid, August outstanding600, one September slip still pending with the existing warning against paying twice. May paid date on Admin remains11May07:05.
- No production financial writes or other-house repair used to verify this release. No new LINE login or R2 image test claimed.

## Evidence

Private root: `C:\Users\sanch\moobaan-db-backups\20260909-2895`.

- `invoice-order-release-state.json`, `invoice-order-preflight.json`
- `invoice-order-deployment-latest.json`, `invoice-order-postdeploy-checks.json`
- `invoice-order-verification.json`
- `invoice-order-release-20260909T082402Z` backup/metadata/fingerprints

The context-only commit following this report preserves the application code above; its deployment/status evidence is saved separately as `invoice-order-docs-*`. Earlier local-readiness entries in context remain historical records, not current deployment blockers.
