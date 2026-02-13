import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { invoicesAPI, payinsAPI, api } from '../../../api/client';
import { useRole } from '../../../contexts/RoleContext';
import MobileLayout from './MobileLayout';
import PayinDetailModal from './PayinDetailModal';
import PaymentHistoryCompactList from './PaymentHistoryCompactList';
import { Home, Loader2, FileText, CreditCard } from 'lucide-react';
import {
  canEditPayin,
  canDeletePayin,
  isBlockingPayin,
  getStatusText as getPayinStatusText,
  getStatusBadgeColor,
  formatPayinDateTime,
  formatThaiDate,
} from '../../../utils/payinStatus';

export default function MobileDashboard() {
  const { currentHouseId } = useRole();
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [payins, setPayins] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPayin, setSelectedPayin] = useState(null);
  const [notification, setNotification] = useState(null); // { type: 'success' | 'error', message: string }

  // Check if there's a blocking pay-in (DRAFT or PENDING)
  const hasBlockingPayin = payins.some(isBlockingPayin);
  const blockingPayin = payins.find(isBlockingPayin);

  useEffect(() => {
    // Guard: Only load data when currentHouseId is ready
    // This prevents API calls with house_id = null during login flow
    if (currentHouseId) {
      loadData();
    }
  }, [currentHouseId]);

  const loadData = async () => {
    // Double guard: Don't call API if no house context
    if (!currentHouseId) {
      console.warn('⚠️ MobileDashboard: No currentHouseId, skipping API calls');
      return;
    }
    
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

  const handleDeletePayin = async (payinId) => {
    try {
      await payinsAPI.delete(payinId);
      setSelectedPayin(null);
      setNotification({ type: 'success', message: '✅ ลบรายการสำเร็จ' });
      setTimeout(() => setNotification(null), 3000);
      loadData();
    } catch (error) {
      console.error('Failed to delete payin:', error);
      
      // Map error codes to Thai messages
      let errorMessage = 'ลบรายการไม่สำเร็จ';
      
      if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        errorMessage = 'เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ (CORS/Network)';
      } else if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (typeof detail === 'object' && detail.message) {
          errorMessage = detail.message;
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        }
      }
      
      setNotification({ type: 'error', message: `❌ ${errorMessage}` });
      setTimeout(() => setNotification(null), 5000);
    }
  };

  // Get balance from summary API (negative = owe, positive = overpaid)
  const currentBalance = summary?.current_balance || 0;
  const isOverpaid = currentBalance > 0;
  const displayAmount = Math.abs(currentBalance);

  // Invoice status colors (separate from Pay-in)
  const getInvoiceStatusColor = (status) => {
    const upperStatus = status?.toUpperCase();
    const colors = {
      PENDING: 'bg-yellow-500 text-black',  // เหลือง - รอชำระ
      UNPAID: 'bg-yellow-500 text-black',   // เหลือง - ยังไม่ชำระ
      PAID: 'bg-green-500 text-white',      // เขียว - ชำระแล้ว
      OVERDUE: 'bg-red-500 text-white',     // แดง - เกินกำหนด
    };
    return colors[upperStatus] || 'bg-gray-500 text-white';
  };

  const getInvoiceStatusText = (status) => {
    const upperStatus = status?.toUpperCase();
    const texts = {
      PENDING: 'รอชำระ',
      UNPAID: 'ยังไม่ชำระ',
      PAID: 'ชำระแล้ว',
      OVERDUE: 'เกินกำหนด',
    };
    return texts[upperStatus] || status;
  };

  // Guard: Wait for house context before rendering dashboard
  // This handles the brief moment after login but before RoleContext syncs
  if (!currentHouseId) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Home className="mx-auto text-emerald-500 mb-2" size={48} />
            <p className="text-gray-400">กำลังโหลดข้อมูลบ้าน...</p>
          </div>
        </div>
      </MobileLayout>
    );
  }

  if (loading) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Loader2 className="mx-auto text-emerald-500 mb-2 animate-spin" size={48} />
            <p className="text-gray-400">กำลังโหลด...</p>
          </div>
        </div>
      </MobileLayout>
    );
  }

  return (
    <MobileLayout>
      {/* Notification Toast */}
      {notification && (
        <div className={`fixed top-4 left-4 right-4 z-50 p-4 rounded-lg shadow-lg ${
          notification.type === 'success' 
            ? 'bg-green-900/90 border border-green-600' 
            : 'bg-red-900/90 border border-red-600'
        }`}>
          <p className={`text-sm ${
            notification.type === 'success' ? 'text-green-300' : 'text-red-300'
          }`}>
            {notification.message}
          </p>
        </div>
      )}

      {/* Sticky Balance Card - Enhanced Design */}
      <div className="sticky top-0 z-10 bg-gray-900 p-4">
        <div className={`rounded-2xl p-6 shadow-xl ${
          isOverpaid 
            ? 'bg-gradient-to-br from-emerald-600 to-emerald-700' 
            : 'bg-gradient-to-br from-red-600 to-red-700'
        }`}>
          {/* Status Badge */}
          <div className="flex items-center justify-between mb-4">
            <span className={`text-sm font-medium ${
              isOverpaid ? 'text-emerald-100' : 'text-red-100'
            }`}>
              {isOverpaid ? 'ชำระเกิน' : 'ยอดค้างชำระ'}
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
              isOverpaid 
                ? 'bg-emerald-500/30 text-emerald-100' 
                : 'bg-red-500/30 text-red-100'
            }`}>
              {isOverpaid ? 'ชำระแล้ว' : 'ต้องชำระ'}
            </span>
          </div>
          
          {/* Amount */}
          <div className="mb-6">
            <p className={`text-sm mb-1 ${
              isOverpaid ? 'text-emerald-100' : 'text-red-100'
            }`}>
              จำนวนเงิน
            </p>
            <p className="text-4xl font-bold text-white">
              ฿{displayAmount.toLocaleString()}
            </p>
          </div>
          
          {/* Action Button */}
          {!isOverpaid && (
            hasBlockingPayin ? (
              <div className="w-full">
                <div className="w-full bg-gray-400 text-gray-600 font-semibold py-3 rounded-lg text-center cursor-not-allowed flex items-center justify-center gap-2">
                  <CreditCard size={20} />
                  ชำระเงินเลย
                </div>
                <p className="text-yellow-200 text-xs mt-2 text-center">
                  ⚠️ คุณมีรายการที่ยังไม่เสร็จ กรุณาดำเนินการให้เสร็จก่อน
                </p>
              </div>
            ) : (
              <Link 
                to="/resident/submit" 
                className="flex items-center justify-center gap-2 w-full bg-white text-red-600 font-semibold py-3 rounded-lg hover:bg-red-50 active:bg-red-100 transition-colors duration-200 shadow-md"
              >
                <CreditCard size={20} />
                ชำระเงินเลย
              </Link>
            )
          )}
        </div>
      </div>

      {/* Quick Stats - Enhanced Cards */}
      <div className="grid grid-cols-2 gap-3 px-4 mb-6">
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 shadow-sm hover:border-gray-600 transition-colors">
          <p className="text-xs text-gray-400 mb-1 uppercase tracking-wide">ใบแจ้งหนี้ทั้งหมด</p>
          <p className="text-3xl font-bold text-white">{invoices.length}</p>
          <p className="text-xs text-gray-500 mt-1">รายการ</p>
        </div>
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 shadow-sm hover:border-gray-600 transition-colors">
          <p className="text-xs text-gray-400 mb-1 uppercase tracking-wide">ส่งสลิปแล้ว</p>
          <p className="text-3xl font-bold text-white">{payins.length}</p>
          <p className="text-xs text-gray-500 mt-1">ครั้ง</p>
        </div>
      </div>

      {/* Invoices Section - Enhanced Card Design */}
      <div className="px-4 mb-6">
        <h2 className="text-xl font-bold text-white mb-4">ใบแจ้งหนี้</h2>
        {invoices.length === 0 ? (
          <div className="bg-gray-800 rounded-xl p-8 text-center border border-gray-700">
            <FileText className="mx-auto text-gray-600 mb-3" size={48} />
            <p className="text-gray-400 font-medium">ไม่มีใบแจ้งหนี้</p>
          </div>
        ) : (
          <div className="space-y-3">
            {invoices.map(inv => (
              <div 
                key={inv.id} 
                className="relative bg-gray-800 rounded-xl p-4 border border-gray-700 hover:border-gray-600 active:bg-gray-750 transition-all shadow-sm"
              >
                {/* Status Indicator Line */}
                <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-xl ${
                  inv.status?.toUpperCase() === 'PAID' ? 'bg-gradient-to-b from-green-500 to-transparent' :
                  inv.status?.toUpperCase() === 'OVERDUE' ? 'bg-gradient-to-b from-red-500 to-transparent' :
                  'bg-gradient-to-b from-yellow-500 to-transparent'
                }`} />
                
                {/* Header */}
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <span className="text-xs text-gray-400 uppercase tracking-wide">รอบบิล</span>
                    <p className="text-lg font-semibold text-white">{inv.cycle || '-'}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getInvoiceStatusColor(inv.status)}`}>
                    {getInvoiceStatusText(inv.status)}
                  </span>
                </div>
                
                {/* Amount */}
                <div className="mb-4 pb-4 border-b border-gray-700">
                  <p className="text-3xl font-bold text-emerald-400">
                    ฿{inv.total.toLocaleString()}
                  </p>
                </div>
                
                {/* Details */}
                <div className="flex justify-between text-xs text-gray-400">
                  <span>
                    {inv.invoice_type === 'monthly_auto' ? 'รายเดือน' : 'พิเศษ'}
                  </span>
                  <span>
                    ครบกำหนด: {formatThaiDate(inv.due_date)}
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
            <CreditCard className="mx-auto text-gray-600 mb-2" size={48} />
            <p className="text-gray-400">ยังไม่มีการส่งสลิป</p>
            {!hasBlockingPayin && (
              <Link 
                to="/resident/submit"
                className="inline-block mt-4 text-primary-400 font-medium"
              >
                ส่งสลิปเลย →
              </Link>
            )}
          </div>
        ) : (
          <PaymentHistoryCompactList
            payins={payins}
            onView={(payin) => setSelectedPayin(payin)}
            onEdit={(payin) => navigate('/resident/submit', { state: { editPayin: payin } })}
          />
        )}
      </div>

      {/* Pay-in Detail Modal */}
      {selectedPayin && (
        <PayinDetailModal
          payin={selectedPayin}
          onClose={() => setSelectedPayin(null)}
          onDelete={handleDeletePayin}
        />
      )}
    </MobileLayout>
  );
}
