# Moobaan Smart — CLAUDE.md

## Project Overview
ระบบจัดการการเงินหมู่บ้านจัดสรร **แมกไม้ลีลาวดี** (Housing Estate Finance Management)
- **Live:** https://moobaan-smart.vercel.app
- **Backend API:** https://moobaan-smart-production.up.railway.app

## Tech Stack
- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL (psycopg3) + Alembic
- **Frontend:** React 18 + Vite 5 + Tailwind CSS + React Router 7
- **Storage:** Cloudflare R2 (slip images, attachments)
- **Auth:** JWT (admin/accounting), OTP + LINE OAuth (resident)
- **Deployment:** Vercel (frontend), Railway (backend) — auto-deploy on push to master

## Key Commands
```bash
# Backend (from backend/)
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000
alembic upgrade head                    # Run migrations

# Frontend (from frontend/)
npm install
npm run dev                             # http://localhost:5173
npm run build                           # Production build
```

## Project Structure
```
backend/
  app/
    api/          # 32 route files (auth, invoices, payins, expenses, bank_*, etc.)
    db/models/    # 22 SQLAlchemy models
    core/         # config, auth, deps, uploads (R2), timezone (Asia/Bangkok)
    services/     # Business logic (CSV parser, OTP, notifications, accounting)
  alembic/        # Database migrations
  requirements.txt

frontend/
  src/
    api/client.js        # Axios client, all API methods
    pages/admin/         # 17 admin pages (Dashboard, Invoices, PayIns, Expenses, etc.)
    pages/resident/      # Resident pages + mobile/ subfolder
    components/          # 19 shared components
    contexts/            # AuthContext, RoleContext
    hooks/               # useLocale, useServerPagination
    locales/th.js        # Thai translations (~1400 lines)
    utils/               # compressImage, deviceDetect, payinStatus
```

## Architecture & Conventions

### Roles
- `super_admin` — full access
- `accounting` — financial operations
- `resident` — house-bound, mobile-only UI

### PayIn Workflow
`DRAFT → SUBMITTED → PENDING (matched with bank tx) → ACCEPTED / REJECTED_NEEDS_FIX`
- Bank matching: 1:1 relationship, match by amount (±0.01) + time (±60s)
- Only ACCEPTED creates IncomeTransaction (ledger entry)

### Invoice Flow
- Auto-generated monthly or manual
- Statuses: `ISSUED → PARTIALLY_PAID → PAID / CREDITED`
- InvoicePayment links IncomeTransaction → Invoice

### UI Theme
- Dark theme throughout (bg-slate-900, cards bg-slate-800, borders slate-700)
- Thai language primary (all text via `t()` from `locales/th.js`)
- Lucide React icons
- Mobile-first resident pages, responsive admin pages

### Slip/Attachment Images
- Stored in Cloudflare R2
- `slip_url` in DB is an R2 object key, **NOT a direct URL**
- Must use backend proxy: `GET /api/payin-reports/{id}/slip`
- Frontend: `payinsAPI.slipUrl(id)` — never use `slip_url` directly as img src

### Localization
- All UI text in `frontend/src/locales/th.js`
- Access via `t('section.key')` — only accepts key + fallback, no interpolation params
- Always add translation keys when adding new UI text

## Important Notes

### Deployment
- Owner deploys manually after review — do NOT push or commit without asking
- Frontend auto-deploys from Vercel on push to master
- Backend auto-deploys from Railway on push to master

### Village Info (Hardcoded)
- Village: หมู่บ้านแมกไม้ลีลาวดี (juristic person, no PromptPay)
- Bank: KBANK 040-1-56500-0, นิติบุคคลหมู่บ้านจัดสรรแมกไม้ลีลาวดี, ออมทรัพย์
- Hardcoded in `MobileDashboard.jsx` — no backend config needed

### Database
- PostgreSQL on Railway
- Timezone: Asia/Bangkok (UTC+7)
- Alembic for migrations — always create migration for schema changes
- House members: max 3 per house (enforced)

### Pagination
- Backend: `usePagination` hook (client-side sort/page on full dataset)
- Some endpoints support server-side `page` + `page_size` params
- `SortableHeader` component for column sorting

### Common Patterns
- Admin pages wrap in `<AdminPageWrapper>`
- Tables use `<SortableHeader>`, `<Pagination>`, `<SkeletonTable>`, `<EmptyState>`
- Modals: custom `<ConfirmModal>`, `<AlertModal>`, or inline modal JSX
- Toast notifications via `useToast()` hook
- Export via `<ExportButton reportType="..." />`
