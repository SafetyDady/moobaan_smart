/**
 * AdminLoginModal.jsx
 * Phase R.4 - Admin Login Modal (Secondary)
 * 
 * Rules:
 * - Completely separate from ResidentLogin
 * - Reuses existing admin login logic (POST /api/auth/login)
 * - Modal form with email/password
 * - Reset state on close
 * - NO modification to existing admin behavior
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { X, Building2, Mail, Lock, Loader2, Eye, EyeOff } from 'lucide-react';

export default function AdminLoginModal({ isOpen, onClose }) {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  // Admin-specific state (NOT shared with resident)
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setEmail('');
      setPassword('');
      setShowPassword(false);
      setError('');
      setLoading(false);
    }
  }, [isOpen]);
  
  // Handle form submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      setError('กรุณากรอกอีเมลและรหัสผ่าน');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Use existing AuthContext login (POST /api/auth/login)
      await login({ email, password });
      
      // Success - redirect to admin dashboard
      onClose();
      navigate('/admin/dashboard');
    } catch (err) {
      console.error('Admin login error:', err);
      if (err.response?.status === 401) {
        setError('อีเมลหรือรหัสผ่านไม่ถูกต้อง');
      } else if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        // Handle both string and object error formats
        if (typeof detail === 'string') {
          setError(detail);
        } else if (Array.isArray(detail)) {
          // Pydantic validation errors array
          setError(detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', '));
        } else if (typeof detail === 'object') {
          setError(detail.message || detail.msg || JSON.stringify(detail));
        } else {
          setError('เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง');
        }
      } else {
        setError('เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง');
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Handle backdrop click
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget && !loading) {
      onClose();
    }
  };
  
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen && !loading) {
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, loading, onClose]);
  
  if (!isOpen) return null;
  
  return (
    <div 
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-md border border-gray-700 relative animate-in fade-in zoom-in-95 duration-200">
        {/* Close button */}
        <button
          onClick={onClose}
          disabled={loading}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <X className="w-6 h-6" />
        </button>
        
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Building2 className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">เข้าสู่ระบบผู้ดูแล</h2>
              <p className="text-sm text-gray-400">Admin / Accounting Login</p>
            </div>
          </div>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Error message */}
          {error && (
            <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          
          {/* Email field */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              อีเมล
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(''); }}
                className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
                placeholder="admin@example.com"
                required
                disabled={loading}
                autoComplete="email"
              />
            </div>
          </div>
          
          {/* Password field */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              รหัสผ่าน
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(''); }}
                className="w-full pl-10 pr-12 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                required
                disabled={loading}
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>
          
          {/* Remember me */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="admin-remember"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              disabled={loading}
              className="w-4 h-4 text-amber-500 bg-gray-700 border-gray-600 rounded focus:ring-amber-500 focus:ring-2"
            />
            <label htmlFor="admin-remember" className="ml-2 text-sm text-gray-300">
              จดจำฉันไว้
            </label>
          </div>
          
          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-amber-500 hover:bg-amber-600 text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>กำลังเข้าสู่ระบบ...</span>
              </>
            ) : (
              <span>เข้าสู่ระบบ</span>
            )}
          </button>
        </form>
        
        {/* Footer */}
        <div className="px-6 pb-6">
          <p className="text-xs text-gray-500 text-center">
            หากลืมรหัสผ่าน กรุณาติดต่อผู้ดูแลระบบ
          </p>
        </div>
      </div>
    </div>
  );
}
