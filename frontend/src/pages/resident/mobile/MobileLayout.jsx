/**
 * MobileLayout - Resident Mobile-only Layout (IMPROVED UI/UX)
 * 
 * Bottom Navigation (Left to Right):
 * 1. บ้าน (Dashboard) - Icon: Home (Lucide)
 * 2. มบ. (Village Stats) - Icon: BarChart3 (Lucide)
 * 3. แจ้งชำระ (Submit Payment) - Icon: CreditCard (Lucide) - PRIMARY
 * 4. ประวัติ (Payment History) - Icon: History (Lucide)
 * 5. โปรไฟล์ (Profile) - Icon: User (Lucide)
 * 
 * Improvements:
 * - Replaced emoji icons with Lucide React icons
 * - Enhanced visual hierarchy
 * - Improved touch targets (min 48px)
 * - Better active states with transitions
 * - Primary action button with elevation
 */

import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, BarChart3, CreditCard, History, User, LogOut } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../../../contexts/AuthContext';
import ConfirmModal from '../../../components/ConfirmModal';
import { useRole } from '../../../contexts/RoleContext';
import { t } from '../../../hooks/useLocale';

export default function MobileLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { currentHouseCode } = useRole();

  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleLogout = async () => {
    setShowLogoutConfirm(false);
    await logout();
    navigate('/login');
  };

  const navItems = [
    { 
      path: '/resident/dashboard', 
      icon: Home, 
      label: t('mobileLayout.navHome'),
      size: 24
    },
    { 
      path: '/resident/village', 
      icon: BarChart3,
      label: t('mobileLayout.navVillage'),
      size: 24
    },
    { 
      path: '/resident/submit', 
      icon: CreditCard,
      label: t('mobileLayout.navSubmit'),
      size: 24,
      isPrimary: true
    },
    { 
      path: '/resident/payments', 
      icon: History, 
      label: t('mobileLayout.navHistory'),
      size: 24
    },
    { 
      path: '/resident/profile', 
      icon: User, 
      label: t('mobileLayout.navProfile'),
      size: 24
    },
  ];

  return (
    // Full width layout - same on mobile and desktop (100vw)
    <div className="flex flex-col min-h-screen w-full bg-gray-900">
      {/* Header - Enhanced with better spacing */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between sticky top-0 z-20 shadow-sm">
        <div>
          <h1 className="text-lg font-bold text-primary-400 flex items-center gap-2">
            <Home size={20} className="text-primary-500" />
            {t('mobileLayout.appName')}
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            {currentHouseCode ? `${t('mobileLayout.houseNo')} ${currentHouseCode}` : (user?.name || t('mobileLayout.resident'))}
          </p>
        </div>
        <button
          onClick={() => setShowLogoutConfirm(true)}
          className="flex items-center gap-2 text-gray-400 hover:text-white active:text-white 
                     text-sm px-3 py-2 rounded-lg bg-gray-700 hover:bg-gray-600
                     transition-colors duration-200 min-h-[44px]"
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">{t('mobileLayout.logout')}</span>
        </button>
      </header>

      {/* Content Area - with bottom padding for nav */}
      <main className="flex-1 overflow-y-auto pb-20">
        {children}
      </main>

      {/* Bottom Navigation - Enhanced with better visual hierarchy */}
      <nav className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 z-30 shadow-lg">
        <div className="flex items-center justify-around">
          {navItems.map(item => {
            const isActive = location.pathname === item.path;
            const IconComponent = item.icon;
            
            // Special styling for primary action button (center)
            if (item.isPrimary) {
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className="flex-1 flex flex-col items-center justify-center min-h-[68px] py-2"
                >
                  <div className={`w-14 h-14 rounded-full flex items-center justify-center mb-1 
                                  transition-all duration-200 shadow-lg
                                  ${
                                    isActive 
                                      ? 'bg-primary-500 shadow-primary-500/50' 
                                      : 'bg-gray-700 hover:bg-gray-600'
                                  }`}>
                    <IconComponent 
                      size={item.size} 
                      className={isActive ? 'text-white' : 'text-gray-300'}
                      strokeWidth={2.5}
                    />
                  </div>
                  <span className={`text-xs font-medium transition-colors
                                  ${isActive ? 'text-primary-400 font-semibold' : 'text-gray-400'}`}>
                    {item.label}
                  </span>
                </Link>
              );
            }
            
            // Regular nav items with improved styling
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex-1 flex flex-col items-center justify-center min-h-[68px] py-2
                           transition-all duration-200
                           ${
                             isActive 
                               ? 'text-primary-400 bg-gray-750' 
                               : 'text-gray-400 hover:text-gray-300 hover:bg-gray-750'
                           }`}
              >
                <IconComponent 
                  size={item.size} 
                  className="mb-1"
                  strokeWidth={isActive ? 2.5 : 2}
                />
                <span className={`text-xs transition-all
                                ${isActive ? 'font-semibold' : 'font-medium'}`}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
      <ConfirmModal
        open={showLogoutConfirm}
        title={t('mobileLayout.logoutConfirmTitle')}
        message={t('mobileLayout.logoutConfirmMsg')}
        variant="warning"
        confirmText={t('mobileLayout.logout')}
        onConfirm={handleLogout}
        onCancel={() => setShowLogoutConfirm(false)}
      />
    </div>
  );
}
