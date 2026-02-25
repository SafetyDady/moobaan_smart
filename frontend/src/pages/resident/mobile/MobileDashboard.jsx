import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { invoicesAPI, payinsAPI, api } from '../../../api/client';
import { useRole } from '../../../contexts/RoleContext';
import MobileLayout from './MobileLayout';
import InvoiceTable from './InvoiceTable';
import { Home, Loader2, CreditCard } from 'lucide-react';
import { SkeletonMobileList } from '../../../components/Skeleton';
import { isBlockingPayin } from '../../../utils/payinStatus';

export default function MobileDashboard() {
  const { currentHouseId } = useRole();
  const [invoices, setInvoices] = useState([]);
  const [payins, setPayins] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

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

  // Get balance from summary API (negative = owe, positive = overpaid)
  const currentBalance = summary?.current_balance || 0;
  const isOverpaid = currentBalance > 0;
  const displayAmount = Math.abs(currentBalance);

  // Guard: Wait for house context before rendering dashboard
  if (!currentHouseId) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-full">
          <SkeletonMobileList />
        </div>
      </MobileLayout>
    );
  }

  if (loading) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-full">
          <SkeletonMobileList />
        </div>
      </MobileLayout>
    );
  }

  return (
    <MobileLayout>
      {/* Compact Hero Card (Balance Card) */}
      <div className="sticky top-0 z-10 bg-gray-900 p-4">
        <div className={`rounded-2xl p-5 shadow-xl ${
          isOverpaid 
            ? 'bg-gradient-to-br from-emerald-600 to-emerald-700' 
            : 'bg-gradient-to-br from-red-600 to-red-700'
        }`}>
          {/* Status Badge */}
          <div className="flex items-center justify-between mb-3">
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
          <div className="mb-4">
            <p className={`text-sm mb-1 ${
              isOverpaid ? 'text-emerald-100' : 'text-red-100'
            }`}>
              จำนวนเงิน
            </p>
            <p className="text-3xl font-bold text-white">
              ฿{displayAmount.toLocaleString()}
            </p>
          </div>
          
          {/* Action Button */}
          {!isOverpaid && (
            hasBlockingPayin ? (
              <div className="w-full">
                <div className="w-full bg-gray-400 text-gray-600 font-semibold py-2 rounded-lg text-center cursor-not-allowed flex items-center justify-center gap-2">
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
                className="flex items-center justify-center gap-2 w-full bg-white text-red-600 font-semibold py-2 rounded-lg hover:bg-red-50 active:bg-red-100 transition-colors duration-200 shadow-md"
              >
                <CreditCard size={20} />
                ชำระเงินเลย
              </Link>
            )
          )}
        </div>
      </div>

      {/* Invoice Table Section */}
      <div className="px-4 mb-6">
        <h2 className="text-xl font-bold text-white mb-4">ใบแจ้งหนี้</h2>
        <InvoiceTable invoices={invoices} />
      </div>

    </MobileLayout>
  );
}
