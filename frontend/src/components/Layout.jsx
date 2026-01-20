import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAdmin, isAccounting, isResident } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Navigation based on user role
  const getNavigation = () => {
    if (!user) return [];

    if (user.role === 'super_admin') {
      return [
        { name: 'Dashboard', path: '/admin/dashboard', icon: '📊' },
        { name: 'Houses', path: '/admin/houses', icon: '🏠' },
        { name: 'Members', path: '/admin/members', icon: '👥' },
        { name: 'Invoices', path: '/admin/invoices', icon: '📄' },
        { name: 'Pay-ins', path: '/admin/payins', icon: '💰' },
        { name: 'Expenses', path: '/admin/expenses', icon: '💸' },
        { name: 'Bank Statements', path: '/admin/statements', icon: '🏦' },
        { name: 'Unidentified Receipts', path: '/admin/unidentified-receipts', icon: '❓' },
        { name: 'Chart of Accounts', path: '/admin/chart-of-accounts', icon: '📋' },
        { name: 'Period Closing', path: '/admin/period-closing', icon: '🔒' },
        { name: 'Aging Report', path: '/admin/reports/aging', icon: '📈' },
        { name: 'Cash Flow Report', path: '/admin/reports/cashflow', icon: '💹' },
      ];
    } else if (user.role === 'accounting') {
      return [
        { name: 'Dashboard', path: '/accounting/dashboard', icon: '📊' },
        { name: 'Invoices', path: '/accounting/invoices', icon: '📄' },
        { name: 'Pay-ins', path: '/accounting/payins', icon: '💰' },
        { name: 'Expenses', path: '/accounting/expenses', icon: '💸' },
        { name: 'Bank Statements', path: '/accounting/statements', icon: '🏦' },
        { name: 'Unidentified Receipts', path: '/accounting/unidentified-receipts', icon: '❓' },
        { name: 'Chart of Accounts', path: '/accounting/chart-of-accounts', icon: '📋' },
        { name: 'Period Closing', path: '/accounting/period-closing', icon: '🔒' },
        { name: 'Aging Report', path: '/accounting/reports/aging', icon: '📈' },
        { name: 'Cash Flow Report', path: '/accounting/reports/cashflow', icon: '💹' },
      ];
    } else if (user.role === 'resident') {
      return [
        { name: 'Dashboard', path: '/resident/dashboard', icon: '📊' },
        { name: 'Submit Payment', path: '/resident/submit', icon: '💳' },
      ];
    }

    return [];
  };

  const currentNav = getNavigation();

  // Role badge color
  const getRoleBadgeColor = () => {
    if (user?.role === 'super_admin') return 'bg-primary-600';
    if (user?.role === 'accounting') return 'bg-blue-600';
    if (user?.role === 'resident') return 'bg-gray-600';
    return 'bg-gray-600';
  };

  // Role display name
  const getRoleDisplayName = () => {
    if (user?.role === 'super_admin') return 'Super Admin';
    if (user?.role === 'accounting') return 'Accounting';
    if (user?.role === 'resident') return 'Resident';
    return 'Unknown';
  };

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-800 border-r border-gray-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-2xl font-bold text-primary-500">
            🏘️ Moobaan Smart
          </h1>
          <p className="text-sm text-gray-400 mt-1">Village Accounting</p>
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold">
              {user?.name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.name || 'User'}
              </p>
              <span className={`inline-block px-2 py-0.5 text-xs rounded ${getRoleBadgeColor()} text-white`}>
                {getRoleDisplayName()}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {currentNav.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Logout Button */}
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            <span>🚪</span>
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
