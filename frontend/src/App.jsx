import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

// Auth pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Admin pages
import AdminDashboard from './pages/admin/Dashboard';
import Houses from './pages/admin/Houses';
import Members from './pages/admin/Members';
import Invoices from './pages/admin/Invoices';
import PayIns from './pages/admin/PayIns';
import Expenses from './pages/admin/Expenses';
import BankStatements from './pages/admin/BankStatements';

// Resident pages
import ResidentDashboard from './pages/resident/Dashboard';
import SubmitPayment from './pages/resident/SubmitPayment';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes - Admin/Accounting */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute allowedRoles={['super_admin', 'accounting']}>
                <Layout>
                  <Routes>
                    <Route path="dashboard" element={<AdminDashboard />} />
                    <Route path="houses" element={<Houses />} />
                    <Route path="members" element={<Members />} />
                    <Route path="invoices" element={<Invoices />} />
                    <Route path="payins" element={<PayIns />} />
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
                    <Route path="expenses" element={<Expenses />} />
                    <Route path="statements" element={<BankStatements />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Protected Routes - Resident */}
          <Route
            path="/resident/*"
            element={
              <ProtectedRoute allowedRoles={['resident']}>
                <Layout>
                  <Routes>
                    <Route path="dashboard" element={<ResidentDashboard />} />
                    <Route path="submit" element={<SubmitPayment />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Root redirect to login */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* 404 - redirect to login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
