# Moobaan Smart - Phase 1 TODO

## Goal
สร้าง UI/UX สวยงาม table-heavy พร้อม Backend mock endpoints

## Phase 1: Backend Mock Endpoints
- [x] เพิ่ม CORS config สำหรับ Vercel
- [x] สร้าง mock data models (Pydantic)
- [x] สร้าง GET /api/dashboard/summary
- [x] สร้าง CRUD /api/houses
- [x] สร้าง CRUD /api/members
- [x] สร้าง CRUD /api/invoices
- [x] สร้าง POST /api/invoices/generate-monthly
- [x] สร้าง CRUD /api/payin-reports
- [x] สร้าง POST /api/payin-reports/{id}/reject
- [x] สร้าง POST /api/payin-reports/{id}/match
- [x] สร้าง POST /api/payin-reports/{id}/accept
- [x] สร้าง CRUD /api/expenses
- [x] สร้าง POST /api/bank-statements/upload
- [x] สร้าง GET /api/bank-statements/{id}/rows

## Phase 2: Frontend Setup
- [x] ติดตั้ง Tailwind CSS
- [x] ติดตั้ง React Router
- [x] ติดตั้ง Axios
- [x] สร้าง Dark + Green theme config
- [x] สร้าง API client utility
- [x] สร้าง Layout component (Sidebar)
- [x] สร้าง Role context/provider (mock)

## Phase 3: Admin/Accounting Pages
- [x] Dashboard page (Cards + Quick Actions)
- [x] Houses page (List + CRUD + Search)
- [x] Members page (List + Add with 3-member validation)
- [x] Invoices page (Tabs: Auto/Manual + Generate + Edit)
- [x] Pay-ins page (Inbox table + Slip preview + Reject/Accept)
- [x] Expenses page (List + CRUD + Receipt upload)
- [x] Bank Statements page (Upload + Table view + Matching UI)

## Phase 4: Resident Pages
- [x] Resident Dashboard (My invoices + Pay-in history)
- [x] Submit Pay-in form
- [x] Edit Pay-in (Only when REJECTED)

## Phase 5: Integration & Testing
- [x] Test all pages with mock data
- [x] Test role-based UI gating
- [x] Test all action buttons call endpoints
- [x] Test CORS with Vercel domain
- [x] Verify mobile responsive

## Phase 6: Documentation & Deployment
- [x] Update README.md
- [x] Push to GitHub
- [ ] Verify Vercel auto-deploy (waiting for auto-deploy)
- [ ] Test production URLs (after deploy)

## Core Rules Checklist
- [x] House-centric design (1 house ≤ 3 members)
- [x] Pay-in lifecycle: SUBMITTED → REJECTED → MATCHED → ACCEPTED
- [x] Resident can edit only REJECTED pay-ins
- [x] Invoice: Auto-gen + Manual
- [x] Bank Statement: Upload → Table → Matching UI
- [x] Role-based access (Resident vs Accounting vs Super Admin)

## Phase 7: Authentication (Login/Register)
- [x] Backend: Create POST /api/auth/login endpoint (hardcoded users)
- [x] Backend: Create POST /api/auth/register endpoint (mock)
- [x] Backend: Mock JWT token generation
- [x] Frontend: Create Login page (Username/Password + Remember Me)
- [x] Frontend: Create Register page
- [x] Frontend: Create AuthContext for authentication state
- [x] Frontend: Implement Protected Routes
- [x] Frontend: Add logout functionality
- [x] Frontend: Persist auth state with localStorage (Remember Me)
- [x] Test login flow with all 3 roles
- [x] Test protected routes redirect to login
- [ ] Push to GitHub
