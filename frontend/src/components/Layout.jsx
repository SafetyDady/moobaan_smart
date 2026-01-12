import { Link, useLocation } from 'react-router-dom';
import { useRole, ROLES } from '../contexts/RoleContext';

export default function Layout({ children }) {
  const location = useLocation();
  const { currentRole, setCurrentRole, isAdmin, isAccounting, isResident } = useRole();

  const navigation = {
    [ROLES.SUPER_ADMIN]: [
      { name: 'Dashboard', path: '/admin/dashboard', icon: '📊' },
      { name: 'Houses', path: '/admin/houses', icon: '🏠' },
      { name: 'Members', path: '/admin/members', icon: '👥' },
      { name: 'Invoices', path: '/admin/invoices', icon: '📄' },
      { name: 'Pay-ins', path: '/admin/payins', icon: '💰' },
      { name: 'Expenses', path: '/admin/expenses', icon: '💸' },
      { name: 'Bank Statements', path: '/admin/statements', icon: '🏦' },
    ],
    [ROLES.ACCOUNTING]: [
      { name: 'Dashboard', path: '/accounting/dashboard', icon: '📊' },
      { name: 'Invoices', path: '/accounting/invoices', icon: '📄' },
      { name: 'Pay-ins', path: '/accounting/payins', icon: '💰' },
      { name: 'Expenses', path: '/accounting/expenses', icon: '💸' },
      { name: 'Bank Statements', path: '/accounting/statements', icon: '🏦' },
    ],
    [ROLES.RESIDENT]: [
      { name: 'Dashboard', path: '/resident/dashboard', icon: '📊' },
      { name: 'Submit Payment', path: '/resident/submit', icon: '💳' },
    ],
  };

  const currentNav = navigation[currentRole] || [];

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-800 border-r border-gray-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-2xl font-bold text-primary-500">
            Moobaan Smart
          </h1>
          <p className="text-sm text-gray-400 mt-1">Village Accounting</p>
        </div>

        {/* Role Selector (Mock) */}
        <div className="p-4 border-b border-gray-700">
          <label className="block text-xs text-gray-400 mb-2">
            Current Role (Mock)
          </label>
          <select
            value={currentRole}
            onChange={(e) => setCurrentRole(e.target.value)}
            className="w-full input text-sm"
          >
            <option value={ROLES.SUPER_ADMIN}>Super Admin</option>
            <option value={ROLES.ACCOUNTING}>Accounting</option>
            <option value={ROLES.RESIDENT}>Resident</option>
          </select>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {currentNav.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-300 hover:bg-slate-700'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700">
          <div className="text-xs text-gray-400">
            <div>Phase 1 - UI/UX Demo</div>
            <div className="mt-1">Mock Data Only</div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
