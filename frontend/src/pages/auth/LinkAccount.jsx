/**
 * LinkAccount.jsx
 * Phase R.3: LINE Account Linking Page
 * 
 * Shown when resident LINE login → line_user_id not found in DB
 * Resident enters phone + house_code to link their LINE to a pre-created account.
 * 
 * Rules:
 * - NO user creation (admin must pre-create)
 * - Must match phone + house_code + ACTIVE membership
 * - Once linked, next LINE login goes directly to dashboard
 */

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { Loader2, AlertCircle, Link2, Home, Phone } from 'lucide-react';

export default function LinkAccount() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setResidentUser } = useAuth();
  
  const displayName = location.state?.displayName || '';
  
  const [phone, setPhone] = useState('');
  const [houseCode, setHouseCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleLink = async (e) => {
    e.preventDefault();
    
    if (!phone.trim() || !houseCode.trim()) {
      setError('กรุณากรอกข้อมูลให้ครบ');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/api/auth/line/link-account', {
        phone: phone.trim(),
        house_code: houseCode.trim(),
      });
      
      if (response.data.success) {
        if (response.data.message === 'SELECT_HOUSE_REQUIRED') {
          // Multi-house → go to house selection
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
        
        // Single house → set user and go to dashboard
        setResidentUser({
          id: response.data.user_id,
          full_name: response.data.display_name,
          role: 'resident',
          house_id: response.data.house_id || null,
          house_code: response.data.house_code || null,
          houses: response.data.houses || [],
        });
        
        navigate('/resident/dashboard', { replace: true });
      }
    } catch (err) {
      console.error('Link account error:', err);
      const detail = err.response?.data?.detail;
      
      if (detail?.code === 'NOT_FOUND') {
        setError('ไม่พบข้อมูล กรุณาตรวจสอบเบอร์โทรและบ้านเลขที่');
      } else if (detail?.code === 'ALREADY_LINKED') {
        setError('บัญชีนี้ผูกกับ LINE อื่นอยู่แล้ว กรุณาติดต่อผู้ดูแลหมู่บ้าน');
      } else if (detail?.code === 'LINE_ALREADY_USED') {
        setError('LINE นี้ผูกกับบัญชีอื่นอยู่แล้ว');
      } else if (detail?.code === 'TOKEN_EXPIRED' || detail?.code === 'NO_TOKEN') {
        setError('เซสชันหมดอายุ กรุณากลับไปเข้าสู่ระบบผ่าน LINE ใหม่');
      } else {
        setError(detail?.message || 'เกิดข้อผิดพลาด กรุณาลองใหม่');
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-white mb-2">
            <Home size={20} className="inline mr-1" />หมู่บ้านสมาร์ท
          </h1>
          <p className="text-gray-400 text-sm">
            ผูกบัญชี LINE กับข้อมูลลูกบ้าน
          </p>
        </div>
        
        {/* Card */}
        <div className="bg-gray-800 rounded-xl p-6 shadow-xl">
          {/* Welcome */}
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
              <Link2 className="w-8 h-8 text-green-400" />
            </div>
            <h2 className="text-lg font-semibold text-white mb-1">
              ผูกบัญชีของคุณ
            </h2>
            {displayName && (
              <p className="text-green-400 text-sm">
                สวัสดี, {displayName}
              </p>
            )}
            <p className="text-gray-400 text-xs mt-2">
              กรอกเบอร์โทรและบ้านเลขที่ที่ผู้ดูแลลงทะเบียนไว้
            </p>
          </div>
          
          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-500/30 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
          
          {/* Form */}
          <form onSubmit={handleLink} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">
                <Phone className="w-4 h-4 inline mr-1" />
                เบอร์โทรศัพท์
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="0812345678"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500"
                autoFocus
                disabled={loading}
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">
                <Home className="w-4 h-4 inline mr-1" />
                บ้านเลขที่
              </label>
              <input
                type="text"
                value={houseCode}
                onChange={(e) => setHouseCode(e.target.value)}
                placeholder="28/73"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500"
                disabled={loading}
              />
            </div>
            
            <button
              type="submit"
              disabled={loading || !phone.trim() || !houseCode.trim()}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-600/50 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  กำลังตรวจสอบ...
                </>
              ) : (
                <>
                  <Link2 className="w-5 h-5" />
                  ผูกบัญชี
                </>
              )}
            </button>
          </form>
          
          {/* Help text */}
          <p className="text-gray-500 text-xs text-center mt-4">
            ใช้เบอร์โทรและบ้านเลขที่เดียวกับที่ผู้ดูแลลงทะเบียนไว้ให้
          </p>
        </div>
        
        {/* Back to LINE login */}
        <div className="text-center mt-4">
          <button
            onClick={() => navigate('/login', { replace: true })}
            className="text-gray-500 hover:text-gray-300 text-sm transition-colors"
          >
            ← กลับหน้าเข้าสู่ระบบ
          </button>
        </div>
      </div>
    </div>
  );
}
