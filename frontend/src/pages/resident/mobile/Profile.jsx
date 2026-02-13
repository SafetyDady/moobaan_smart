import { useState, useEffect } from 'react';
import { ChevronLeft, LogOut, Home, User, Mail, Phone, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { useRole } from '../../../contexts/RoleContext';
import MobileLayout from './MobileLayout';

export default function Profile() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { currentHouseCode, currentHouseId } = useRole();
  const [toast, setToast] = useState(null);
  
  const showToast = (message) => {
    setToast(message);
    setTimeout(() => setToast(null), 2000);
  };
  
  const handleLogout = async () => {
    if (confirm('ต้องการออกจากระบบหรือไม่?')) {
      await logout();
      navigate('/login');
    }
  };
  
  return (
    <MobileLayout>
      {/* Toast notification */}
      {toast && (
        <div className="fixed top-4 left-4 right-4 z-50 bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
          <p className="text-sm text-gray-200 text-center">{toast}</p>
        </div>
      )}
      
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center gap-3">
          <button
            onClick={() => navigate('/resident/dashboard')}
            className="text-white active:text-gray-300"
          >
            <ChevronLeft size={24} />
          </button>
          <h1 className="text-lg font-bold text-white">โปรไฟล์</h1>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Profile Card */}
          <div className="bg-gradient-to-br from-primary-500 to-blue-600 rounded-xl p-6 text-center">
            <div className="w-20 h-20 bg-white/20 rounded-full mx-auto mb-3 flex items-center justify-center">
              <User size={40} className="text-white" />
            </div>
            <div className="text-xl font-bold text-white">
              {user?.full_name || 'ลูกบ้าน'}
            </div>
            {currentHouseCode && (
              <div className="text-sm text-white/80 mt-1">
                บ้านเลขที่ {currentHouseCode}
              </div>
            )}
          </div>
          
          {/* Info Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 divide-y divide-gray-700">
            <div className="p-4">
              <div className="text-xs text-gray-400 mb-1">ชื่อ-นามสกุล</div>
              <div className="flex items-center gap-2 text-white">
                <User size={18} className="text-gray-400" />
                <span>{user?.full_name || 'ไม่ได้ระบุ'}</span>
              </div>
            </div>
            
            <div className="p-4">
              <div className="text-xs text-gray-400 mb-1">อีเมล</div>
              <div className="flex items-center gap-2 text-white">
                <Mail size={18} className="text-gray-400" />
                <span>{user?.email || 'ไม่ได้ระบุ'}</span>
              </div>
            </div>
            
            <div className="p-4">
              <div className="text-xs text-gray-400 mb-1">เบอร์โทรศัพท์</div>
              <div className="flex items-center gap-2 text-white">
                <Phone size={18} className="text-gray-400" />
                <span>{user?.phone || 'ไม่ได้ระบุ'}</span>
              </div>
            </div>
            
            {currentHouseCode && (
              <div className="p-4">
                <div className="text-xs text-gray-400 mb-1">บ้านเลขที่</div>
                <div className="flex items-center gap-2 text-white">
                  <Home size={18} className="text-gray-400" />
                  <span>{currentHouseCode}</span>
                </div>
              </div>
            )}
          </div>
          
          {/* Account Info Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-sm font-medium text-gray-300">ข้อมูลบัญชี</h3>
            </div>
            
            <div className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield size={18} className="text-gray-400" />
                <span className="text-white">สถานะบัญชี</span>
              </div>
              <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-400">
                {user?.is_active ? 'ใช้งานอยู่' : 'ไม่ได้ใช้งาน'}
              </span>
            </div>
            
            <div className="p-4 flex items-center justify-between border-t border-gray-700">
              <div className="flex items-center gap-2">
                <span className="text-lg">🟢</span>
                <span className="text-white">LINE เชื่อมต่อ</span>
              </div>
              <span className="text-xs text-green-400">เข้าสู่ระบบผ่าน LINE</span>
            </div>
            
            {user?.houses && user.houses.length > 1 && (
              <div className="p-4 border-t border-gray-700">
                <div className="text-xs text-gray-400 mb-2">บ้านที่เชื่อมต่อ</div>
                <div className="flex flex-wrap gap-2">
                  {user.houses.map(h => (
                    <span key={h.id} className={`text-xs px-2 py-1 rounded-full ${
                      h.house_code === currentHouseCode 
                        ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30' 
                        : 'bg-gray-700 text-gray-300'
                    }`}>
                      บ้าน {h.house_code}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {/* About Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-2">เกี่ยวกับ</h3>
            <div className="text-xs text-gray-400 space-y-1">
              <div>แอปพลิเคชัน: Moobaan Smart</div>
              <div>เวอร์ชัน: 1.0.0</div>
              <div>© 2026 Moobaan Smart. All rights reserved.</div>
            </div>
          </div>
          
          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full bg-red-500/10 border border-red-500 text-red-400 rounded-lg p-4 flex items-center justify-center gap-2 font-medium active:bg-red-500/20"
          >
            <LogOut size={20} />
            <span>ออกจากระบบ</span>
          </button>
          
          {/* Bottom Spacing for Nav */}
          <div className="h-4"></div>
        </div>
      </div>
    </MobileLayout>
  );
}
