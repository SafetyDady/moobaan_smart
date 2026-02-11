import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { RoleProvider } from './contexts/RoleContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

// Auth pages
import UnifiedLogin from './pages/UnifiedLogin';
import SelectHouse from './pages/auth/SelectHouse';

// Admin pages
import AdminDashboard from './pages/admin/Dashboard';
import Houses from './pages/admin/Houses';
import AddHouse from './pages/admin/AddHouse';
import AddResident from './pages/admin/AddResident';
import Members from './pages/admin/Members';
import Invoices from './pages/admin/Invoices';
import PayIns from './pages/admin/PayIns';
import Expenses from './pages/admin/ExpensesV2';  // Phase F.1: Expense Core
import Vendors from './pages/admin/Vendors';  // Phase H.1.1: Vendor & Category
import BankStatements from './pages/admin/BankStatements';
import UnidentifiedReceipts from './pages/admin/UnidentifiedReceipts';
import InvoiceAgingReport from './pages/admin/InvoiceAgingReport';
import CashFlowReport from './pages/admin/CashFlowReport';
import ChartOfAccounts from './pages/ChartOfAccounts';  // Phase F.2: COA Lite
import PeriodClosing from './pages/PeriodClosing';  // Phase G.1: Period Closing

// Resident pages (with mobile detection)
import { ResidentDashboardWrapper, ResidentSubmitPaymentWrapper, ResidentVillageDashboardWrapper, ResidentPaymentHistoryWrapper, ResidentProfileWrapper } from './pages/resident/ResidentRouteWrapper';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <RoleProvider>
          <Routes>
          {/* Root path redirect */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Public Routes */}
          <Route path="/login" element={<UnifiedLogin />} />
          <Route path="/select-house" element={<SelectHouse />} />

          {/* Protected Routes - Admin/Accounting */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute allowedRoles={['super_admin', 'accounting']}>
                <Layout>
                  <Routes>
                    <Route path="dashboard" element={<AdminDashboard />} />
                    <Route path="houses" element={<Houses />} />
                    <Route path="add-house" element={<AddHouse />} />
                    <Route path="add-resident" element={<AddResident />} />
                    <Route path="members" element={<Members />} />
                    <Route path="invoices" element={<Invoices />} />
                    <Route path="payins" element={<PayIns />} />
                    <Route path="unidentified-receipts" element={<UnidentifiedReceipts />} />
                    <Route path="expenses" element={<Expenses />} />
                    <Route path="statements" element={<BankStatements />} />
                    <Route path="reports/aging" element={<InvoiceAgingReport />} />
                    <Route path="reports/cashflow" element={<CashFlowReport />} />
                    <Route path="chart-of-accounts" element={<ChartOfAccounts />} />
                    <Route path="period-closing" element={<PeriodClosing />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Protected Routes - Accounting (alias to admin) */}
          <Route
            path="/accounting/*"
            element={
              <ProtectedRoute allowedRoles={['accounting', 'super_admin']}>
                <Layout>
                  <Routes>
                    <Route path="dashboard" element={<AdminDashboard />} />
                    <Route path="invoices" element={<Invoices />} />
                    <Route path="payins" element={<PayIns />} />
                    <Route path="unidentified-receipts" element={<UnidentifiedReceipts />} />
                    <Route path="expenses" element={<Expenses />} />
                    <Route path="vendors" element={<Vendors />} />
                    <Route path="statements" element={<BankStatements />} />
                    <Route path="reports/aging" element={<InvoiceAgingReport />} />
                    <Route path="reports/cashflow" element={<CashFlowReport />} />
                    <Route path="chart-of-accounts" element={<ChartOfAccounts />} />
                    <Route path="period-closing" element={<PeriodClosing />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Protected Routes - Resident (MOBILE ONLY - No Layout wrapper) */}
          {/* Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC: No sidebar, no desktop layout */}
          <Route
            path="/resident/*"
            element={
              <ProtectedRoute allowedRoles={['resident']}>
                <Routes>
                  <Route path="dashboard" element={<ResidentDashboardWrapper />} />
                  <Route path="village" element={<ResidentVillageDashboardWrapper />} />
                  <Route path="submit" element={<ResidentSubmitPaymentWrapper />} />
                  <Route path="payments" element={<ResidentPaymentHistoryWrapper />} />
                  <Route path="profile" element={<ResidentProfileWrapper />} />
                </Routes>
              </ProtectedRoute>
            }
          />

          {/* Root redirect to login */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* 404 - redirect to login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </RoleProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
