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
      path: '/resident/submit', 
      icon: '💳', 
      label: 'ชำระเงิน',
      activeIcon: '💳'
    },
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between sticky top-0 z-20">
        <div>
          <h1 className="text-lg font-bold text-primary-400">
            🏘️ Moobaan Smart
          </h1>
          <p className="text-xs text-gray-400">
            {currentHouseCode ? `บ้านเลขที่ ${currentHouseCode}` : (user?.name || 'Resident')}
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="text-gray-400 hover:text-white text-sm px-3 py-1.5 rounded bg-gray-700"
        >
          ออกจากระบบ
        </button>
      </header>

      {/* Content Area - with bottom padding for nav */}
      <main className="flex-1 overflow-y-auto pb-20">
        {children}
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 z-30">
        <div className="flex">
          {navItems.map(item => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex-1 flex flex-col items-center justify-center h-16 transition-colors ${
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
