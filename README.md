# Moobaan Smart - Village Accounting System

**Phase 1 Complete:** UI/UX with Mock Backend ✅

## 🎯 Project Overview

A comprehensive village accounting system with house-centric design, payment tracking, invoice management, and expense tracking.

**Live Deployments:**
- Frontend (Vercel): https://moobaan-smart.vercel.app
- Backend (Railway): https://moobaan-smart-production.up.railway.app

## 🏗️ Architecture

**Monorepo Structure:**
```
moobaan_smart/
├── backend/          # FastAPI + Python
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── mock_data.py
│   │   └── api/      # API routers
│   └── requirements.txt
├── frontend/         # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── pages/
│   │   └── api/
│   └── package.json
└── docker-compose.yml
```

## ✨ Features Implemented (Phase 1)

### Backend (Mock Endpoints)
- ✅ Dashboard summary statistics
- ✅ Houses CRUD with search/filter
- ✅ Members CRUD with 3-member validation
- ✅ Invoices CRUD (Auto-gen + Manual)
- ✅ Pay-in reports workflow (SUBMITTED → REJECTED → MATCHED → ACCEPTED)
- ✅ Expenses CRUD
- ✅ Bank statements upload & matching

### Frontend (Complete UI)
- ✅ Dark + Green theme with Tailwind CSS
- ✅ Sidebar navigation with role-based menu
- ✅ Mock role switching (Super Admin / Accounting / Resident)
- ✅ **Admin/Accounting Pages:**
  - Dashboard with stats cards
  - Houses management (List + CRUD + Search)
  - Members management (3-member validation)
  - Invoices (Auto/Manual tabs + Generate)
  - Pay-ins inbox (Reject/Match/Accept actions)
  - Expenses tracking
  - Bank statements (Upload + Matching UI)
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
ENV=local
PORT=8000
```

**Frontend (.env):**
```env
VITE_API_BASE_URL=http://localhost:8000
# Production: https://moobaan-smart-production.up.railway.app
```

## 🚧 Phase 1 Scope & Limitations

**✅ What's Implemented:**
- Complete UI/UX for all pages
- Mock backend endpoints with proper response shapes
- Role-based navigation
- Table-heavy interfaces
- Workflow status tracking
- Mobile responsive design

**❌ Not Implemented (Phase 2+):**
- Real authentication (mock role switching only)
- Real database (mock data in memory)
- File upload to S3 (mock URLs)
- Excel parsing (mock statement rows)
- Matching algorithm (placeholder)
- Accounting correctness (no double-entry)
- Real-time updates

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

## 🔄 Next Steps (Phase 2)

1. **Database Layer:**
   - PostgreSQL setup
   - SQLAlchemy models
   - Alembic migrations

2. **Authentication:**
   - JWT tokens
   - OAuth2 flow
   - Role-based access control

3. **File Storage:**
   - S3 integration
   - Image upload/download
   - Excel parsing

4. **Business Logic:**
   - Matching algorithm
   - Transaction ledger
   - Accounting rules

5. **Testing:**
   - pytest (backend)
   - vitest (frontend)
   - E2E tests

## 📄 License

MIT

## 👥 Contact

For questions or support, please open an issue on GitHub.

---

**Status:** Phase 1 Complete ✅  
**Last Updated:** 2025-01-12  
**Next Phase:** Database Integration & Authentication
