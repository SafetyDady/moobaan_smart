import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  BarChart3, Home, Users, Building2, FileText, DollarSign, 
  TrendingDown, CreditCard, PieChart, TrendingUp, List, 
  Lock, LogOut, ChevronDown, ChevronRight, GitCompare,
  HelpCircle, UserCog, Send
} from 'lucide-react';
import { useState } from 'react';
import NotificationBell from './NotificationBell';

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAdmin, isAccounting, isResident } = useAuth();
  
  // State for collapsible sections
  const [expandedSections, setExpandedSections] = useState({
    management: true,
    finance: true,
    reporting: true,
    settings: true,
    actions: true,
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Navigation based on user role with icons
  const getNavigation = () => {
    if (!user) return { dashboard: null, sections: [] };

    if (user.role === 'super_admin') {
      return {
        dashboard: { name: 'Dashboard', path: '/admin/dashboard', icon: BarChart3 },
        sections: [
          {
            id: 'management',
            title: 'MANAGEMENT',
            items: [
              { name: 'Houses', path: '/admin/houses', icon: Home },
              { name: 'Members', path: '/admin/members', icon: Users },
              { name: 'Vendors', path: '/admin/vendors', icon: Building2 },
              { name: 'User Management', path: '/admin/users', icon: UserCog },
            ]
          },
          {
            id: 'finance',
            title: 'FINANCE',
            items: [
              { name: 'Invoices', path: '/admin/invoices', icon: FileText },
              { name: 'Pay-ins', path: '/admin/payins', icon: DollarSign },
              { name: 'Expenses', path: '/admin/expenses', icon: TrendingDown },
              { name: 'Bank Statements', path: '/admin/statements', icon: CreditCard },
              { name: 'Expense Matching', path: '/admin/expense-reconciliation', icon: GitCompare },
              { name: 'Unidentified Receipts', path: '/admin/unidentified-receipts', icon: HelpCircle },
            ]
          },
          {
            id: 'reporting',
            title: 'REPORTING',
            items: [
              { name: 'Aging Report', path: '/admin/reports/aging', icon: PieChart },
              { name: 'Cash Flow Report', path: '/admin/reports/cashflow', icon: TrendingUp },
            ]
          },
          {
            id: 'settings',
            title: 'SETTINGS',
            items: [
              { name: 'Chart of Accounts', path: '/admin/chart-of-accounts', icon: List },
              { name: 'Period Closing', path: '/admin/period-closing', icon: Lock },
            ]
          },
        ]
      };
    } else if (user.role === 'accounting') {
      return {
        dashboard: { name: 'Dashboard', path: '/accounting/dashboard', icon: BarChart3 },
        sections: [
          {
            id: 'finance',
            title: 'FINANCE',
            items: [
              { name: 'Invoices', path: '/accounting/invoices', icon: FileText },
              { name: 'Pay-ins', path: '/accounting/payins', icon: DollarSign },
              { name: 'Expenses', path: '/accounting/expenses', icon: TrendingDown },
              { name: 'Vendors', path: '/accounting/vendors', icon: Building2 },
              { name: 'Bank Statements', path: '/accounting/statements', icon: CreditCard },
              { name: 'Expense Matching', path: '/accounting/expense-reconciliation', icon: GitCompare },
              { name: 'Unidentified Receipts', path: '/accounting/unidentified-receipts', icon: HelpCircle },
            ]
          },
          {
            id: 'reporting',
            title: 'REPORTING',
            items: [
              { name: 'Aging Report', path: '/accounting/reports/aging', icon: PieChart },
              { name: 'Cash Flow Report', path: '/accounting/reports/cashflow', icon: TrendingUp },
            ]
          },
          {
            id: 'settings',
            title: 'SETTINGS',
            items: [
              { name: 'Chart of Accounts', path: '/accounting/chart-of-accounts', icon: List },
              { name: 'Period Closing', path: '/accounting/period-closing', icon: Lock },
            ]
          },
        ]
      };
    } else if (user.role === 'resident') {
      return {
        dashboard: { name: 'Dashboard', path: '/resident/dashboard', icon: BarChart3 },
        sections: [
          {
            id: 'actions',
            title: 'ACTIONS',
            items: [
              { name: 'Submit Payment', path: '/resident/submit', icon: Send },
            ]
          },
        ]
      };
    }

    return { dashboard: null, sections: [] };
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
            <NotificationBell />
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {/* Dashboard Link */}
          {currentNav.dashboard && (
            <div className="mb-4">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                DASHBOARD
              </p>
              <Link
                to={currentNav.dashboard.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  location.pathname === currentNav.dashboard.path
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                <currentNav.dashboard.icon className="w-5 h-5" />
                <span className="font-medium">{currentNav.dashboard.name}</span>
              </Link>
            </div>
          )}

          {/* Grouped Sections */}
          {currentNav.sections.map((section) => (
            <div key={section.id} className="mb-4">
              <button
                onClick={() => toggleSection(section.id)}
                className="flex items-center justify-between w-full text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 hover:text-gray-300 transition-colors"
              >
                <span>{section.title}</span>
                {expandedSections[section.id] ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              
              {expandedSections[section.id] && (
                <div className="space-y-1">
                  {section.items.map((item) => {
                    const isActive = location.pathname === item.path;
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-colors ${
                          isActive
                            ? 'bg-primary-600 text-white'
                            : 'text-gray-300 hover:bg-slate-700 hover:text-white'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        <span className="font-medium text-sm">{item.name}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </nav>

        {/* Logout Button */}
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
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
