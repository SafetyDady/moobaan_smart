/**
 * UnifiedLogin.jsx
 * Landing Page — Choose Login Method
 * 
 * Flow:
 * - If LINE OAuth callback (code/error param) → process via LineLogin
 * - Otherwise → show Landing Page with 2 buttons:
 *   1. LINE Login (Resident) — redirects to LINE OAuth
 *   2. Admin Login — opens modal
 * 
 * Rules:
 * - NO auto-redirect
 * - User explicitly chooses their login method
 * - Clean UX, zero confusion
 */

import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import LineLogin from './auth/LineLogin';
import AdminLoginModal from './resident/auth/AdminLoginModal';
import { Shield, MessageCircle } from 'lucide-react';

export default function UnifiedLogin() {
  const [searchParams] = useSearchParams();
  const [showAdminModal, setShowAdminModal] = useState(false);
  const [startLineLogin, setStartLineLogin] = useState(false);
  
  // Check if this is a LINE OAuth callback
  const hasLineCode = searchParams.has('code');
  const hasLineError = searchParams.has('error');
  const isLineCallback = hasLineCode || hasLineError;
  
  // If LINE callback → process via LineLogin component
  if (isLineCallback) {
    return <LineLogin />;
  }
  
  // If user clicked LINE Login → show LineLogin with auto-redirect
  if (startLineLogin) {
    return <LineLogin />;
  }
  
  // Landing Page — Choose Login Method
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo/Header */}
        <div className="text-center mb-10">
          <div className="text-5xl mb-4">🏠</div>
          <h1 className="text-2xl font-bold text-white mb-2">
            หมู่บ้านสมาร์ท
          </h1>
          <p className="text-gray-400 text-sm">
            ระบบจัดการหมู่บ้าน
          </p>
        </div>
        
        {/* Login Options */}
        <div className="space-y-4">
          {/* LINE Login — Primary (Resident) */}
          <button
            onClick={() => setStartLineLogin(true)}
            className="w-full bg-[#06C755] hover:bg-[#05b34d] text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-3 shadow-lg shadow-green-900/30 hover:shadow-green-900/50 hover:scale-[1.02] active:scale-[0.98]"
          >
            <MessageCircle className="w-6 h-6" />
            <span className="text-lg">เข้าสู่ระบบด้วย LINE</span>
          </button>
          
          <p className="text-center text-gray-500 text-xs">
            สำหรับลูกบ้าน / Resident
          </p>
          
          {/* Divider */}
          <div className="flex items-center gap-3 py-2">
            <div className="flex-1 h-px bg-gray-700"></div>
            <span className="text-gray-500 text-xs">หรือ</span>
            <div className="flex-1 h-px bg-gray-700"></div>
          </div>
          
          {/* Admin Login — Secondary */}
          <button
            onClick={() => setShowAdminModal(true)}
            className="w-full bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white font-medium py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-3 border border-gray-700 hover:border-gray-600"
          >
            <Shield className="w-5 h-5" />
            <span>เข้าสู่ระบบสำหรับผู้ดูแล</span>
          </button>
          
          <p className="text-center text-gray-600 text-xs">
            Admin / Super Admin
          </p>
        </div>
        
        {/* Footer */}
        <div className="text-center mt-10">
          <p className="text-gray-700 text-xs">
            © หมู่บ้านสมาร์ท — ระบบจัดการหมู่บ้านอัจฉริยะ
          </p>
        </div>
      </div>
      
      {/* Admin Login Modal */}
      <AdminLoginModal
        isOpen={showAdminModal}
        onClose={() => setShowAdminModal(false)}
      />
    </div>
  );
}
