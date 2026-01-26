/**
 * UnifiedLogin.jsx
 * Phase R.4 - Unified Login Page
 * 
 * Layout:
 * - ResidentLogin as PRIMARY (always visible)
 * - Admin login modal triggered by small button at bottom
 * 
 * Rules:
 * - NO role toggle
 * - NO shared form
 * - NO shared validation
 * - NO unified auth logic
 * - Separate components, separate state
 */

import { useState } from 'react';
import ResidentLogin from './resident/auth/ResidentLogin';
import AdminLoginModal from './resident/auth/AdminLoginModal';
import { Shield } from 'lucide-react';

export default function UnifiedLogin() {
  // Admin modal state (NOT shared with ResidentLogin)
  const [showAdminModal, setShowAdminModal] = useState(false);
  
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Primary: Resident OTP Login (always visible) */}
      <div className="flex-1 flex flex-col">
        <ResidentLogin />
        
        {/* Secondary: Admin login trigger at bottom */}
        <div className="p-4 text-center">
          <button
            onClick={() => setShowAdminModal(true)}
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            <Shield className="w-4 h-4" />
            <span>ผู้ดูแลระบบ / Admin</span>
          </button>
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
