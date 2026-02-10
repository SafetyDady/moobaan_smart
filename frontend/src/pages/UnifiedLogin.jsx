/**
 * UnifiedLogin.jsx
 * Phase D.4.1 - Unified Login Page (LINE OA Gateway)
 * 
 * Flow:
 * - If LINE OAuth callback (code param) → process LINE login
 * - If from LINE OA (no admin param) → auto-redirect to LINE
 * - Admin login via modal triggered by small button
 * 
 * Rules:
 * - LINE Login as PRIMARY for residents
 * - Admin login via modal
 * - NO shared state between LINE and admin
 */

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import LineLogin from './auth/LineLogin';
import AdminLoginModal from './resident/auth/AdminLoginModal';
import { Shield } from 'lucide-react';

export default function UnifiedLogin() {
  const [searchParams] = useSearchParams();
  const [showAdminModal, setShowAdminModal] = useState(false);
  
  // Check if this is a LINE OAuth callback
  const hasLineCode = searchParams.has('code');
  const hasLineError = searchParams.has('error');
  
  // Check if admin mode is requested
  const isAdminMode = searchParams.get('mode') === 'admin';
  
  // If LINE callback or not admin mode, show LINE login
  if (hasLineCode || hasLineError || !isAdminMode) {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col">
        {/* LINE Login Flow */}
        <div className="flex-1">
          <LineLogin />
        </div>
        
        {/* Admin login trigger (only shown if not processing LINE callback) */}
        {!hasLineCode && !hasLineError && (
          <div className="p-4 text-center">
            <button
              onClick={() => setShowAdminModal(true)}
              className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
            >
              <Shield className="w-4 h-4" />
              <span>ผู้ดูแลระบบ / Admin</span>
            </button>
          </div>
        )}
        
        {/* Admin Login Modal */}
        <AdminLoginModal
          isOpen={showAdminModal}
          onClose={() => setShowAdminModal(false)}
        />
      </div>
    );
  }
  
  // Admin mode: show admin login modal directly
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center">
      <AdminLoginModal
        isOpen={true}
        onClose={() => window.location.href = '/login'}
      />
    </div>
  );
}
