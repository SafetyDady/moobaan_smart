import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import DatePicker from 'react-datepicker';
import { subDays, startOfDay } from 'date-fns';
import { th } from 'date-fns/locale';
import 'react-datepicker/dist/react-datepicker.css';
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
    transfer_date: editPayin?.transfer_date ? new Date(editPayin.transfer_date) : null, // Date object for DatePicker
    transfer_hour: editPayin?.transfer_hour !== undefined ? String(editPayin.transfer_hour).padStart(2, '0') : '',
    transfer_minute: editPayin?.transfer_minute !== undefined ? String(editPayin.transfer_minute).padStart(2, '0') : '',
    slip_image: null,
    slip_preview: editPayin?.slip_image_url || null,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // File size limit: 8MB
  const MAX_FILE_SIZE = 8 * 1024 * 1024;

  // Date range: 90 days back from today
  const today = startOfDay(new Date());
  const minDate = subDays(today, 90);
  const maxDate = today;

  const handleCameraCapture = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError(null);

    if (!file.type.startsWith('image/')) {
      setError('กรุณาเลือกไฟล์รูปภาพเท่านั้น');
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
      setError(`ไฟล์ใหญ่เกินไป (${sizeMB}MB) กรุณาเลือกไฟล์ที่เล็กกว่า 8MB`);
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    setFormData({ 
      ...formData, 
      slip_image: file,
      slip_preview: previewUrl
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setSubmitting(true);
    setError(null);

    try {
      // Validate slip image FIRST for CREATE
      if (!editPayin && !formData.slip_image) {
        setError('❌ กรุณาแนบสลิปก่อนส่ง');
        setSubmitting(false);
        return;
      }

      // Validate house ID
      if (!currentHouseId) {
        setError('ไม่พบข้อมูลบ้าน กรุณาเข้าสู่ระบบใหม่อีกครั้ง');
        setSubmitting(false);
        return;
      }

      // Validate date
      if (!formData.transfer_date) {
        setError('กรุณาเลือกวันที่โอน');
        setSubmitting(false);
        return;
      }

      // Validate hour and minute
      const hour = parseInt(formData.transfer_hour);
      const minute = parseInt(formData.transfer_minute);

      if (isNaN(hour) || hour < 0 || hour > 23) {
        setError('กรุณากรอกชั่วโมงให้ถูกต้อง (00-23)');
        setSubmitting(false);
        return;
      }

      if (isNaN(minute) || minute < 0 || minute > 59) {
        setError('กรุณากรอกนาทีให้ถูกต้อง (00-59)');
        setSubmitting(false);
        return;
      }

      // Build ISO datetime (local timezone)
      const paidAtDate = new Date(formData.transfer_date);
      paidAtDate.setHours(hour, minute, 0, 0);
      
      // Format as ISO string but remove 'Z' to preserve local time
      const year = paidAtDate.getFullYear();
      const month = String(paidAtDate.getMonth() + 1).padStart(2, '0');
      const day = String(paidAtDate.getDate()).padStart(2, '0');
      const hourStr = String(paidAtDate.getHours()).padStart(2, '0');
      const minuteStr = String(paidAtDate.getMinutes()).padStart(2, '0');
      const paidAtISO = `${year}-${month}-${day}T${hourStr}:${minuteStr}:00`;

      if (editPayin) {
        // For edit, use JSON (legacy behavior)
        const jsonData = {
          amount: parseFloat(formData.amount),
          transfer_date: `${year}-${month}-${day}`,
          transfer_hour: hour,
          transfer_minute: minute,
          slip_image_url: formData.slip_preview || 'https://example.com/slips/updated.jpg'
        };
        await payinsAPI.update(editPayin.id, jsonData);
        alert('✅ แก้ไขและส่งสลิปใหม่เรียบร้อยแล้ว');
      } else {
        // For create, use FormData
        const submitFormData = new FormData();
        submitFormData.append('amount', parseFloat(formData.amount));
        submitFormData.append('paid_at', paidAtISO);
        
        if (formData.slip_image) {
          submitFormData.append('slip', formData.slip_image);
        }

        const response = await payinsAPI.createFormData(submitFormData);
        alert('✅ ส่งสลิปเรียบร้อยแล้ว');
        navigate('/resident/dashboard');
        return;
      }
      
      navigate('/resident/dashboard');
    } catch (error) {
      console.error('❌ Mobile submit failed:', error);
      console.error('Error response:', error.response?.data);
      
      // Handle 409 - pay-in already exists
      if (error.response?.status === 409) {
        const errorData = error.response?.data;
        const detail = errorData?.detail;
        
        // Check for PAYIN_ALREADY_OPEN code
        if (detail?.code === 'PAYIN_ALREADY_OPEN' || 
            detail?.code === 'INCOMPLETE_PAYIN_EXISTS' || 
            detail?.code === 'PAYIN_PENDING_EXISTS') {
          const existingStatus = detail.existing_status || '';
          let statusText = '';
          switch(existingStatus) {
            case 'PENDING': statusText = '(รอตรวจสอบ)'; break;
            case 'DRAFT': statusText = '(แบบร่าง)'; break;
            case 'REJECTED_NEEDS_FIX': statusText = '(ถูกปฏิเสธ-รอแก้ไข)'; break;
            case 'SUBMITTED': statusText = '(ส่งแล้ว)'; break;
            default: statusText = '';
          }
          const msg = `⚠️ คุณมีรายการส่งสลิปค้างอยู่ ${statusText}\n\nกรุณากลับไปดำเนินการรายการเดิมให้เสร็จก่อน หรือลบรายการเดิมออก`;
          setError(msg);
          setSubmitting(false);
          return;
        }
        
        // Generic 409 message
        const msg = detail?.message || 'มีรายการค้างอยู่ กรุณาตรวจสอบ';
        setError(`⚠️ ${msg}`);
        setSubmitting(false);
        return;
      }
      
      // Handle network error
      if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        setError('❌ เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต');
        setSubmitting(false);
        return;
      }
      
      // Extract error message
      let errorMsg = 'ส่งสลิปไม่สำเร็จ กรุณาลองใหม่';
      const errorData = error.response?.data;
      
      if (errorData?.detail) {
        if (Array.isArray(errorData.detail)) {
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
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <MobileLayout>
      <div className="p-4 pb-24">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-1">
            {editPayin ? '✏️ แก้ไขและส่งใหม่' : '💳 ส่งสลิปการชำระเงิน'}
          </h1>
          <p className="text-sm text-gray-400">
            บ้านเลขที่ #{currentHouseId}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 bg-red-900/30 border border-red-600 rounded-lg p-3">
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {/* Rejection Notice */}
        {editPayin && editPayin.status === 'REJECTED' && editPayin.reject_reason && (
          <div className="mb-4 bg-red-900/30 border border-red-600 rounded-lg p-3">
            <p className="text-xs text-red-300 mb-1">
              <strong>⚠️ เหตุผลที่ถูกปฏิเสธ:</strong>
            </p>
            <p className="text-sm text-red-200">{editPayin.reject_reason}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
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
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-4 text-white text-xl font-semibold focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="0.00"
            />
          </div>

          {/* Transfer Date (Custom Calendar) */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              วันที่โอน *
            </label>
            <DatePicker
              selected={formData.transfer_date}
              onChange={(date) => setFormData({ ...formData, transfer_date: date })}
              minDate={minDate}
              maxDate={maxDate}
              dateFormat="dd/MM/yyyy"
              locale={th}
              placeholderText="เลือกวันที่"
              required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-base focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              calendarClassName="custom-calendar"
              wrapperClassName="w-full"
            />
            <p className="text-xs text-gray-500 mt-2">
              💡 เลือกได้ย้อนหลังไม่เกิน 90 วัน
            </p>
          </div>

          {/* Transfer Time (HH MM) */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              เวลาที่โอน *
            </label>
            <div className="grid grid-cols-2 gap-3">
              {/* Hour Input */}
              <div>
                <input
                  type="number"
                  inputMode="numeric"
                  min="0"
                  max="23"
                  required
                  value={formData.transfer_hour}
                  onChange={(e) => {
                    let value = e.target.value;
                    if (value.length > 2) value = value.slice(0, 2);
                    if (parseInt(value) > 23) value = '23';
                    setFormData({ ...formData, transfer_hour: value });
                  }}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-lg text-center focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="HH"
                />
                <p className="text-xs text-gray-500 mt-1 text-center">ชั่วโมง</p>
              </div>

              {/* Minute Input */}
              <div>
                <input
                  type="number"
                  inputMode="numeric"
                  min="0"
                  max="59"
                  required
                  value={formData.transfer_minute}
                  onChange={(e) => {
                    let value = e.target.value;
                    if (value.length > 2) value = value.slice(0, 2);
                    if (parseInt(value) > 59) value = '59';
                    setFormData({ ...formData, transfer_minute: value });
                  }}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-lg text-center focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="MM"
                />
                <p className="text-xs text-gray-500 mt-1 text-center">นาที</p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              💡 กรอก 00-23 และ 00-59
            </p>
          </div>

          {/* Camera Capture */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              แนบสลิป *
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
                <div className="relative">
                  <img 
                    src={formData.slip_preview} 
                    alt="Slip preview"
                    className="w-full rounded-lg border-2 border-gray-700 max-h-64 object-contain bg-gray-800"
                  />
                  <label
                    htmlFor="camera-input"
                    className="absolute bottom-3 right-3 bg-primary-600 text-white px-3 py-2 rounded-lg shadow-lg cursor-pointer active:bg-primary-700 flex items-center gap-2 text-sm"
                  >
                    <span>📸</span>
                    <span className="font-medium">เปลี่ยน</span>
                  </label>
                </div>
              ) : (
                <label
                  htmlFor="camera-input"
                  className="block w-full bg-gray-800 border-2 border-dashed border-gray-600 rounded-lg p-4 text-center cursor-pointer active:bg-gray-750 transition-colors"
                >
                  <div className="flex items-center justify-center gap-3">
                    <span className="text-3xl">📸</span>
                    <span className="text-white font-medium">แตะเพื่อถ่ายหรือเลือกรูป</span>
                  </div>
                </label>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              💡 ถ่ายให้เห็นรายละเอียดชัดเจน
            </p>
          </div>
        </form>
      </div>

      {/* Sticky Submit Button */}
      <div className="fixed bottom-16 left-0 right-0 bg-gray-900 border-t border-gray-800 p-4 z-20">
        <button
          type="submit"
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full bg-primary-600 active:bg-primary-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-lg text-lg transition-colors min-h-[56px] shadow-lg"
        >
          {submitting ? (
            <span>⏳ กำลังส่ง...</span>
          ) : editPayin ? (
            <span>✅ แก้ไขและส่งใหม่</span>
          ) : (
            <span>✅ ส่งสลิปเลย</span>
          )}
        </button>
        
        <button
          type="button"
          onClick={() => navigate('/resident/dashboard')}
          disabled={submitting}
          className="w-full text-gray-400 text-sm mt-3 underline"
        >
          ยกเลิก
        </button>
      </div>

      {/* Custom Calendar Styles */}
      <style>{`
        .custom-calendar {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }

        .react-datepicker__header {
          background: #f9fafb;
          border-bottom: 1px solid #e5e7eb;
          padding-top: 0.5rem;
        }

        .react-datepicker__current-month {
          color: #111827;
          font-weight: 600;
          font-size: 1rem;
        }

        .react-datepicker__day-name {
          color: #6b7280;
          font-weight: 500;
        }

        .react-datepicker__day {
          color: #111827;
        }

        .react-datepicker__day--selected {
          background-color: #3b82f6 !important;
          color: white !important;
        }

        .react-datepicker__day--today {
          background-color: #10b981 !important;
          color: white !important;
          font-weight: bold;
        }

        .react-datepicker__day--disabled {
          color: #d1d5db !important;
          text-decoration: line-through;
          cursor: not-allowed !important;
        }

        .react-datepicker__day:hover:not(.react-datepicker__day--disabled) {
          background-color: #e5e7eb;
        }

        .react-datepicker__navigation {
          top: 0.75rem;
        }

        .react-datepicker__navigation-icon::before {
          border-color: #6b7280;
        }
      `}</style>
    </MobileLayout>
  );
}
