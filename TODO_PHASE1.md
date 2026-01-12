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
- [ ] Test all pages with mock data
- [ ] Test role-based UI gating
- [ ] Test all action buttons call endpoints
- [ ] Test CORS with Vercel domain
- [ ] Verify mobile responsive

## Phase 6: Documentation & Deployment
- [ ] Update README.md
- [ ] Push to GitHub
- [ ] Verify Vercel auto-deploy
- [ ] Test production URLs

## Core Rules Checklist
- [ ] House-centric design (1 house ≤ 3 members)
- [ ] Pay-in lifecycle: SUBMITTED → REJECTED → MATCHED → ACCEPTED
- [ ] Resident can edit only REJECTED pay-ins
- [ ] Invoice: Auto-gen + Manual
- [ ] Bank Statement: Upload → Table → Matching UI
- [ ] Role-based access (Resident vs Accounting vs Super Admin)
