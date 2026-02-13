/**
 * LineLogin.jsx
 * Phase D.4.1 - LINE Login Page (Resident Entry Point)
 * 
 * Flow:
 * 1. Page loads → auto-redirect to LINE authorization
 * 2. User authorizes in LINE
 * 3. LINE redirects back with code
 * 4. Frontend calls backend /api/auth/line/login
 * 5. Success → redirect to /resident/dashboard
 * 6. Error → show message
 * 
 * Rules:
 * - NO form
 * - NO OTP
 * - NO phone
 * - NO toggle
 * - Auto-trigger LINE OAuth
 */

import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { Loader2, AlertCircle, ExternalLink, Home } from 'lucide-react';

// LINE Login states
const STATE = {
  LOADING: 'loading',
  REDIRECTING: 'redirecting',
  PROCESSING: 'processing',
  ERROR: 'error',
};

export default function LineLogin() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setResidentUser } = useAuth();
  
  const [state, setState] = useState(STATE.LOADING);
  const [error, setError] = useState(null);
  
  // Get redirect URI for LINE OAuth
  // LINE OAuth requires a redirect_uri that is EXACTLY registered in LINE Developers Console
  // Production: https://moobaan-smart.vercel.app/login
  // Local dev: http://localhost:5173/login (must also be registered in LINE console)
  const getRedirectUri = () => {
    // In production (Vercel), always use the stable production URL
    if (import.meta.env.PROD) {
      return 'https://moobaan-smart.vercel.app/login';
    }
    // Local development
    return `${window.location.origin}/login`;
  };
  
  // Handle LINE OAuth callback (when code is in URL)
  const handleLineCallback = async (code) => {
    setState(STATE.PROCESSING);
    
    try {
      const response = await api.post('/api/auth/line/login', {
        code: code,
        redirect_uri: getRedirectUri(),
      });
      
      if (response.data.success) {
        // R.3: LINE user not bound yet → redirect to link account page
        if (response.data.message === 'NEED_LINK') {
          navigate('/link-account', {
            replace: true,
            state: {
              displayName: response.data.display_name || '',
            },
          });
          return;
        }
        
        // PATCH-2 rev: Check if house selection is required (multi-house)
        if (response.data.message === 'SELECT_HOUSE_REQUIRED') {
          // Multi-house resident — redirect to house selection page
          navigate('/select-house', {
            replace: true,
            state: {
              houses: response.data.houses || [],
              userId: response.data.user_id,
              displayName: response.data.display_name,
            },
          });
          return;
        }
        
        // Case A: Single house — set full user and go to dashboard
        setResidentUser({
          id: response.data.user_id,
          full_name: response.data.display_name,
          role: 'resident',
          house_id: response.data.house_id || null,
          house_code: response.data.house_code || null,
          houses: response.data.houses || [],
        });
        
        // Redirect to dashboard
        navigate('/resident/dashboard', { replace: true });
      }
    } catch (err) {
      console.error('LINE login error:', err);
      const detail = err.response?.data?.detail;
      
      if (detail?.code === 'NOT_REGISTERED_RESIDENT') {
        setError({
          title: 'ไม่พบสิทธิ์การใช้งาน',
          message: detail.message || 'บัญชีนี้ยังไม่ได้รับสิทธิ์ใช้งาน กรุณาติดต่อผู้ดูแลหมู่บ้าน',
        });
      } else if (detail?.code === 'LINE_AUTH_FAILED') {
        setError({
          title: 'การยืนยันตัวตนล้มเหลว',
          message: 'ไม่สามารถยืนยันตัวตนกับ LINE ได้ กรุณาลองใหม่อีกครั้ง',
        });
      } else {
        setError({
          title: 'เกิดข้อผิดพลาด',
          message: typeof detail === 'string' ? detail : 'ไม่สามารถเข้าสู่ระบบได้ กรุณาลองใหม่อีกครั้ง',
        });
      }
      setState(STATE.ERROR);
    }
  };
  
  // Redirect to LINE authorization
  const redirectToLine = async () => {
    setState(STATE.REDIRECTING);
    
    try {
      // Debug: log API base URL and redirect URI for troubleshooting
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'NOT SET (fallback to localhost)';
      const redirectUri = getRedirectUri();
      console.log('[LINE] API_BASE_URL:', apiBaseUrl);
      console.log('[LINE] redirect_uri:', redirectUri);
      
      const response = await api.get('/api/auth/line/config', {
        params: { redirect_uri: redirectUri },
      });
      
      console.log('[LINE] config response:', response.data);
      
      // Redirect to LINE authorization URL
      window.location.href = response.data.login_url;
    } catch (err) {
      console.error('LINE config error:', err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.message;
      console.error('[LINE] Error status:', status, 'detail:', detail);
      setError({
        title: 'ระบบยังไม่พร้อม',
        message: `ระบบ LINE Login ยังไม่พร้อมใช้งาน กรุณาติดต่อผู้ดูแลหมู่บ้าน (${status || 'network error'})`,
      });
      setState(STATE.ERROR);
    }
  };
  
  // On mount: check for callback code or redirect to LINE
  useEffect(() => {
    const code = searchParams.get('code');
    const errorParam = searchParams.get('error');
    
    if (errorParam) {
      // LINE returned an error
      setError({
        title: 'การยืนยันตัวตนถูกยกเลิก',
        message: 'คุณได้ยกเลิกการเข้าสู่ระบบผ่าน LINE',
      });
      setState(STATE.ERROR);
      return;
    }
    
    if (code) {
      // Handle LINE callback
      handleLineCallback(code);
    } else {
      // No code, redirect to LINE
      redirectToLine();
    }
  }, [searchParams]);
  
  // Retry login
  const handleRetry = () => {
    setError(null);
    setState(STATE.LOADING);
    redirectToLine();
  };
  
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-900/40 mb-4">
            <Home size={32} className="text-white" strokeWidth={2.2} />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Moobaan Smart
          </h1>
          <p className="text-gray-400 text-sm">
            ระบบจัดการหมู่บ้าน
          </p>
        </div>
        
        {/* Content based on state */}
        <div className="bg-gray-800 rounded-xl p-6 shadow-xl">
          {(state === STATE.LOADING || state === STATE.REDIRECTING) && (
            <div className="text-center py-8">
              <Loader2 className="w-12 h-12 text-green-500 animate-spin mx-auto mb-4" />
              <p className="text-gray-300">
                {state === STATE.LOADING ? 'กำลังเตรียมระบบ...' : 'กำลังเชื่อมต่อ LINE...'}
              </p>
              <p className="text-gray-500 text-sm mt-2">
                กรุณารอสักครู่
              </p>
            </div>
          )}
          
          {state === STATE.PROCESSING && (
            <div className="text-center py-8">
              <Loader2 className="w-12 h-12 text-green-500 animate-spin mx-auto mb-4" />
              <p className="text-gray-300">กำลังเข้าสู่ระบบ...</p>
              <p className="text-gray-500 text-sm mt-2">
                กำลังตรวจสอบสิทธิ์การใช้งาน
              </p>
            </div>
          )}
          
          {state === STATE.ERROR && error && (
            <div className="text-center py-6">
              <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-red-400" />
              </div>
              
              <h2 className="text-lg font-semibold text-white mb-2">
                {error.title}
              </h2>
              
              <p className="text-gray-400 text-sm mb-6">
                {error.message}
              </p>
              
              <button
                onClick={handleRetry}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <ExternalLink className="w-5 h-5" />
                ลองใหม่อีกครั้ง
              </button>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-gray-600 text-xs">
            เข้าสู่ระบบผ่าน LINE Official Account
          </p>
        </div>
      </div>
    </div>
  );
}
