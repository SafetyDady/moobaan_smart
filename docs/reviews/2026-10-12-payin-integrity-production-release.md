# PayIn Match Integrity Phase 1 — production release

## Authorization and scope

Owner authorized commit/push on 12 October 2026 after checks found no release blockers. This supersedes the earlier wait-for-owner state in the implementation handoff; no new independent Auditor result is claimed.

Release adds shared evidence validation and bank→PayIn locking, releases stale matches on evidence edit/rejection, and uses Statement amounts/timestamps at all three receipt entry points. Admin reviews slip, entered fields, and Statement before Match/Post, with a revision token checked under lock. Resident submission UI and invoice FIFO remain unchanged. No schema migration, historical correction executor, production configuration change, dependency change, or QR verification service is included.

The earlier two-house correction report is included to preserve the context already recorded locally. Publishing that report does not rerun the correction.

## Verification before push

- Git master/origin and active Railway deployment: `598f2bb734b25cdd7cc1a743e8cf2cbce6b1dea3` (code rollback baseline).
- Railway `RUN_PROD_SEED=false`, `PROD_RESET_ADMIN_PASSWORD=false`; health/readiness and both frontend domains returned 200 at preflight.
- Local backend: 141 passed, including 40 integrity checks with 12 real PostgreSQL blocking races. Other suites cover settlement, allocation, accounting reads, ledger eligibility, invoice access, paid date, statuses, and exports.
- Chrome UI: 11 synthetic scenarios passed, desktop/mobile390px, New York/Tokyo machine timezone. API requests mocked, non-local requests blocked. This is not browser-to-database end-to-end testing or Safari/device testing.
- Frontend production build passed; existing bundle-size/Browserslist and test deprecation warnings remain non-blocking.
- Read-only compatibility check on restored production snapshot: review token generated for all 334 PayIns. There were zero reviewable matched PayIns at that snapshot; this does not prove a live receipt workflow. Real financial actions were not used as production tests.
- Dedicated Local PostgreSQL17 container `moobaan-integrity-release-20261012`, loopback55443. Existing service on55442 was left running.

## Fresh database backup

- Snapshot timestamp: **2026-10-12 12:35:21 Bangkok**.
- Directory: `C:\Users\sanch\moobaan-db-backups\payin-integrity-release-20261012T053519Z`.
- SHA256: `92822dbf82e594fbea45986f6e2d4b9bd85bd455480b9c1fe7cfb029d7ed01a8`.
- Custom dump: 238,928 bytes, exported under a read-only repeatable-read snapshot.
- Restored into a separate Local database; **all 26 tables matched row counts and content hashes**, Alembic revision `p5_1_notifications` matched.
- Includes DB rows and R2 object keys, not R2 object bytes. No production restore or DB write was performed.

Private execution evidence: `C:\Users\sanch\moobaan-local-tests\payin-integrity-20261012` (`backend-results.json`, `results.json`, `preflight.json`, `backup.json`, `restored-compatibility.json`). Credentials and DB dump stay outside Git.

## Publication status

Preflight complete; commit/push and post-deployment verification are the next steps. Actual commit/deployment results will be appended after observing them.

## Operational limits

This change does not establish image authenticity or infer house ownership. Admin still checks the image, sender/receiver, and house evidence. Existing API clients without a review token retain compatibility but cannot prove which image the operator viewed. Existing inconsistent or reversed records may be blocked for investigation rather than silently repaired.

Rollback means reverting the application change after inspecting current deployment and any new transactions. Never restore this snapshot over later production activity, and never rerun completed financial repair executors.
