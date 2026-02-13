import React from 'react';
import { Eye, Edit2 } from 'lucide-react';
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
    <div className="space-y-3">
      {payins.map((payin, index) => {
        // Determine status color for indicator line
        const getStatusColor = (status) => {
          const upperStatus = status?.toUpperCase();
          if (['MATCHED', 'ACCEPTED'].includes(upperStatus)) return 'bg-gradient-to-b from-green-500 to-transparent';
          if (['REJECTED', 'REJECTED_NEEDS_FIX'].includes(upperStatus)) return 'bg-gradient-to-b from-red-500 to-transparent';
          return 'bg-gradient-to-b from-yellow-500 to-transparent';
        };
        
        return (
          <div
            key={payin.id || index}
            className="relative bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-all shadow-sm"
          >
            {/* Status Indicator Line */}
            <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-lg ${getStatusColor(payin.status)}`} />
            
            {/* Content */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                {/* Date */}
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">
                  ส่งสลิปเมื่อ {formatDateTime(payin).split(' ')[0]}
                </p>
                
                {/* Amount */}
                <p className="text-2xl font-bold text-emerald-400 mb-2">
                  ฿{formatAmount(payin.amount)}
                </p>
                
                {/* Transfer Time */}
                <p className="text-xs text-gray-500">
                  โอนเมื่อ {formatDateTime(payin)}
                </p>
              </div>
              
              {/* Right Side: Status & Actions */}
              <div className="flex flex-col items-end gap-2">
                {/* Status Badge */}
                <span className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${getStatusBadgeColor(payin.status)}`}>
                  {getStatusText(payin.status)}
                </span>
                
                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                  {/* View Button */}
                  <button
                    onClick={() => onView && onView(payin)}
                    className="w-9 h-9 rounded-lg bg-gray-700 hover:bg-gray-600 flex items-center justify-center transition-colors"
                    aria-label="ดูรายละเอียด"
                  >
                    <Eye size={18} className="text-gray-300" />
                  </button>

                  {/* Edit Button (only for editable status) */}
                  {isEditable(payin.status) && (
                    <button
                      onClick={() => onEdit && onEdit(payin)}
                      className="w-9 h-9 rounded-lg bg-blue-600 hover:bg-blue-700 flex items-center justify-center transition-colors"
                      aria-label="แก้ไข"
                    >
                      <Edit2 size={18} className="text-white" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default PaymentHistoryCompactList;
