# Moobaan Smart - Village Operational Finance System

**Production System** — Backend (FastAPI + PostgreSQL) + Frontend (React + Vite) ✅

## 🎯 Project Overview

A village operational finance system with house-centric design: income collection, expense tracking, bank reconciliation, and evidence storage.

> **Design Principle:** Moobaan Smart = Village Operational Finance System, NOT Accounting Software.
> No GL, No Journal Entry, No Double Entry, No Document Management, No Versioning, No Approval Workflow.

**Live Deployments:**
- Frontend (Vercel): https://moobaan-smart.vercel.app
- Backend (Railway): https://moobaan-smart-production.up.railway.app

## 🏗️ Architecture

**Monorepo Structure:**
```
moobaan_smart/
├── backend/                    # FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                # API routers
│   │   │   ├── expenses_v2.py
│   │   │   ├── expense_reconciliation.py
│   │   │   ├── attachments.py  # Evidence layer (R2)
│   │   │   └── ...
│   │   └── db/models/          # SQLAlchemy models
│   ├── alembic/                # Database migrations
│   └── requirements.txt
├── frontend/                   # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── pages/admin/        # Admin pages (ExpensesV2, etc.)
│   │   └── api/client.js       # API client (incl. attachmentsAPI)
│   └── package.json
└── docker-compose.yml
```

## ✨ Features Implemented (Phase 1)

### Backend
- ✅ Dashboard summary statistics
- ✅ Houses CRUD with search/filter
- ✅ Members CRUD with 3-member validation
- ✅ Invoices CRUD (Auto-gen + Manual)
- ✅ Pay-in reports workflow (SUBMITTED → REJECTED → MATCHED → ACCEPTED)
- ✅ Expenses CRUD with amount immutability guard
- ✅ Bank statements upload & matching
- ✅ **Vendor & Category master** (Phase H.1.1)
- ✅ **Chart of Accounts (COA Lite)** — account_code linkage
- ✅ **Expense ↔ Bank Allocation** — M:N junction with row locks (FOR UPDATE)
- ✅ **Attachments Evidence Layer** — presigned upload to Cloudflare R2
  - `POST /api/attachments/presign` → presigned PUT URL
  - `GET /api/attachments/` → list by entity
  - `DELETE /api/attachments/{id}` → soft delete with immutability check
- ✅ **Period Closing & Snapshot** (Phase G.1)
- ✅ **User Management** — Staff + Resident CRUD

### Frontend (Complete UI)
- ✅ Dark + Green theme with Tailwind CSS
- ✅ Sidebar navigation with role-based menu
- ✅ JWT Cookie auth (httpOnly, secure, SameSite=None) + CSRF
- ✅ **Admin/Accounting Pages:**
  - Dashboard with stats cards
  - Houses management (List + CRUD + Search)
  - Members management (3-member validation)
  - Invoices (Auto/Manual tabs + Generate)
  - Pay-ins inbox (Reject/Match/Accept actions)
  - Expenses tracking with **📎 Attachments UI** (upload Invoice/Receipt to R2)
  - Bank statements (Upload + Matching UI)
  - **Expense ↔ Bank Matching** (reconciliation page)
  - Vendors & Categories management
  - User Management Dashboard
- ✅ **Resident Pages:**
  - Dashboard (My invoices + Payment history)
  - Submit payment slip
  - Edit & resubmit (REJECTED only)

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker (optional)

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Docker (All-in-one):**
```bash
docker-compose up
```

Access:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🎨 Design System

**Theme:** Dark + Green (Financial stability)

