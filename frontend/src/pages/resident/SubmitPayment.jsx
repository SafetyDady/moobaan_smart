/**
 * @deprecated This Desktop SubmitPayment is no longer used.
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Section 2.1:
 * "Resident Desktop UI is intentionally removed by design."
 * 
 * All Resident users now see MobileSubmitPayment regardless of device.
 * This file is kept for reference but is not rendered.
 * 
 * See: frontend/src/pages/resident/ResidentRouteWrapper.jsx
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AlertTriangle, MessageCircle, FileText, Paperclip, Check, Loader2, CheckCircle } from 'lucide-react';
import { payinsAPI, api } from '../../api/client';
import { useToast } from '../../components/Toast';
import { useRole } from '../../contexts/RoleContext';

export default function SubmitPayment() {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentHouseId, currentHouseCode } = useRole();
  const toast = useToast();
  const editPayin = location.state?.editPayin;

  const [formData, setFormData] = useState({
    amount: editPayin?.amount || '',
    transfer_date: editPayin?.transfer_date || '',
    transfer_hour: editPayin?.transfer_hour || '',
    transfer_minute: editPayin?.transfer_minute || '',
    slip_image_url: editPayin?.slip_image_url || '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [slipFile, setSlipFile] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('🚀🚀🚀 handleSubmit CALLED - form submitted!');
    
    // Early validation - before any async operations
    try {
      console.log('🔍 DEBUG - currentHouseId:', currentHouseId, 'Type:', typeof currentHouseId);
      console.log('🔍 DEBUG - formData:', formData);
      console.log('🔍 DEBUG - slipFile:', slipFile);
      console.log('🔍 DEBUG - editPayin:', editPayin);
      
      // Validate slip is attached FIRST (most common error)
      if (!slipFile && !editPayin?.slip_url) {
        console.log('❌ VALIDATION FAILED: No slip attached');
        toast.warning('กรุณาแนบสลิปการโอนเงิน');
        return;
      }
      
      // Validate all required fields
      if (!formData.amount || !formData.transfer_date || formData.transfer_hour === '' || formData.transfer_minute === '') {
        console.log('❌ VALIDATION FAILED: Missing required fields');
        toast.warning('กรุณากรอกข้อมูลให้ครบถ้วน');
        return;
      }

      // Validate amount is a positive finite number (parseFloat('') === NaN)
      const amountNum = parseFloat(formData.amount);
      if (!Number.isFinite(amountNum) || amountNum <= 0) {
        toast.warning('กรุณากรอกจำนวนเงินที่ถูกต้อง (มากกว่า 0)');
        return;
      }
      
      console.log('✅ VALIDATION PASSED');
    } catch (validationError) {
      console.error('Validation error:', validationError);
      toast.error('เกิดข้อผิดพลาดในการตรวจสอบข้อมูล');
      return;
    }
    
    // Validate house ID from context
    if (!currentHouseId) {
      console.error('❌ No house_id found in RoleContext');
      
      // Try to get user data directly from API
      try {
        const response = await api.get('/api/auth/me');
        const userData = response.data;
        console.log('🔍 Direct API check - userData:', userData);
        
        if (!userData.house_id) {
          toast.error('ไม่พบข้อมูลบ้าน: บัญชีของคุณยังไม่ได้เชื่อมโยงกับบ้าน กรุณาติดต่อแอดมิน');
          return;
        }
      } catch (error) {
        console.error('❌ Failed to fetch user data:', error);
        toast.error('ไม่พบข้อมูลบ้าน กรุณาเข้าสู่ระบบใหม่อีกครั้ง');
        navigate('/auth/login');
        return;
      }
    }
    
    // Validate hour and minute ranges
    const hour = parseInt(formData.transfer_hour);
    const minute = parseInt(formData.transfer_minute);
    if (isNaN(hour) || isNaN(minute) || hour < 0 || hour > 23 || minute < 0 || minute > 59) {
      toast.warning('เวลาไม่ถูกต้อง (ชั่วโมง: 0-23, นาที: 0-59)');
      return;
    }
    
    setSubmitting(true);

    try {
      // Create FormData for multipart/form-data submission
      const submitFormData = new FormData();
      
      // Create ISO datetime from date + time (local timezone)
      const paidAtDate = new Date(formData.transfer_date);
      paidAtDate.setHours(hour, minute, 0, 0);
      
      // Format as ISO string but preserve local time (don't convert to UTC)
      const year = paidAtDate.getFullYear();
      const month = String(paidAtDate.getMonth() + 1).padStart(2, '0');
      const day = String(paidAtDate.getDate()).padStart(2, '0');
      const hourStr = String(paidAtDate.getHours()).padStart(2, '0');
      const minuteStr = String(paidAtDate.getMinutes()).padStart(2, '0');
      const paidAtISO = `${year}-${month}-${day}T${hourStr}:${minuteStr}:00`;
      
      submitFormData.append('amount', parseFloat(formData.amount));
      submitFormData.append('paid_at', paidAtISO);
      
      if (slipFile) {
        submitFormData.append('slip', slipFile);
      }

      console.log('📤 Submitting FormData fields:', {
        amount: submitFormData.get('amount'),
        paid_at: submitFormData.get('paid_at'),
        hour: hourStr,
        minute: minuteStr,
        slip: slipFile ? slipFile.name : 'none'
      });

      if (editPayin) {
        // For edit: upload new slip first if changed, then update payin
        let slipUrl = undefined; // undefined = don't update slip_url
        if (slipFile) {
          const uploadRes = await payinsAPI.uploadSlip(slipFile, currentHouseId);
          slipUrl = uploadRes.data.slip_url;
        }
        const jsonData = {
          amount: parseFloat(formData.amount),
          transfer_date: formData.transfer_date,
          transfer_hour: hour,
          transfer_minute: minute,
        };
        if (slipUrl !== undefined) {
          jsonData.slip_image_url = slipUrl;
        }
        await payinsAPI.update(editPayin.id, jsonData);
        toast.success('แก้ไขและส่งรายงานการชำระเงินเรียบร้อยแล้ว');
      } else {
        // For create, use FormData
        const response = await payinsAPI.createFormData(submitFormData);
        console.log('✅ Success response:', response);
        toast.success('ส่งรายงานการชำระเงินเรียบร้อยแล้ว');
      }
      
      // Use navigate to avoid losing auth state
      navigate('/resident/dashboard');
    } catch (error) {
      console.error('❌ Failed to submit:', error);
      console.error('❌ Error status:', error.response?.status);
      console.error('❌ Error response:', error.response);
      console.error('❌ Error data:', JSON.stringify(error.response?.data, null, 2));
      console.error('❌ Error detail:', error.response?.data?.detail);
      
      // Handle 409 duplicate submission gracefully
      if (error.response?.status === 409) {
        const errorData = error.response?.data;
        if (errorData?.detail?.code === 'PAYIN_PENDING_EXISTS') {
          const msg = errorData.detail.message || 'มีรายการรอตรวจสอบอยู่แล้ว กรุณารอสักครู่ก่อนส่งใหม่';
          toast.warning(msg);
          setSubmitting(false);
          return;
        }
      }
      
      // Show detailed error
      let errorMsg = 'ไม่สามารถส่งรายงานการชำระเงินได้';
      const errorData = error.response?.data;
      
      if (errorData?.detail) {
        if (Array.isArray(errorData.detail)) {
          // FastAPI/Pydantic validation errors
          const errors = errorData.detail.map(e => {
            const field = Array.isArray(e.loc) ? e.loc.join('.') : String(e.loc || 'field');
            const msg = e.msg || String(e);
            return `• ${field}: ${msg}`;
          }).join('\n');
          errorMsg = `ข้อมูลไม่ถูกต้อง:\n\n${errors}`;
        } else if (typeof errorData.detail === 'string') {
          errorMsg = errorData.detail;
        } else if (typeof errorData.detail === 'object') {
          // Handle object detail - extract meaningful message
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
      
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          {editPayin ? 'แก้ไขข้อมูลการชำระเงิน' : 'ส่งสลิปการชำระเงิน'}
        </h1>
        <p className="text-gray-400">
          บ้านเลขที่ {currentHouseCode || `#${currentHouseId}`} - อัพโหลดข้อมูลการชำระเงิน
        </p>
        {editPayin && editPayin.status === 'REJECTED' && (
          <div className="mt-4 p-4 bg-yellow-900 bg-opacity-30 border border-yellow-600 rounded-lg">
            <p className="text-yellow-300 text-sm">
              <strong>เหตุผลที่ปฏิเสธ:</strong> {editPayin.reject_reason}
            </p>
          </div>
        )}
        {editPayin && editPayin.status === 'REJECTED_NEEDS_FIX' && (
          <div className="mt-4 p-4 bg-red-900 bg-opacity-30 border border-red-600 rounded-lg">
            <p className="text-red-300 text-sm font-medium mb-2">
              <AlertTriangle size={14} className="inline mr-1" />ต้องแก้ไขข้อมูล
            </p>
            {editPayin.reject_reason && (
              <p className="text-red-200 text-sm">
                <strong>เหตุผล:</strong> {editPayin.reject_reason}
              </p>
            )}
            {editPayin.admin_note && (
              <p className="text-yellow-300 text-sm mt-2">
                <MessageCircle size={14} className="inline mr-1" /><strong>หมายเหตุจากแอดมิน:</strong> {editPayin.admin_note}
              </p>
            )}
          </div>
        )}
        {editPayin && editPayin.status === 'DRAFT' && (
          <div className="mt-4 p-4 bg-gray-800 bg-opacity-50 border border-gray-600 rounded-lg">
            <p className="text-gray-300 text-sm">
              <FileText size={14} className="inline mr-1" />แก้ไขร่างการชำระเงิน - ยังไม่ได้ส่งเข้าระบบ
            </p>
          </div>
        )}
        {editPayin && editPayin.status === 'PENDING' && (
          <div className="mt-4 p-4 bg-blue-900 bg-opacity-30 border border-blue-600 rounded-lg">
            <p className="text-blue-300 text-sm">
              <FileText size={14} className="inline mr-1" />กำลังแก้ไขรายการที่รอตรวจสอบ - คุณสามารถปรับปรุงข้อมูลได้
            </p>
          </div>
        )}
      </div>

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit} className="card p-6 space-y-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Amount (฿) *
            </label>
            <input
              type="number"
              required
              step="0.01"
              min="1"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="input w-full"
              placeholder="3000.00"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Transfer Date *
            </label>
            <input
              type="date"
              required
              value={formData.transfer_date}
              onChange={(e) => setFormData({ ...formData, transfer_date: e.target.value })}
              className="input w-full"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Transfer Hour (HH) *
              </label>
              <input
                type="number"
                required
                min="0"
                max="23"
                value={formData.transfer_hour}
                onChange={(e) => setFormData({ ...formData, transfer_hour: e.target.value })}
                className="input w-full"
                placeholder="14"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Transfer Minute (MM) *
              </label>
              <input
                type="number"
                required
                min="0"
                max="59"
                value={formData.transfer_minute}
                onChange={(e) => setFormData({ ...formData, transfer_minute: e.target.value })}
                className="input w-full"
                placeholder="30"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">
              แนบสลิปการโอนเงิน *
            </label>
            <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
              <div className="mb-2"><Paperclip size={36} className="text-gray-500 mx-auto" /></div>
              <p className="text-gray-400 text-sm mb-2">
                แนบรูปสลิปการโอนเงิน (บังคับ)
              </p>
              <input
                type="file"
                accept="image/*"
                required={!editPayin}
                onChange={(e) => {
                  const file = e.target.files[0];
                  if (file) {
                    setSlipFile(file);
                  }
                }}
                className="hidden"
                id="slip-upload"
              />
              <label htmlFor="slip-upload" className="btn-secondary cursor-pointer inline-block">
                เลือกไฟล์
              </label>
              {slipFile && (
                <p className="text-primary-400 text-sm mt-2">
                  <Check size={14} className="inline mr-1" />เลือกไฟล์แล้ว: {slipFile.name}
                </p>
              )}
              {formData.slip_image_url && !slipFile && (
                <p className="text-primary-400 text-sm mt-2">
                  <Check size={14} className="inline mr-1" />มีไฟล์แนบอยู่แล้ว
                </p>
              )}
            </div>
            <p className="text-xs text-red-400 mt-2">
              * ต้องแนบสลิปการโอนเงิน (Note: File upload is mocked in Phase 1)
            </p>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary flex-1 disabled:bg-gray-600 disabled:cursor-not-allowed"
            >
              {submitting ? <><Loader2 size={16} className="inline mr-1 animate-spin" />กำลังส่ง...</> : (editPayin ? <><CheckCircle size={16} className="inline mr-1" />แก้ไขและส่งใหม่</> : <><CheckCircle size={16} className="inline mr-1" />ส่งสลิป</>)}
            </button>
            <button
              type="button"
              onClick={() => navigate('/resident/dashboard')}
              disabled={submitting}
              className="btn-secondary flex-1 disabled:bg-gray-700 disabled:cursor-not-allowed"
            >
              ยกเลิก
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
