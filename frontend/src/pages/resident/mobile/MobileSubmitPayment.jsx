import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { payinsAPI } from '../../../api/client';
import { useRole } from '../../../contexts/RoleContext';
import { isIOS } from '../../../utils/deviceDetect';
import MobileLayout from './MobileLayout';

export default function MobileSubmitPayment() {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentHouseId } = useRole();
  const editPayin = location.state?.editPayin;

  const [formData, setFormData] = useState({
    amount: editPayin?.amount || '',
    transfer_date: editPayin?.transfer_date || '',
    transfer_time: editPayin ? `${String(editPayin.transfer_hour).padStart(2, '0')}:${String(editPayin.transfer_minute).padStart(2, '0')}` : '',
    slip_image: null,
    slip_preview: editPayin?.slip_image_url || null,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [keyboardOpen, setKeyboardOpen] = useState(false);

  // File size limit: 8MB
  const MAX_FILE_SIZE = 8 * 1024 * 1024;

  // Handle iOS keyboard overlap
  useEffect(() => {
    if (!isIOS()) return;

    const handleResize = () => {
      // On iOS, when keyboard opens, visualViewport.height < window.innerHeight
      if (window.visualViewport) {
        const isOpen = window.visualViewport.height < window.innerHeight * 0.75;
        setKeyboardOpen(isOpen);
      }
    };

    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleResize);
      return () => window.visualViewport.removeEventListener('resize', handleResize);
    }
  }, []);

  const handleCameraCapture = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Clear previous error
    setError(null);

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('กรุณาเลือกไฟล์รูปภาพเท่านั้น');
      return;
    }

    // Validate file size (max 8MB)
    if (file.size > MAX_FILE_SIZE) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
      setError(`ไฟล์ใหญ่เกินไป (${sizeMB}MB) กรุณาเลือกไฟล์ที่เล็กกว่า 8MB`);
      return;
    }

    // Create preview URL
    const previewUrl = URL.createObjectURL(file);
    setFormData({ 
      ...formData, 
      slip_image: file,
      slip_preview: previewUrl
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Validate house ID
      if (!currentHouseId) {
        setError('ไม่พบข้อมูลบ้าน กรุณาเข้าสู่ระบบใหม่อีกครั้ง');
        navigate('/auth/login');
        return;
      }

      // Validate slip image for CREATE
      if (!editPayin && !formData.slip_image) {
        setError('กรุณาถ่ายรูปสลิปก่อนส่ง');
        setSubmitting(false);
        return;
      }

      // Parse time and build ISO datetime
      const [hour, minute] = formData.transfer_time.split(':');
      const paidAtDate = new Date(formData.transfer_date);
      paidAtDate.setHours(parseInt(hour), parseInt(minute), 0, 0);
      const paidAtISO = paidAtDate.toISOString();

      console.log('📱 Mobile - Building FormData:', {
        amount: formData.amount,
        paid_at: paidAtISO,
        slip: formData.slip_image?.name || 'none'
      });

      if (editPayin) {
        // For edit, use JSON (legacy behavior for Phase 1)
        const jsonData = {
          amount: parseFloat(formData.amount),
          transfer_date: formData.transfer_date,
          transfer_hour: parseInt(hour),
          transfer_minute: parseInt(minute),
          slip_image_url: formData.slip_preview || 'https://example.com/slips/updated.jpg'
        };
        await payinsAPI.update(editPayin.id, jsonData);
        alert('✅ แก้ไขและส่งสลิปใหม่เรียบร้อยแล้ว');
      } else {
        // For create, use FormData (same as Desktop)
        const submitFormData = new FormData();
        submitFormData.append('amount', parseFloat(formData.amount));
        submitFormData.append('paid_at', paidAtISO);
        submitFormData.append('note', `Mobile submit at ${hour}:${minute}`);
        
        if (formData.slip_image) {
          submitFormData.append('slip', formData.slip_image);
        }

        console.log('📤 Mobile - Sending FormData');
        await payinsAPI.createFormData(submitFormData);
        alert('✅ ส่งสลิปเรียบร้อยแล้ว');
      }
      
      navigate('/resident/dashboard');
    } catch (error) {
      console.error('❌ Mobile submit failed:', error);
      console.error('❌ Error response:', error.response?.data);
      
      // Extract error message properly
      let errorMsg = 'ส่งสลิปไม่สำเร็จ กรุณาลองใหม่';
      const errorData = error.response?.data;
      
      if (errorData?.detail) {
        if (Array.isArray(errorData.detail)) {
          // FastAPI validation errors
          const errors = errorData.detail.map(e => {
            const field = Array.isArray(e.loc) ? e.loc.join('.') : String(e.loc || 'field');
            const msg = e.msg || String(e);
            return `• ${field}: ${msg}`;
          }).join('\n');
          errorMsg = `ข้อมูลไม่ถูกต้อง:\n\n${errors}`;
        } else if (typeof errorData.detail === 'string') {
          errorMsg = errorData.detail;
        } else if (typeof errorData.detail === 'object') {
          const detailStr = Object.entries(errorData.detail)
            .map(([key, val]) => `${key}: ${String(val)}`)
            .join('\n');
          errorMsg = `Error details:\n${detailStr}`;
        }
      } else if (errorData?.message) {
        errorMsg = errorData.message;
      } else if (error.message) {
        errorMsg = `Error: ${error.message}`;
      }
      
      setError(errorMsg);
      alert('❌ ' + errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <MobileLayout>
      <div className={`p-4 ${keyboardOpen ? 'pb-96' : ''}`}>
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-2">
            {editPayin ? '✏️ แก้ไขและส่งใหม่' : '💳 ส่งสลิปการชำระเงิน'}
          </h1>
          <p className="text-sm text-gray-400">
            บ้านเลขที่ #{currentHouseId}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-900 bg-opacity-30 border border-red-600 rounded-lg p-4">
            <p className="text-sm text-red-300">
              <strong>⚠️ ข้อผิดพลาด:</strong>
            </p>
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Rejection Notice */}
        {editPayin && editPayin.reject_reason && (
          <div className="mb-6 bg-red-900 bg-opacity-30 border border-red-600 rounded-lg p-4">
            <p className="text-sm text-red-300 mb-1">
              <strong>⚠️ เหตุผลที่ถูกปฏิเสธ:</strong>
            </p>
            <p className="text-red-200">{editPayin.reject_reason}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              จำนวนเงิน (บาท) *
            </label>
            <input
              type="number"
              inputMode="decimal"
              step="0.01"
              min="0"
              required
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-4 text-white text-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="3,000.00"
            />
          </div>

          {/* Transfer Date */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              วันที่โอน *
            </label>
            <input
              type="date"
              required
              value={formData.transfer_date}
              onChange={(e) => setFormData({ ...formData, transfer_date: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-4 text-white text-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Transfer Time */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              เวลาที่โอน *
            </label>
            <input
              type="time"
              required
              value={formData.transfer_time}
              onChange={(e) => setFormData({ ...formData, transfer_time: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-4 text-white text-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Camera Capture */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              ถ่ายรูปสลิป
            </label>
            <div className="relative">
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleCameraCapture}
                className="hidden"
                id="camera-input"
              />
              
              {formData.slip_preview ? (
                // Preview
                <div className="relative">
                  <img 
                    src={formData.slip_preview} 
                    alt="Slip preview"
                    className="w-full rounded-lg border-2 border-gray-700"
                  />
                  <label
                    htmlFor="camera-input"
                    className="absolute bottom-4 right-4 bg-primary-600 text-white px-4 py-2 rounded-lg shadow-lg cursor-pointer active:bg-primary-700 flex items-center gap-2"
                  >
                    <span>📸</span>
                    <span className="font-medium">ถ่ายใหม่</span>
                  </label>
                </div>
              ) : (
                // Upload Button
                <label
                  htmlFor="camera-input"
                  className="block w-full bg-gray-800 border-2 border-dashed border-gray-600 rounded-lg p-12 text-center cursor-pointer active:bg-gray-750 transition-colors"
                >
                  <div className="text-5xl mb-3">📸</div>
                  <p className="text-white font-medium text-lg mb-1">ถ่ายรูปสลิป</p>
                  <p className="text-sm text-gray-400">แตะเพื่อเปิดกล้อง</p>
                </label>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              💡 เคล็ดลับ: ถ่ายให้เห็นรายละเอียดชัดเจน
            </p>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-primary-600 hover:bg-primary-700 active:bg-primary-800 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-lg text-lg transition-colors"
          >
            {submitting ? (
              <span>⏳ กำลังส่ง...</span>
            ) : editPayin ? (
              <span>✅ แก้ไขและส่งใหม่</span>
            ) : (
              <span>✅ ส่งสลิปเลย</span>
            )}
          </button>

          {/* Cancel Button */}
          <button
            type="button"
            onClick={() => navigate('/resident/dashboard')}
            disabled={submitting}
            className="w-full bg-gray-700 hover:bg-gray-600 active:bg-gray-600 disabled:bg-gray-800 text-white font-medium py-4 rounded-lg text-lg transition-colors"
          >
            ยกเลิก
          </button>
        </form>

        {/* Help Text */}
        <div className="mt-6 bg-blue-900 bg-opacity-20 border border-blue-700 rounded-lg p-4">
          <p className="text-sm text-blue-300">
            <strong>📝 หมายเหตุ:</strong> การอัปโหลดไฟล์เป็นแบบจำลองใน Phase 1 
            ในระบบจริงจะบันทึกรูปภาพลงในระบบ
          </p>
        </div>
      </div>
    </MobileLayout>
  );
}