**Colors:**
- Primary: Emerald Green (#10b981)
- Background: Slate 900 (#0f172a)
- Cards: Slate 800 (#1e293b)
- Text: White + Gray scale

**Typography:**
- Font: Inter (Latin) + Noto Sans Thai (Thai)
- Bilingual support (Thai/English)

## 📋 API Endpoints

All endpoints return mock data in Phase 1. See `/docs` for interactive API documentation.

**Key Endpoints:**
```
GET  /health
GET  /api/dashboard/summary
CRUD /api/houses
CRUD /api/members
CRUD /api/invoices
POST /api/invoices/generate-monthly
CRUD /api/payin-reports
POST /api/payin-reports/{id}/reject
POST /api/payin-reports/{id}/match
POST /api/payin-reports/{id}/accept
CRUD /api/expenses
POST /api/bank-statements/upload
GET  /api/bank-statements/{id}/rows

# Expense Reconciliation
GET  /api/reconcile/expenses
GET  /api/reconcile/bank-debits
POST /api/reconcile/allocate
DEL  /api/reconcile/allocate/{id}
GET  /api/reconcile/allocations

# Attachments (Evidence Layer — Cloudflare R2)
POST /api/attachments/presign     # Get presigned PUT URL
GET  /api/attachments/             # List by entity_type + entity_id
DEL  /api/attachments/{id}         # Soft delete

# Vendors & Categories
CRUD /api/vendors
CRUD /api/expense-categories

# User Management
GET  /api/users/staff
POST /api/users/staff
GET  /api/users/residents
```

## 🔐 Core Business Rules

1. **House-centric:** All data tied to houses
2. **3-member limit:** Maximum 3 members per house (enforced in UI)
3. **Pay-in lifecycle:** SUBMITTED → REJECTED → MATCHED → ACCEPTED
4. **Edit restrictions:** Residents can only edit REJECTED pay-ins
5. **Accept authority:** Only Super Admin can perform final Accept
6. **Invoice types:** Auto-generated monthly + Manual billing
7. **Time format:** HH:MM (24-hour format)

## 🧪 Testing

**Mock Role Switching:**
Use the dropdown in sidebar to switch between:
- Super Admin (full access)
- Accounting (financial operations)
- Resident (house-bound access)

**Test Scenarios:**
1. Navigate all pages as each role
2. Try CRUD operations on Houses/Members
3. Submit pay-in as Resident
4. Reject/Match/Accept pay-in as Admin
5. Generate monthly invoices
6. Upload bank statement

## 📦 Environment Variables

**Backend (.env):**
```env
APP_NAME=moobaan_smart_backend
ENV=production
PORT=8000
SECRET_KEY=<64-byte-hex>
DATABASE_URL=postgresql+psycopg://...

# Cloudflare R2 (Object Storage)
R2_ACCOUNT_ID=<account-id>
R2_ACCESS_KEY_ID=<access-key>
R2_SECRET_ACCESS_KEY=<secret-key>
R2_BUCKET_NAME=moobaan-smart-production
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-xxx.r2.dev
```

**Frontend (.env):**
```env
VITE_API_BASE_URL=http://localhost:8000
# Production: https://moobaansmart-production.up.railway.app
```

## 🚧 Phase 1 Scope & Limitations

**✅ What's Implemented:**
- Complete UI/UX for all pages
- Mock backend endpoints with proper response shapes
- Role-based navigation
- Table-heavy interfaces
- Workflow status tracking
- Mobile responsive design

**❌ Not Yet Implemented:**
- LINE Login full flow (admin link line_user_id → resident)
- Real-time updates / WebSocket
- CSRF enforcement (currently warn mode)
- Mobile-native app

## 📝 Development Notes

**Code Structure:**
- Backend: FastAPI with Pydantic models
- Frontend: React functional components with hooks
- State: Local state (no Redux/Zustand yet)
- API: Axios client with base URL config
- Styling: Tailwind utility classes + custom CSS

**Mock Data:**
- 5 houses (A-101 to A-105)
- 10 members across houses
- 10 invoices (mix of auto/manual)
- 8 pay-in reports (various statuses)
- 5 expenses
- 2 bank statements with rows

## 🔄 Next Steps

1. **LINE Resident Login** — full flow with admin linking
2. **CSRF Enforcement** — switch from warn to block mode
3. **Mobile UX Polish** — responsive tweaks
4. **Testing** — pytest (backend), vitest (frontend), E2E
5. **Period Close Reporting** — month-end export improvements

## 📄 License

MIT

## 👥 Contact

For questions or support, please open an issue on GitHub.

---

**Status:** Production ✅  
**Last Updated:** 2026-02-13  
**Git HEAD:** `cd842f2`
