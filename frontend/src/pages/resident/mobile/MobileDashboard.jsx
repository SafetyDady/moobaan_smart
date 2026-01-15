import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { invoicesAPI, payinsAPI, api } from '../../../api/client';
import { useRole } from '../../../contexts/RoleContext';
import MobileLayout from './MobileLayout';

export default function MobileDashboard() {
  const { currentHouseId } = useRole();
  const [invoices, setInvoices] = useState([]);
  const [payins, setPayins] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [currentHouseId]);

  const loadData = async () => {
    try {
      const [invoicesRes, payinsRes, summaryRes] = await Promise.all([
        invoicesAPI.list({ house_id: currentHouseId }),
        payinsAPI.list({ house_id: currentHouseId }),
        api.get('/api/dashboard/summary'),
      ]);
      setInvoices(invoicesRes.data);
      setPayins(payinsRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get balance from summary API (negative = owe, positive = overpaid)
  const currentBalance = summary?.current_balance || 0;
  const isOverpaid = currentBalance > 0;
  const displayAmount = Math.abs(currentBalance);

  const getStatusColor = (status) => {
    const colors = {
      submitted: 'bg-blue-500 text-white',
      rejected: 'bg-red-500 text-white',
      matched: 'bg-yellow-500 text-white',
      accepted: 'bg-green-500 text-white',
      pending: 'bg-yellow-500 text-white',
      paid: 'bg-green-500 text-white',
      overdue: 'bg-red-500 text-white',
    };
    return colors[status] || 'bg-gray-500 text-white';
  };

  const getStatusText = (status) => {
    const texts = {
      submitted: 'ส่งแล้ว',
      rejected: 'ถูกปฏิเสธ',
      matched: 'จับคู่แล้ว',
      accepted: 'อนุมัติแล้ว',
      pending: 'รอชำระ',
      paid: 'ชำระแล้ว',
      overdue: 'เกินกำหนด',
    };
    return texts[status] || status;
  };

  if (loading) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-4xl mb-2">⏳</div>
            <p className="text-gray-400">กำลังโหลด...</p>
          </div>
        </div>
      </MobileLayout>
    );
  }

  return (
    <MobileLayout>
      {/* Sticky Balance Card */}
      <div className="sticky top-0 z-10 bg-gray-900 p-4">
        <div className={`rounded-xl p-5 shadow-lg ${
          isOverpaid 
            ? 'bg-gradient-to-br from-green-600 to-green-700' 
            : 'bg-gradient-to-br from-red-600 to-red-700'
        }`}>
          <p className={`text-sm mb-1 ${
            isOverpaid ? 'text-green-100' : 'text-red-100'
          }`}>
            {isOverpaid ? 'ชำระเกิน' : 'ยอดค้างชำระ'}
          </p>
          <p className="text-4xl font-bold text-white mb-4">
            ฿{displayAmount.toLocaleString()}
          </p>
          {!isOverpaid && (
            <Link 
              to="/resident/submit" 
              className="block w-full bg-white text-red-600 font-semibold py-3 rounded-lg text-center active:bg-red-50 transition-colors"
            >
              💳 ชำระเงินเลย
            </Link>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-3 px-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <p className="text-xs text-gray-400 mb-1">ใบแจ้งหนี้ทั้งหมด</p>
          <p className="text-2xl font-bold text-white">{invoices.length}</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <p className="text-xs text-gray-400 mb-1">ส่งสลิปแล้ว</p>
          <p className="text-2xl font-bold text-white">{payins.length}</p>
        </div>
      </div>

      {/* Invoices Section */}
      <div className="px-4 mb-6">
        <h2 className="text-lg font-bold text-white mb-3">ใบแจ้งหนี้</h2>
        {invoices.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 text-center border border-gray-700">
            <div className="text-4xl mb-2">📄</div>
            <p className="text-gray-400">ไม่มีใบแจ้งหนี้</p>
          </div>
        ) : (
          <div className="space-y-3">
            {invoices.map(inv => (
              <div 
                key={inv.id} 
                className="bg-gray-800 rounded-lg p-4 border border-gray-700 active:bg-gray-750 transition-colors"
              >
                {/* Header */}
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-xs text-gray-400">รอบบิล</span>
                    <p className="font-medium text-white">{inv.cycle || '-'}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(inv.status)}`}>
                    {getStatusText(inv.status)}
                  </span>
                </div>
                
                {/* Amount */}
                <div className="text-2xl font-bold text-white mb-2">
                  ฿{inv.total.toLocaleString()}
                </div>
                
                {/* Details */}
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">
                    {inv.invoice_type === 'monthly_auto' ? 'รายเดือน' : 'พิเศษ'}
                  </span>
                  <span className="text-gray-400">
                    ครบกำหนด: {new Date(inv.due_date).toLocaleDateString('th-TH', { 
                      day: 'numeric', 
                      month: 'short',
                      year: '2-digit'
                    })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Payment History Section */}
      <div className="px-4 pb-6">
        <h2 className="text-lg font-bold text-white mb-3">ประวัติการส่งสลิป</h2>
        {payins.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 text-center border border-gray-700">
            <div className="text-4xl mb-2">💳</div>
            <p className="text-gray-400">ยังไม่มีการส่งสลิป</p>
            <Link 
              to="/resident/submit"
              className="inline-block mt-4 text-primary-400 font-medium"
            >
              ส่งสลิปเลย →
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {payins.map(payin => (
              <div 
                key={payin.id} 
                className="bg-gray-800 rounded-lg p-4 border border-gray-700"
              >
                {/* Header */}
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-xs text-gray-400">จำนวนเงิน</span>
                    <p className="text-xl font-bold text-white">
                      ฿{payin.amount.toLocaleString()}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(payin.status)}`}>
                    {getStatusText(payin.status)}
                  </span>
                </div>
                
                {/* Transfer Info */}
                <div className="text-sm text-gray-400 mb-2">
                  โอนเมื่อ: {new Date(payin.transfer_date).toLocaleDateString('th-TH', {
                    day: 'numeric',
                    month: 'short',
                    year: '2-digit'
                  })} เวลา {payin.transfer_hour}:{String(payin.transfer_minute).padStart(2, '0')} น.
                </div>

                {/* Rejection Reason */}
                {payin.reject_reason && (
                  <div className="bg-red-900 bg-opacity-30 border border-red-600 rounded p-2 mb-2">
                    <p className="text-xs text-red-300">
                      <strong>เหตุผล:</strong> {payin.reject_reason}
                    </p>
                  </div>
                )}

                {/* Actions */}
                {payin.status === 'rejected' && (
                  <Link 
                    to="/resident/submit" 
                    state={{ editPayin: payin }}
                    className="block w-full bg-primary-600 text-white text-center font-medium py-2 rounded mt-3 active:bg-primary-700"
                  >
                    แก้ไขและส่งใหม่
                  </Link>
                )}

                {/* Submitted Date */}
                <div className="text-xs text-gray-500 mt-2">
                  ส่งเมื่อ: {new Date(payin.created_at).toLocaleDateString('th-TH', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric'
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </MobileLayout>
  );
}
