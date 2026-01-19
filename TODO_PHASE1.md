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
- [x] Push to GitHub

## Phase 1.2 - Remove Registration Feature

- [x] Backend: Remove `/api/auth/register` endpoint
- [x] Frontend: Delete Register.jsx page
- [x] Frontend: Remove register link from Login page
- [x] Frontend: Remove register route from App.jsx
- [x] Documentation: Update README_AUTH.md
- [x] Documentation: Update PHASE1_SUMMARY.md
- [x] Push changes to GitHub

## Phase 1.3 - Mobile-First UX for Residents

- [x] Create mobile layout with bottom navigation
- [x] Create mobile dashboard with card-based lists
- [x] Create mobile submit payment with camera integration
- [x] Add mobile detection and auto-routing
- [ ] Test mobile UI on different screen sizes
- [ ] Push to GitHub (requires user credentials)


## Phase 1.4 - Fix Submit Payment 422 Error

- [x] Pull latest code from GitHub
- [x] Analyze 422 validation error from backend
- [ ] Fix Mobile Submit Payment component (FormData issue)
- [ ] Fix Desktop Submit Payment Content-Type header
- [ ] Fix error message display ([object Object] issue)
- [ ] Test submit payment flow (both mobile and desktop)
- [ ] Push fix to GitHub


## Phase 1.5 - Fix Login Redirect Loop

- [x] Pull latest code from GitHub
- [x] Analyze AuthContext race condition (setUser vs navigate)
- [x] Document root cause analysis
- [x] Provide fix recommendations (isAuthenticated check)
- [x] Create test cases for 5 scenarios
- [x] Document security considerations
- [x] Create visual diagrams and quick fix guide
- [ ] Apply fix to AuthContext.jsx (Line 90)
- [ ] Test all 5 scenarios
- [ ] Push fix and documentation to GitHub


## Phase 1.6 - Improve Resident Mobile Dashboard UX

- [ ] Analyze current card sizes and layout issues
- [ ] Design compact card layouts for invoices
- [ ] Design compact card layouts for payment history
- [ ] Reduce card heights and improve information density
- [ ] Implement responsive typography and spacing
- [ ] Test on various mobile screen sizes
- [ ] Apply changes to MobileDashboard.jsx
- [ ] Push improvements to GitHub


## Phase 1.7 - Redesign Resident Mobile Dashboard (Summary + Table View)

- [ ] Design summary cards layout (total amount, invoice count, payment count)
- [ ] Design filter tabs (All, Paid, Unpaid, Pending)
- [ ] Design table view for invoices (compact rows)
- [ ] Design table view for payments (compact rows)
- [ ] Create mockup UI as JPG images
- [ ] Document implementation details
- [ ] Implement new dashboard layout
- [ ] Test filtering and navigation
- [ ] Push to GitHub


## Phase 1.8 - Add Village Dashboard (ภาพรวมหมู่บ้าน)

- [x] Implement backend API endpoint (/api/dashboard/village-summary)
- [x] Create VillageDashboard.jsx page with all components
- [x] Update MobileLayout.jsx bottom navigation (5 items)
- [x] Add route in App.jsx
- [ ] Test village dashboard displays correctly (REQUIRES DOCKER/DB)
- [ ] Verify status colors/logic unchanged (PENDING=yellow, REJECTED_NEEDS_FIX=red, SUBMITTED=gray, ACCEPTED=green)
- [ ] Test all navigation flows (REQUIRES DOCKER/DB)
- [x] Prepare git pull documentation (VILLAGE_DASHBOARD_IMPLEMENTATION.md)


## Phase 1.9 - Add Payment History and Profile Pages

- [x] Create mockup for Payment History page (Option A: Tabs)
- [x] Create mockup for Payment History page (Option B: Single view)
- [x] Get user approval on design (Option A selected)
- [x] Implement PaymentHistory.jsx page
- [x] Implement Profile.jsx page
- [x] Add routes in App.jsx
- [x] Add wrappers in ResidentRouteWrapper.jsx
- [x] Test all 5 navigation items work (code review complete)
- [x] Verify status colors/logic unchanged (verified - read-only)
- [x] Commit and push to GitHub (commit 05d0bd0)
