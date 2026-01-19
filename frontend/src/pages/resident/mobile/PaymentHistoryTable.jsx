import React from 'react';
import { format } from 'date-fns';
import { th } from 'date-fns/locale';

/**
 * PaymentHistoryTable Component
 * 
 * แสดงประวัติการส่งสลิปในรูปแบบตาราง (Table View)
 * เหมาะสำหรับการดูข้อมูลหลายรายการพร้อมกัน
 */
const PaymentHistoryTable = ({ payins, onView, onEdit }) => {
  // ฟังก์ชันสำหรับแปลง status เป็นข้อความภาษาไทย
  const getStatusText = (status) => {
    const statusMap = {
      DRAFT: 'ร่าง',
      PENDING: 'รอตรวจสอบ',
      SUBMITTED: 'รอตรวจสอบ',
      ACCEPTED: 'ยืนยันแล้ว',
      REJECTED: 'ถูกปฏิเสธ',
      REJECTED_NEEDS_FIX: 'ต้องแก้ไข',
    };
    return statusMap[status] || status;
  };

  // ฟังก์ชันสำหรับกำหนดสี status badge
  const getStatusColor = (status) => {
    const colorMap = {
      DRAFT: 'bg-gray-500',
      PENDING: 'bg-yellow-500 text-black',
      SUBMITTED: 'bg-blue-500',
      ACCEPTED: 'bg-green-500',
      REJECTED: 'bg-red-500',
      REJECTED_NEEDS_FIX: 'bg-red-500',
    };
    return colorMap[status] || 'bg-gray-500';
  };

  // ฟังก์ชันตรวจสอบว่าสามารถแก้ไขได้หรือไม่
  const isEditable = (status) => {
    return ['DRAFT', 'PENDING', 'REJECTED', 'REJECTED_NEEDS_FIX'].includes(status);
  };

  // ฟังก์ชันจัดรูปแบบวันที่และเวลา
  const formatDateTime = (transferDate, transferTime) => {
    try {
      const dateStr = `${transferDate}T${transferTime}`;
      const date = new Date(dateStr);
      
      // Format: "1 ม.ค. 69 11:11"
      const dayMonth = format(date, 'd MMM. yy', { locale: th });
      const time = format(date, 'HH:mm');
      
      return `${dayMonth} ${time}`;
    } catch (error) {
      return `${transferDate} ${transferTime}`;
    }
  };

  // ฟังก์ชันจัดรูปแบบจำนวนเงิน
  const formatAmount = (amount) => {
    return new Intl.NumberFormat('th-TH').format(amount);
  };

  // Empty state
  if (!payins || payins.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-10 text-center">
        <p className="text-gray-500 text-base">ไม่มีประวัติการส่งสลิป</p>
        <p className="text-gray-600 text-sm mt-2">กดปุ่ม + ด้านล่างเพื่อส่งสลิปใหม่</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Table Container with horizontal scroll */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[600px]">
          {/* Table Header */}
          <thead>
            <tr className="bg-gray-700">
              <th className="px-2 py-3 text-left text-xs font-semibold text-gray-400 w-[20%]">
                จำนวนเงิน
              </th>
              <th className="px-2 py-3 text-left text-xs font-semibold text-gray-400 w-[30%]">
                วันที่-เวลา
              </th>
              <th className="px-2 py-3 text-center text-xs font-semibold text-gray-400 w-[25%]">
                สถานะ
              </th>
              <th className="px-2 py-3 text-right text-xs font-semibold text-gray-400 w-[25%]">
                แอคชั่น
              </th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody>
            {payins.map((payin, index) => (
              <tr
                key={payin.id}
                className={`
                  border-b border-gray-700 last:border-b-0
                  hover:bg-gray-750 transition-colors duration-200
                  ${index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-825'}
                `}
              >
                {/* Column 1: Amount */}
                <td className="px-2 py-3">
                  <span className="text-white text-lg font-bold">
                    ฿{formatAmount(payin.amount)}
                  </span>
                </td>

                {/* Column 2: Date-Time */}
                <td className="px-2 py-3">
                  <span className="text-gray-300 text-sm">
                    {formatDateTime(payin.transfer_date, payin.transfer_time)}
                  </span>
                </td>

                {/* Column 3: Status Badge */}
                <td className="px-2 py-3 text-center">
                  <span
                    className={`
                      inline-block px-3 py-1 rounded-full text-xs font-semibold
                      text-white whitespace-nowrap
                      ${getStatusColor(payin.status)}
                    `}
                  >
                    {getStatusText(payin.status)}
                  </span>
                </td>

                {/* Column 4: Action Buttons */}
                <td className="px-2 py-3">
                  <div className="flex items-center justify-end gap-2">
                    {/* View Button */}
                    <button
                      onClick={() => onView(payin)}
                      className="
                        w-9 h-9 rounded-full bg-gray-700 hover:bg-gray-600
                        flex items-center justify-center
                        transition-all duration-200 hover:opacity-80 active:scale-95
                      "
                      aria-label="ดูรายละเอียด"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={2}
                        stroke="currentColor"
                        className="w-5 h-5 text-white"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                      </svg>
                    </button>

                    {/* Edit Button (conditional) */}
                    {isEditable(payin.status) && (
                      <button
                        onClick={() => onEdit(payin)}
                        className="
                          w-9 h-9 rounded-full bg-blue-500 hover:bg-blue-600
                          flex items-center justify-center
                          transition-all duration-200 hover:opacity-80 active:scale-95
                        "
                        aria-label="แก้ไข"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          strokeWidth={2}
                          stroke="currentColor"
                          className="w-5 h-5 text-white"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PaymentHistoryTable;
