import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { RoleProvider, useRole, ROLES } from './contexts/RoleContext';
import Layout from './components/Layout';

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

function AppRoutes() {
  const { currentRole } = useRole();

  // Redirect to appropriate dashboard based on role
  const getDefaultRoute = () => {
    switch (currentRole) {
      case ROLES.SUPER_ADMIN:
        return '/admin/dashboard';
      case ROLES.ACCOUNTING:
        return '/accounting/dashboard';
      case ROLES.RESIDENT:
        return '/resident/dashboard';
      default:
        return '/admin/dashboard';
    }
  };

  return (
    <Routes>
      <Route path="/" element={<Navigate to={getDefaultRoute()} replace />} />
      
      {/* Admin Routes */}
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
      <Route path="/admin/houses" element={<Houses />} />
      <Route path="/admin/members" element={<Members />} />
      <Route path="/admin/invoices" element={<Invoices />} />
      <Route path="/admin/payins" element={<PayIns />} />
      <Route path="/admin/expenses" element={<Expenses />} />
      <Route path="/admin/statements" element={<BankStatements />} />

      {/* Accounting Routes (reuse admin components) */}
      <Route path="/accounting/dashboard" element={<AdminDashboard />} />
      <Route path="/accounting/invoices" element={<Invoices />} />
      <Route path="/accounting/payins" element={<PayIns />} />
      <Route path="/accounting/expenses" element={<Expenses />} />
      <Route path="/accounting/statements" element={<BankStatements />} />

      {/* Resident Routes */}
      <Route path="/resident/dashboard" element={<ResidentDashboard />} />
      <Route path="/resident/submit" element={<SubmitPayment />} />

      {/* 404 */}
      <Route path="*" element={<Navigate to={getDefaultRoute()} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <RoleProvider>
        <Layout>
          <AppRoutes />
        </Layout>
      </RoleProvider>
    </BrowserRouter>
  );
}

export default App;
