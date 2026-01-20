import React from 'react';
import { formatPayinDateTime, getStatusBadgeColor, getStatusText } from '../../../utils/payinStatus';

/**
 * PaymentHistoryCompactList Component
 * 
 * Single-line compact list view for payment history
 * - No horizontal scrolling
 * - All info in one line
 * - Mobile-friendly
 */
const PaymentHistoryCompactList = ({ payins = [], onView, onEdit }) => {
  
  // ตรวจสอบว่า status สามารถแก้ไขได้หรือไม่
  const isEditable = (status) => {
    return ['DRAFT', 'PENDING', 'REJECTED', 'REJECTED_NEEDS_FIX'].includes(status);
  };

  // ฟังก์ชันจัดรูปแบบวันที่และเวลา (ใช้ centralized utility)
  const formatDateTime = (payin) => {
    const { date, time } = formatPayinDateTime(payin);
    return `${date} ${time}`;
  };

  // ฟังก์ชันจัดรูปแบบจำนวนเงิน
  const formatAmount = (amount) => {
    return new Intl.NumberFormat('th-TH').format(amount);
  };

  // Empty state
  if (!payins || payins.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <p>ยังไม่มีประวัติการส่งสลิป</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {payins.map((payin, index) => (
        <div
          key={payin.id || index}
          className={`
            flex items-center justify-between gap-2 p-3 rounded-lg
            ${index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-750'}
            hover:bg-gray-700 transition-colors
          `}
        >
          {/* Left: Amount */}
          <div className="flex-shrink-0">
            <span className="text-white font-bold text-lg">
              ฿{formatAmount(payin.amount)}
            </span>
          </div>

          {/* Middle: Date-Time */}
          <div className="flex-shrink-0 min-w-0">
            <span className="text-gray-300 text-sm whitespace-nowrap">
              {formatDateTime(payin)}
            </span>
          </div>

          {/* Right: Status Badge */}
          <div className="flex-shrink-0">
            <span
              className={`
                inline-block px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap
                ${getStatusBadgeColor(payin.status)}
              `}
            >
              {getStatusText(payin.status)}
            </span>
          </div>

          {/* Far Right: Action Buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* View Button */}
            <button
              onClick={() => onView && onView(payin)}
              className="w-9 h-9 rounded-full bg-gray-600 hover:bg-gray-500 flex items-center justify-center transition-colors"
              aria-label="ดูรายละเอียด"
            >
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
            </button>

            {/* Edit Button (only for editable status) */}
            {isEditable(payin.status) && (
              <button
                onClick={() => onEdit && onEdit(payin)}
                className="w-9 h-9 rounded-full bg-blue-500 hover:bg-blue-600 flex items-center justify-center transition-colors"
                aria-label="แก้ไข"
              >
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default PaymentHistoryCompactList;
