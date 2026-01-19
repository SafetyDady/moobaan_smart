/**
 * MobileLayout - Resident Mobile-only Layout
 * 
 * Per OPTION A.1 Spec:
 * - Single column layout (100vw)
 * - Card-based UI only
 * - No tables, no hover
 * - Minimum 44px tap target
 * - Thai language only
 * - Bottom navigation = primary navigation
 * - No sidebar, no top desktop menu
 */

import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { useRole } from '../../../contexts/RoleContext';

export default function MobileLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { currentHouseCode } = useRole();

  const handleLogout = async () => {
    if (confirm('ต้องการออกจากระบบหรือไม่?')) {
      await logout();
      navigate('/login');
    }
  };

  const navItems = [
    { 
      path: '/resident/dashboard', 
      icon: '🏠', 
      label: 'หน้าหลัก',
      activeIcon: '🏠'
    },
    { 
      path: '/resident/village', 
      icon: '📈', 
      label: 'ภาพรวม',
      activeIcon: '📈'
    },
    { 
      path: '/resident/submit', 
      icon: '📸', 
      label: 'ส่งสลิป',
      activeIcon: '📸',
      isPrimary: true
    },
    { 
      path: '/resident/payments', 
      icon: '📄', 
      label: 'ประวัติ',
      activeIcon: '📄'
    },
    { 
      path: '/resident/profile', 
      icon: '👤', 
      label: 'โปรไฟล์',
      activeIcon: '👤'
    },
  ];

  return (
    // Full width layout - same on mobile and desktop (100vw)
    <div className="flex flex-col min-h-screen w-full bg-gray-900">
      {/* Header - Sticky top */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between sticky top-0 z-20">
        <div>
          <h1 className="text-lg font-bold text-primary-400">
            🏘️ Moobaan Smart
          </h1>
          <p className="text-xs text-gray-400">
            {currentHouseCode ? `บ้านเลขที่ ${currentHouseCode}` : (user?.name || 'ลูกบ้าน')}
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="text-gray-400 active:text-white text-sm px-3 py-2 rounded bg-gray-700 min-h-[44px] min-w-[44px]"
        >
          ออกจากระบบ
        </button>
      </header>

      {/* Content Area - with bottom padding for nav */}
      <main className="flex-1 overflow-y-auto pb-20">
        {children}
      </main>

      {/* Bottom Navigation - Fixed sticky bottom bar */}
      <nav className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 z-30">
        <div className="flex">
          {navItems.map(item => {
            const isActive = location.pathname === item.path;
            
            // Special styling for primary action button (center)
            if (item.isPrimary) {
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className="flex-1 flex flex-col items-center justify-center min-h-[64px]"
                >
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-1 transition-colors ${
                    isActive ? 'bg-primary-500' : 'bg-gray-700'
                  }`}>
                    <span className="text-2xl">{item.icon}</span>
                  </div>
                  <span className={`text-xs ${
                    isActive ? 'text-primary-400 font-semibold' : 'text-gray-400 font-medium'
                  }`}>
                    {item.label}
                  </span>
                </Link>
              );
            }
            
            // Regular nav items
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex-1 flex flex-col items-center justify-center min-h-[64px] transition-colors ${
                  isActive 
                    ? 'text-primary-400 bg-gray-750' 
                    : 'text-gray-400 active:bg-gray-750'
                }`}
              >
                <span className="text-2xl mb-0.5">
                  {isActive ? item.activeIcon : item.icon}
                </span>
                <span className={`text-xs font-medium ${isActive ? 'font-semibold' : ''}`}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
