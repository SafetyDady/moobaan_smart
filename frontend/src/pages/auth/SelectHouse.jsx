/**
 * SelectHouse.jsx
 * PATCH-2 rev: House selection page for multi-house residents.
 *
 * Flow:
 * 1. LINE login (multi-house) redirects here with houses[] in location.state
 * 2. User picks a house from the list
 * 3. Frontend POST /api/auth/select-house { house_id }
 * 4. Backend validates membership, issues FULL JWT, returns user object
 * 5. Frontend sets auth context and navigates to /resident/dashboard
 *
 * Guard:
 * - If no houses in state → redirect to /login
 * - If API fails → show error, allow retry
 */

import { useState } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { Loader2, Home, ChevronRight } from 'lucide-react';

export default function SelectHouse() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setResidentUser } = useAuth();

  const [selecting, setSelecting] = useState(false);
  const [error, setError] = useState(null);

  // Read houses from navigation state (passed by LineLogin.jsx)
  const houses = location.state?.houses || [];
  const displayName = location.state?.displayName || '';

  // Guard: if no houses data, redirect back to login
  if (houses.length === 0) {
    return <Navigate to="/login" replace />;
  }

  const handleSelectHouse = async (house) => {
    setSelecting(true);
    setError(null);

    try {
      const response = await api.post('/api/auth/select-house', {
        house_id: house.id,
      });

      if (response.data.success) {
        // Set full user in auth context (PATCH-5 shape)
        const userData = response.data.user;
        setResidentUser({
          id: userData.id,
          full_name: userData.full_name,
          role: userData.role,
          house_id: userData.house_id,
          house_code: userData.house_code,
          houses: userData.houses || [],
        });

        // Navigate to resident dashboard
        navigate('/resident/dashboard', { replace: true });
      }
    } catch (err) {
      console.error('House selection error:', err);
      const detail = err.response?.data?.detail;

      if (detail?.code === 'INVALID_HOUSE') {
        setError(detail.message || 'ไม่พบสิทธิ์เข้าถึงบ้านที่เลือก');
      } else if (err.response?.status === 401) {
        // Token expired — redirect to login
        setError('เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่');
        setTimeout(() => navigate('/login', { replace: true }), 2000);
      } else {
        setError(
          typeof detail === 'string'
            ? detail
            : 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง'
        );
      }
    } finally {
      setSelecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-white mb-1">🏠 เลือกบ้าน</h1>
          {displayName && (
            <p className="text-gray-400 text-sm">
              สวัสดี {displayName}
            </p>
          )}
          <p className="text-gray-500 text-xs mt-1">
            กรุณาเลือกบ้านที่ต้องการเข้าใช้งาน
          </p>
        </div>

        {/* House list */}
        <div className="space-y-3">
          {houses.map((house) => (
            <button
              key={house.id}
              onClick={() => handleSelectHouse(house)}
              disabled={selecting}
              className="w-full bg-gray-800 hover:bg-gray-700 disabled:opacity-50 
                         rounded-xl p-4 shadow-lg transition-colors
                         flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-900/40 rounded-lg flex items-center justify-center">
                  <Home className="w-5 h-5 text-green-400" />
                </div>
                <div className="text-left">
                  <p className="text-white font-medium">
                    บ้านเลขที่ {house.house_code}
                  </p>
                  <p className="text-gray-500 text-xs capitalize">
                    {house.role === 'owner' ? 'เจ้าของ' : 
                     house.role === 'family' ? 'สมาชิก' : house.role}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-green-400 transition-colors" />
            </button>
          ))}
        </div>

        {/* Loading overlay */}
        {selecting && (
          <div className="mt-4 text-center">
            <Loader2 className="w-6 h-6 text-green-500 animate-spin mx-auto mb-2" />
            <p className="text-gray-400 text-sm">กำลังเข้าสู่ระบบ...</p>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mt-4 bg-red-900/30 border border-red-800 rounded-lg p-3">
            <p className="text-red-400 text-sm text-center">{error}</p>
          </div>
        )}

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
