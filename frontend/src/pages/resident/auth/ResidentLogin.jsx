/**
 * ResidentLogin.jsx
 * Phase R.4 - Resident OTP Login Flow
 * 
 * Flow:
 * 1. Request OTP (phone number)
 * 2. Verify OTP (6 digits)
 * 3. Select House (if multiple)
 * 4. Redirect to /resident/dashboard
 * 
 * Rules:
 * - Mobile-first design
 * - NO admin logic
 * - NO house_id in payloads (backend uses token)
 * - Separate state from admin login
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../../api/client';
import { useAuth } from '../../../contexts/AuthContext';
import { Building2, Phone, KeyRound, Loader2, ArrowLeft, CheckCircle } from 'lucide-react';
import HouseSelector from './HouseSelector';

// Login steps
const STEP = {
  PHONE: 'phone',
  OTP: 'otp',
  HOUSE: 'house',
  SUCCESS: 'success'
};

export default function ResidentLogin() {
  const navigate = useNavigate();
  const { setResidentUser } = useAuth();
  
  // Resident-specific state (NOT shared with admin)
  const [step, setStep] = useState(STEP.PHONE);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);
  
  // Format phone for display
  const formatPhone = (p) => {
    const cleaned = p.replace(/\D/g, '');
    if (cleaned.length <= 3) return cleaned;
    if (cleaned.length <= 6) return `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
  };
  
  // Handle phone input
  const handlePhoneChange = (e) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 10);
    setPhone(value);
    setError('');
  };
  
  // Handle OTP input
  const handleOtpChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    setError('');
    
    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };
  
  // Handle OTP paste
  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      setOtp(pasted.split(''));
    }
  };
  
  // Handle OTP backspace
  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      prevInput?.focus();
    }
  };
  
  // Start countdown timer for resend OTP
  const startCountdown = () => {
    setCountdown(60);
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };
  
  // Step 1: Request OTP
  const handleRequestOtp = async (e) => {
    e.preventDefault();
    
    if (phone.length !== 10) {
      setError('กรุณากรอกเบอร์โทรศัพท์ 10 หลัก');
      return;
    }
    
    setLoading(true);
    setError('');
    
    console.log('📱 Requesting OTP for phone:', phone); // Debug log
    
    try {
      const response = await api.post('/api/resident/login/request-otp', { phone });
      console.log('✅ OTP Response:', response.data); // Debug log
      setStep(STEP.OTP);
      startCountdown();
    } catch (err) {
      console.error('❌ OTP Error:', err.response?.data); // Debug log
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object') {
        setError(detail.message || 'ไม่พบเบอร์โทรศัพท์นี้ในระบบ');
      } else {
        setError(detail || 'ไม่พบเบอร์โทรศัพท์นี้ในระบบ');
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Step 2: Verify OTP
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    
    const otpCode = otp.join('');
    if (otpCode.length !== 6) {
      setError('กรุณากรอกรหัส OTP 6 หลัก');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/api/resident/login/verify-otp', {
        phone,
        otp: otpCode  // Backend expects 'otp' not 'otp_code'
      });
      
      const data = response.data;
      const memberships = data.memberships || [];
      
      // Small delay to ensure cookies are processed by browser
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Check memberships to determine next step
      if (memberships.length === 0) {
        // No house assigned - show error
        setError('ไม่พบบ้านที่ลงทะเบียน กรุณาติดต่อผู้ดูแลระบบเพื่อเพิ่มเบอร์โทรของท่านในระบบ');
      } else if (memberships.length === 1) {
        // Single house - auto select
        await handleSelectHouse(memberships[0].house_id);
      } else {
        // Multiple houses - show selector
        setHouses(memberships);
        setStep(STEP.HOUSE);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object') {
        if (detail.error_code === 'INVALID_OTP') {
          setError('รหัส OTP ไม่ถูกต้อง');
        } else if (detail.error_code === 'OTP_EXPIRED') {
          setError('รหัส OTP หมดอายุ กรุณาขอรหัสใหม่');
        } else {
          setError(detail.message || 'เกิดข้อผิดพลาด กรุณาลองใหม่');
        }
      } else {
        setError(detail || 'รหัส OTP ไม่ถูกต้อง');
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Step 3: Select House
  const handleSelectHouse = async (houseId) => {
    setLoading(true);
    setError('');
    
    try {
      const selectResponse = await api.post('/api/resident/select-house', { house_id: houseId });
      const selectData = selectResponse.data;
      
      // Get user info from /api/resident/me to populate context
      const meResponse = await api.get('/api/resident/me');
      const meData = meResponse.data;
      const membership = meData.memberships?.find(m => m.house_id === houseId) || meData.memberships?.[0];
      
      // Set user directly in AuthContext (no race condition)
      setResidentUser({
        id: meData.user_id,
        phone: meData.phone,
        role: 'resident',
        house_id: membership?.house_id || houseId,
        house_code: membership?.house_code || selectData.house_code,
        is_active: true,
      });
      
      setStep(STEP.SUCCESS);
      // Navigate after state is set synchronously
      setTimeout(() => navigate('/resident/dashboard', { replace: true }), 500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'object' ? detail.message : detail || 'เกิดข้อผิดพลาด');
    } finally {
      setLoading(false);
    }
  };
  
  // Resend OTP
  const handleResendOtp = async () => {
    if (countdown > 0) return;
    
    setLoading(true);
    setError('');
    
    try {
      await api.post('/api/resident/login/request-otp', { phone });
      setOtp(['', '', '', '', '', '']);
      startCountdown();
    } catch (err) {
      setError('ไม่สามารถส่ง OTP ได้ กรุณาลองใหม่');
    } finally {
      setLoading(false);
    }
  };
  
  // Go back to phone step
  const handleBack = () => {
    setStep(STEP.PHONE);
    setOtp(['', '', '', '', '', '']);
    setError('');
    setCountdown(0);
  };
  
  // Render phone input step
  const renderPhoneStep = () => (
    <form onSubmit={handleRequestOtp} className="space-y-6">
      <div>
        <label className="block text-sm text-gray-400 mb-2">
          เบอร์โทรศัพท์ / Phone Number
        </label>
        <div className="relative">
          <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="tel"
            value={formatPhone(phone)}
            onChange={handlePhoneChange}
            placeholder="08X-XXX-XXXX"
            className="w-full bg-gray-700 border border-gray-600 rounded-lg py-3 pl-10 pr-4 text-white placeholder-gray-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            autoFocus
            disabled={loading}
          />
        </div>
      </div>
      
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}
      
      <button
        type="submit"
        disabled={loading || phone.length !== 10}
        className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="animate-spin" size={20} />
            กำลังส่ง OTP...
          </>
        ) : (
          'ขอรหัส OTP'
        )}
      </button>
      
      <p className="text-center text-gray-500 text-sm">
        ระบบจะส่งรหัส OTP ไปยังเบอร์โทรศัพท์ที่ลงทะเบียนไว้
      </p>
    </form>
  );
  
  // Render OTP input step
  const renderOtpStep = () => (
    <form onSubmit={handleVerifyOtp} className="space-y-6">
      <button
        type="button"
        onClick={handleBack}
        className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft size={18} />
        <span>กลับ</span>
      </button>
      
      <div className="text-center">
        <KeyRound className="mx-auto text-emerald-500 mb-2" size={32} />
        <p className="text-gray-300">กรอกรหัส OTP ที่ส่งไปยัง</p>
        <p className="text-white font-medium">{formatPhone(phone)}</p>
      </div>
      
      <div className="flex justify-center gap-2">
        {otp.map((digit, index) => (
          <input
            key={index}
            id={`otp-${index}`}
            type="text"
            inputMode="numeric"
            value={digit}
            onChange={(e) => handleOtpChange(index, e.target.value)}
            onKeyDown={(e) => handleOtpKeyDown(index, e)}
            onPaste={index === 0 ? handleOtpPaste : undefined}
            className="w-12 h-14 bg-gray-700 border border-gray-600 rounded-lg text-center text-xl text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            maxLength={1}
            disabled={loading}
            autoFocus={index === 0}
          />
        ))}
      </div>
      
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm text-center">
          {error}
        </div>
      )}
      
      <button
        type="submit"
        disabled={loading || otp.join('').length !== 6}
        className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="animate-spin" size={20} />
            กำลังตรวจสอบ...
          </>
        ) : (
          'ยืนยัน'
        )}
      </button>
      
      <div className="text-center">
        {countdown > 0 ? (
          <p className="text-gray-500 text-sm">
            ขอรหัสใหม่ได้ใน {countdown} วินาที
          </p>
        ) : (
          <button
            type="button"
            onClick={handleResendOtp}
            disabled={loading}
            className="text-emerald-500 hover:text-emerald-400 text-sm transition-colors"
          >
            ขอรหัส OTP ใหม่
          </button>
        )}
      </div>
      
      {/* Mock mode hint */}
      <p className="text-center text-gray-600 text-xs">
        [Dev Mode] OTP: 123456
      </p>
    </form>
  );
  
  // Render house selection step
  const renderHouseStep = () => (
    <div className="space-y-4">
      <button
        type="button"
        onClick={handleBack}
        className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft size={18} />
        <span>กลับ</span>
      </button>
      
      <HouseSelector
        houses={houses}
        onSelect={handleSelectHouse}
        loading={loading}
        error={error}
      />
    </div>
  );
  
  // Render success step
  const renderSuccessStep = () => (
    <div className="text-center space-y-4 py-8">
      <CheckCircle className="mx-auto text-emerald-500" size={64} />
      <h3 className="text-xl text-white font-medium">เข้าสู่ระบบสำเร็จ!</h3>
      <p className="text-gray-400">กำลังนำท่านไปยังหน้าหลัก...</p>
      <Loader2 className="mx-auto animate-spin text-emerald-500" size={24} />
    </div>
  );
  
  return (
    <div className="flex-1 bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Building2 className="text-white" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white">Moobaan Smart</h1>
          <p className="text-gray-400 mt-1">ระบบบริหารหมู่บ้านจัดสรร</p>
        </div>
        
        {/* Login Card */}
        <div className="bg-gray-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-lg font-semibold text-white mb-6">
            {step === STEP.PHONE && 'เข้าสู่ระบบ / Login'}
            {step === STEP.OTP && 'ยืนยันรหัส OTP'}
            {step === STEP.HOUSE && 'เลือกบ้าน'}
            {step === STEP.SUCCESS && ''}
          </h2>
          
          {step === STEP.PHONE && renderPhoneStep()}
          {step === STEP.OTP && renderOtpStep()}
          {step === STEP.HOUSE && renderHouseStep()}
          {step === STEP.SUCCESS && renderSuccessStep()}
        </div>
      </div>
    </div>
  );
}
