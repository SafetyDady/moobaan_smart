# Moobaan Smart — CLAUDE.md

> **ไฟล์นี้คือ "สมอง" ของโปรเจกต์ — AI ต้องอ่านก่อนทำงานทุกครั้ง**

---

## 🤝 AI Collaboration & Context System

> ผูกกับเล่มกลาง **UnionMyAi** (`OneDrive\00-Workspace\UnionMyAi`) — มาตรฐานทำงานร่วม AI หลายตัว

**เจ้าภาพหลัก = Claude Code** (จัดการ context, ตัดสินใจสถาปัตยกรรม, merge งานจาก AI ตัวอื่น, เป็นคนแก้/push โค้ดหลัก)

**AI ตัวอื่นที่เข้ามา (Cowork / Codex / Claude อื่น) — ทำตามนี้:**

1. **อ่านก่อนเริ่มเสมอ (ตามลำดับ):** `CLAUDE.md` (ไฟล์นี้) → `STATUS.md` (ทำถึงไหน เหลืออะไร) → `KNOWLEDGE-LOG.md` (เคยเรียนรู้/ตัดสินใจอะไร) → `DESIGN.md` (ทำไมออกแบบแบบนี้)
2. **จบงานสำคัญ:** บันทึกลง `KNOWLEDGE-LOG.md` (พร้อมวันที่) + อัปเดต `STATUS.md`
3. **ตัดสินใจด้านสถาปัตยกรรม:** บันทึกใน `DESIGN.md` — และ**ปรึกษา Claude Code ก่อน**ถ้ากระทบโครงสร้าง/production
4. **ขอบเขตที่ทำได้เลย:** อ่านโค้ด, เสนอ/ร่างงาน, แก้เฉพาะส่วนที่ได้รับมอบหมาย, เขียน context
5. **ต้องผ่าน Claude Code ก่อน:** เปลี่ยนโครงสร้างโปรเจกต์, migration, deploy, แก้ permission/business rule

**ไฟล์ context มาตรฐาน 4 ตัว (ที่ราก repo):** `CLAUDE.md` · `STATUS.md` · `KNOWLEDGE-LOG.md` · `DESIGN.md`
**เอกสารอ้างอิงเพิ่ม:** `DEPLOYMENT_GUIDE.md`, `PAY_IN_SYSTEM_SPEC.md`, `ACCOUNTING_SYSTEM_IMPLEMENTATION.md`, `MIGRATION.md`
> หมายเหตุ: `AGENTS.md` เป็นสำเนาของไฟล์นี้สำหรับ agent ที่อ่าน AGENTS.md — ถ้าแก้ CLAUDE.md ให้ sync AGENTS.md ตามด้วย (หรือพิจารณายุบให้เหลือไฟล์เดียวเพื่อกัน drift)

### 🚫 กฎเหล็ก (ห้ามทำ — จะทำ production พัง)
ห้าม **force-push** · ลบ repo บน GitHub · แก้ env บน Railway/Vercel dashboard โดยไม่ตั้งใจ · push commit เสีย · commit `.env`
> production deploy จาก **GitHub** (Vercel + Railway auto-deploy on push to master) ไม่ใช่ local — จัดบ้าน local ไม่กระทบ production. **Owner deploys/commits เองหลังรีวิว — อย่า push/commit โดยไม่ถาม.** คีย์ลับ `.env` สำรองแบบเข้ารหัสผ่าน `UnionMyAi\scripts\backup-secrets.bat`

---

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
