/**
 * PayinDetailModal - Mobile-friendly Pay-in Detail View
 * 
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Section 9
 * 
 * Required fields:
 * - Amount
 * - Transfer date & time
 * - Status (Thai + English)
 * - Slip preview
 * - Admin rejection reason (if rejected)
 * - Source indicator (Resident / Admin-created / LINE)
 * 
 * Behavior:
 * - Detail view is always accessible
 * - Edit/Delete buttons appear only in editable states
 * - When ACCEPTED → detail becomes read-only permanently
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { payinsAPI } from '../../../api/client';
import ConfirmModal from '../../../components/ConfirmModal';
import {
  canEditPayin,
  canDeletePayin,
  getStatusText,
  getStatusBadgeColor,
  getSourceText,
  getSourceBadgeColor,
  formatPayinDateTime,
  formatThaiDate,
} from '../../../utils/payinStatus';

export default function PayinDetailModal({ payin, onClose, onDelete }) {
  if (!payin) return null;

  const { date, time } = formatPayinDateTime(payin);
  const canEdit = canEditPayin(payin);
  const canDelete = canDeletePayin(payin);
  const submittedDate = formatThaiDate(payin.created_at, {
    day: 'numeric',
    month: 'short',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = () => {
    setShowDeleteConfirm(false);
    onDelete(payin.id);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop - tap to close */}
      <div 
        className="absolute inset-0" 
        onClick={onClose}
      />
      
      {/* Modal - Bottom sheet style on mobile */}
      <div className="relative bg-gray-800 w-full max-w-md rounded-t-2xl sm:rounded-2xl max-h-[90vh] overflow-y-auto animate-slide-up">
        {/* Header */}
        <div className="sticky top-0 bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">รายละเอียดการชำระเงิน</h2>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center text-gray-400 active:text-white active:bg-gray-700 rounded-full min-h-[44px] min-w-[44px]"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Amount - Prominent */}
          <div className="text-center py-4">
            <p className="text-sm text-gray-400 mb-1">จำนวนเงิน</p>
            <p className="text-4xl font-bold text-white">฿{payin.amount?.toLocaleString()}</p>
          </div>

          {/* Status Badge */}
          <div className="flex justify-center">
            <span className={`px-4 py-2 rounded-full text-sm font-medium ${getStatusBadgeColor(payin.status)}`}>
              {getStatusText(payin.status)}
            </span>
          </div>

          {/* Rejection Reason - Prominent when rejected */}
          {(payin.status === 'REJECTED_NEEDS_FIX' || payin.status === 'REJECTED') && payin.reject_reason && (
            <div className="bg-red-900 bg-opacity-40 border border-red-600 rounded-lg p-4">
              <p className="text-sm font-medium text-red-300 mb-1">⚠️ เหตุผลที่ปฏิเสธ</p>
              <p className="text-white">
                {payin.reject_reason}
              </p>
            </div>
          )}

          {/* Admin Note - Display separately if present (read-only) */}
          {payin.admin_note && (
            <div className="bg-gray-700 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-400 mb-1">📝 หมายเหตุจากผู้ดูแล</p>
              <p className="text-white text-sm">
                {payin.admin_note}
              </p>
            </div>
          )}

          {/* Details Grid */}
          <div className="bg-gray-700 rounded-lg divide-y divide-gray-600">
            {/* Transfer Date/Time */}
            <div className="px-4 py-3">
              <p className="text-xs text-gray-400 mb-1">วันที่โอน</p>
              <p className="text-white font-medium">{date}</p>
            </div>
            <div className="px-4 py-3">
              <p className="text-xs text-gray-400 mb-1">เวลาโอน</p>
              <p className="text-white font-medium">{time} น.</p>
            </div>

            {/* Source */}
            <div className="px-4 py-3">
              <p className="text-xs text-gray-400 mb-1">แหล่งที่มา</p>
              <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getSourceBadgeColor(payin.source)}`}>
                {getSourceText(payin.source)}
              </span>
            </div>

            {/* Submitted At */}
            <div className="px-4 py-3">
              <p className="text-xs text-gray-400 mb-1">ส่งข้อมูลเมื่อ</p>
              <p className="text-white font-medium">{submittedDate}</p>
            </div>
          </div>

          {/* Slip Preview — use backend redirect endpoint for R2 slips */}
          {(payin.slip_url || payin.slip_image_url) && (
            <div className="bg-gray-700 rounded-lg p-4">
              <p className="text-xs text-gray-400 mb-2">สลิป</p>
              <a 
                href={payinsAPI.slipUrl(payin.id)} 
                target="_blank" 
                rel="noopener noreferrer"
                className="block"
              >
                <img
                  src={payinsAPI.slipUrl(payin.id)}
                  alt="สลิปการโอนเงิน"
                  className="w-full max-h-64 object-contain rounded-lg border border-gray-600"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60"><text x="10" y="30" fill="gray">ไม่พบรูป</text></svg>';
                  }}
                />
              </a>
              <p className="text-xs text-gray-500 mt-2 text-center">แตะเพื่อดูขนาดเต็ม</p>
            </div>
          )}

          {/* Actions - Only visible in editable states */}
          {(canEdit || canDelete) && (
            <div className="space-y-3 pt-4">
              {canEdit && (
                <Link
                  to="/resident/submit"
                  state={{ editPayin: payin }}
                  className="block w-full bg-blue-600 text-white text-center font-semibold py-4 rounded-lg active:bg-blue-700 min-h-[44px]"
                  onClick={onClose}
                >
                  ✏️ แก้ไข
                </Link>
              )}
              {canDelete && (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="w-full bg-red-600 text-white font-semibold py-4 rounded-lg active:bg-red-700 min-h-[44px]"
                >
                  🗑️ ลบรายการ
                </button>
              )}
            </div>
          )}

          {/* Read-only notice for accepted */}
          {payin.status === 'ACCEPTED' && (
            <div className="bg-green-900 bg-opacity-30 border border-green-600 rounded-lg p-4 text-center">
              <p className="text-green-300 text-sm">
                ✓ รายการนี้ได้รับการยืนยันแล้ว
              </p>
              <p className="text-green-400 text-xs mt-1">
                ไม่สามารถแก้ไขหรือลบได้
              </p>
            </div>
          )}

          {/* Waiting notice for submitted */}
          {payin.status === 'SUBMITTED' && (
            <div className="bg-blue-900 bg-opacity-30 border border-blue-600 rounded-lg p-4 text-center">
              <p className="text-blue-300 text-sm">
                ⏳ กำลังรอการตรวจสอบ
              </p>
              <p className="text-blue-400 text-xs mt-1">
                ไม่สามารถแก้ไขหรือลบได้ในขณะนี้
              </p>
            </div>
          )}

          {/* PENDING notice - can edit but not delete */}
          {payin.status === 'PENDING' && (
            <div className="bg-yellow-900 bg-opacity-30 border border-yellow-600 rounded-lg p-4 text-center">
              <p className="text-yellow-300 text-sm">
                📝 สามารถแก้ไขข้อมูลได้
              </p>
              <p className="text-yellow-400 text-xs mt-1">
                แต่ไม่สามารถลบได้ เนื่องจากรายการอยู่ระหว่างรอตรวจสอบ
              </p>
            </div>
          )}
        </div>

        {/* Close Button - Bottom */}
        <div className="sticky bottom-0 bg-gray-800 border-t border-gray-700 p-4">
          <button
            onClick={onClose}
            className="w-full bg-gray-700 text-white font-semibold py-4 rounded-lg active:bg-gray-600 min-h-[44px]"
          >
            ปิด
          </button>
        </div>
      </div>
      <ConfirmModal
        open={showDeleteConfirm}
        title="ลบรายการชำระเงิน"
        message="คุณต้องการลบรายการชำระเงินนี้ใช่หรือไม่? การดำเนินการนี้ไม่สามารถย้อนกลับได้"
        variant="danger"
        confirmText="ลบ"
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
