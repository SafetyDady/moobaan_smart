/**
 * Phase 2 - Task 2.3: Mobile Navigation Overlay
 * 
 * Since Layout.jsx is forbidden, this component provides a mobile-only
 * hamburger menu button that overlays on top of the existing layout.
 * On mobile/tablet, the sidebar is hidden via CSS and this component
 * provides a slide-out drawer navigation.
 * 
 * This works by:
 * 1. CSS media query hides the sidebar on screens < 1024px
 * 2. This component shows a hamburger button (fixed position)
 * 3. Clicking it opens a slide-out drawer with the same nav links
 * 4. The drawer closes on link click or backdrop click
 */
import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { t } from '../hooks/useLocale';
import {
  BarChart3, Home, Users, Building2, FileText, DollarSign,
  TrendingDown, CreditCard, PieChart, TrendingUp, List,
  Lock, LogOut, ChevronDown, ChevronRight, GitCompare,
  HelpCircle, UserCog, Send, Menu, X
} from 'lucide-react';

export default function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();
  const [expandedSections, setExpandedSections] = useState({
    management: true,
    finance: true,
    reporting: false,
    settings: false,
    actions: true,
  });

  // Close drawer on route change
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
  };

  // Navigation based on user role (mirrors Layout.jsx)
  const getNavigation = () => {
    if (!user) return { dashboard: null, sections: [] };

    if (user.role === 'super_admin') {
      return {
        dashboard: { name: t('nav.dashboard'), path: '/admin/dashboard', icon: BarChart3 },
        sections: [
          {
            id: 'management',
            title: t('nav.management'),
            items: [
              { name: t('nav.manageHouses'), path: '/admin/houses', icon: Home },
              { name: t('nav.memberRegistry'), path: '/admin/members', icon: Users },
              { name: t('nav.vendors'), path: '/admin/vendors', icon: Building2 },
              { name: t('nav.userManagement'), path: '/admin/users', icon: UserCog },
            ]
          },
          {
            id: 'finance',
            title: t('nav.finance'),
            items: [
              { name: t('nav.invoices'), path: '/admin/invoices', icon: FileText },
              { name: t('nav.paymentReview'), path: '/admin/payins', icon: DollarSign },
              { name: t('nav.expenses'), path: '/admin/expenses', icon: TrendingDown },
              { name: t('nav.bankStatements'), path: '/admin/statements', icon: CreditCard },
              { name: t('nav.expenseRecon'), path: '/admin/expense-reconciliation', icon: GitCompare },
              { name: t('nav.unidentifiedReceipts'), path: '/admin/unidentified-receipts', icon: HelpCircle },
            ]
          },
          {
            id: 'reporting',
            title: t('nav.reports'),
            items: [
              { name: t('nav.agingReport'), path: '/admin/reports/aging', icon: PieChart },
              { name: t('nav.cashFlowReport'), path: '/admin/reports/cashflow', icon: TrendingUp },
            ]
          },
          {
            id: 'settings',
            title: t('nav.settings'),
            items: [
              { name: t('nav.chartOfAccounts'), path: '/admin/chart-of-accounts', icon: List },
              { name: t('nav.periodClosing'), path: '/admin/period-closing', icon: Lock },
            ]
          },
        ]
      };
    } else if (user.role === 'accounting') {
      return {
        dashboard: { name: t('nav.dashboard'), path: '/accounting/dashboard', icon: BarChart3 },
        sections: [
          {
            id: 'finance',
            title: t('nav.finance'),
            items: [
              { name: t('nav.invoices'), path: '/accounting/invoices', icon: FileText },
              { name: t('nav.paymentReview'), path: '/accounting/payins', icon: DollarSign },
              { name: t('nav.expenses'), path: '/accounting/expenses', icon: TrendingDown },
              { name: t('nav.vendors'), path: '/accounting/vendors', icon: Building2 },
              { name: t('nav.bankStatements'), path: '/accounting/statements', icon: CreditCard },
              { name: t('nav.expenseRecon'), path: '/accounting/expense-reconciliation', icon: GitCompare },
              { name: t('nav.unidentifiedReceipts'), path: '/accounting/unidentified-receipts', icon: HelpCircle },
            ]
          },
          {
            id: 'reporting',
            title: t('nav.reports'),
            items: [
              { name: t('nav.agingReport'), path: '/accounting/reports/aging', icon: PieChart },
              { name: t('nav.cashFlowReport'), path: '/accounting/reports/cashflow', icon: TrendingUp },
            ]
          },
          {
            id: 'settings',
            title: t('nav.settings'),
            items: [
              { name: t('nav.chartOfAccounts'), path: '/accounting/chart-of-accounts', icon: List },
              { name: t('nav.periodClosing'), path: '/accounting/period-closing', icon: Lock },
            ]
          },
        ]
      };
    } else if (user.role === 'resident') {
      return {
        dashboard: { name: t('nav.dashboard'), path: '/resident/dashboard', icon: BarChart3 },
        sections: [
          {
            id: 'actions',
            title: t('nav.actions'),
            items: [
              { name: t('nav.submitPayment'), path: '/resident/submit', icon: Send },
            ]
          },
        ]
      };
    }

    return { dashboard: null, sections: [] };
  };

  const currentNav = getNavigation();

  const getRoleBadgeColor = () => {
    if (user?.role === 'super_admin') return 'bg-primary-600';
    if (user?.role === 'accounting') return 'bg-blue-600';
    return 'bg-gray-600';
  };

  const getRoleDisplayName = () => {
    if (user?.role === 'super_admin') return t('roles.super_admin');
    if (user?.role === 'accounting') return t('roles.accounting');
    if (user?.role === 'resident') return t('roles.resident');
    return '-';
  };

  return (
    <>
      {/* Hamburger Button - only visible on mobile/tablet */}
      <button
        onClick={() => setIsOpen(true)}
        className="mobile-nav-toggle fixed top-4 left-4 z-50 p-2 bg-slate-800 border border-gray-700 rounded-lg shadow-lg text-white hover:bg-slate-700 transition-colors"
        aria-label={t('common.openMenu')}
      >
        <Menu className="w-6 h-6" />
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-[60] transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Slide-out Drawer */}
      <aside
        className={`fixed top-0 left-0 h-full w-72 bg-slate-800 border-r border-gray-700 z-[70] transform transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold">
              {user?.name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.name || t('common.user')}
              </p>
              <span className={`inline-block px-2 py-0.5 text-xs rounded ${getRoleBadgeColor()} text-white`}>
                {getRoleDisplayName()}
              </span>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-slate-700 transition-colors"
            aria-label={t('common.closeMenu')}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {/* Dashboard Link */}
          {currentNav.dashboard && (
            <div className="mb-4">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                {t('nav.dashboard')}
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
            <span className="font-medium">{t('common.logout')}</span>
          </button>
        </div>
      </aside>
    </>
  );
}
