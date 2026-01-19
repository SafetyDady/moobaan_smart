import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { RoleProvider } from './contexts/RoleContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

// Auth pages
import Login from './pages/auth/Login';

// Admin pages
import AdminDashboard from './pages/admin/Dashboard';
import Houses from './pages/admin/Houses';
import AddHouse from './pages/admin/AddHouse';
import AddResident from './pages/admin/AddResident';
import Members from './pages/admin/Members';
import Invoices from './pages/admin/Invoices';
import PayIns from './pages/admin/PayIns';
import Expenses from './pages/admin/Expenses';
import BankStatements from './pages/admin/BankStatements';
import UnidentifiedReceipts from './pages/admin/UnidentifiedReceipts';

// Resident pages (with mobile detection)
import { ResidentDashboardWrapper, ResidentSubmitPaymentWrapper } from './pages/resident/ResidentRouteWrapper';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <RoleProvider>
          <Routes>
          {/* Root path redirect */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Public Routes */}
          <Route path="/login" element={<Login />} />

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
                    <Route path="statements" element={<BankStatements />} />
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
                  <Route path="submit" element={<ResidentSubmitPaymentWrapper />} />
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
