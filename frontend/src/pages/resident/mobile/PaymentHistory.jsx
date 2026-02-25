import { useState, useEffect } from 'react';
import { ChevronLeft, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { invoicesAPI, payinsAPI } from '../../../api/client';
import { useToast } from '../../../components/Toast';
import { useRole } from '../../../contexts/RoleContext';
import MobileLayout from './MobileLayout';
import PayinDetailModal from './PayinDetailModal';
import {
  getStatusText as getPayinStatusText,
  getStatusBadgeColor,
  formatPayinDateTime,
} from '../../../utils/payinStatus';

export default function PaymentHistory() {
  const navigate = useNavigate();
  const { currentHouseId } = useRole();
  
  // Tab state
  const [activeTab, setActiveTab] = useState('payins'); // 'payins' or 'invoices'
  
  // Payin state
  const [payins, setPayins] = useState([]);
  const [payinFilter, setPayinFilter] = useState('all');
  const [selectedPayin, setSelectedPayin] = useState(null);
  
  // Invoice state
  const [invoices, setInvoices] = useState([]);
  const [invoiceFilter, setInvoiceFilter] = useState('all');
  
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadData();
  }, [currentHouseId]);
  
  const loadData = async () => {
    try {
      setLoading(true);
      const [payinsRes, invoicesRes] = await Promise.all([
        payinsAPI.list({ house_id: currentHouseId }),
        invoicesAPI.list({ house_id: currentHouseId }),
      ]);
      setPayins(payinsRes.data);
      setInvoices(invoicesRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Filter payins
  const filteredPayins = payins.filter(payin => {
    if (payinFilter === 'all') return true;
    if (payinFilter === 'pending') return payin.status === 'PENDING';
    if (payinFilter === 'accepted') return payin.status === 'ACCEPTED';
    if (payinFilter === 'rejected') return payin.status === 'REJECTED_NEEDS_FIX';
    return true;
  });
  
  // Filter invoices — backend returns ISSUED, PARTIALLY_PAID, PAID, CANCELLED, CREDITED
  const filteredInvoices = invoices.filter(invoice => {
    if (invoiceFilter === 'all') return true;
    if (invoiceFilter === 'paid') return invoice.status === 'PAID';
    if (invoiceFilter === 'unpaid') return ['ISSUED', 'PARTIALLY_PAID'].includes(invoice.status);
    if (invoiceFilter === 'cancelled') return ['CANCELLED', 'CREDITED'].includes(invoice.status);
    return true;
  });
  
  // Sort invoices: unpaid first, then by due_date desc
  const sortedInvoices = [...filteredInvoices].sort((a, b) => {
    const order = { ISSUED: 0, PARTIALLY_PAID: 1, PAID: 2, CANCELLED: 3, CREDITED: 3 };
    const diff = (order[a.status] ?? 9) - (order[b.status] ?? 9);
    if (diff !== 0) return diff;
    return new Date(b.due_date || 0) - new Date(a.due_date || 0);
  });
  
  const payinFilterButtons = [
    { id: 'all', label: 'ทั้งหมด' },
    { id: 'pending', label: 'รอตรวจสอบ' },
    { id: 'accepted', label: 'ผ่านแล้ว' },
    { id: 'rejected', label: 'ถูกปฏิเสธ' },
  ];
  
  const invoiceFilterButtons = [
    { id: 'all', label: `ทั้งหมด (${invoices.length})` },
    { id: 'unpaid', label: `ค้างชำระ (${invoices.filter(i => ['ISSUED','PARTIALLY_PAID'].includes(i.status)).length})` },
    { id: 'paid', label: `ชำระแล้ว (${invoices.filter(i => i.status === 'PAID').length})` },
    { id: 'cancelled', label: 'ยกเลิก' },
  ];
  
  if (loading) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">กำลังโหลด...</div>
        </div>
      </MobileLayout>
    );
  }
  
  return (
    <MobileLayout>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center gap-3">
          <button
            onClick={() => navigate('/resident/dashboard')}
            className="text-white active:text-gray-300"
          >
            <ChevronLeft size={24} />
          </button>
          <h1 className="text-lg font-bold text-white">ประวัติการชำระ</h1>
        </div>
        
        {/* Tabs */}
        <div className="bg-gray-800 border-b border-gray-700 flex">
          <button
            onClick={() => setActiveTab('payins')}
            className={`flex-1 py-3 text-sm font-medium transition-colors relative ${
              activeTab === 'payins'
                ? 'text-primary-400'
                : 'text-gray-400'
            }`}
          >
            ประวัติส่งสลิป
            {activeTab === 'payins' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-400" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('invoices')}
            className={`flex-1 py-3 text-sm font-medium transition-colors relative ${
              activeTab === 'invoices'
                ? 'text-primary-400'
                : 'text-gray-400'
            }`}
          >
            ใบแจ้งหนี้
            {activeTab === 'invoices' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-400" />
            )}
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'payins' ? (
            <div className="p-4 space-y-4">
              {/* Filter Buttons */}
              <div className="flex gap-2 overflow-x-auto pb-2">
                {payinFilterButtons.map(btn => (
                  <button
                    key={btn.id}
                    onClick={() => setPayinFilter(btn.id)}
                    className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                      payinFilter === btn.id
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-700 text-gray-300 active:bg-gray-600'
                    }`}
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
              
              {/* Payin List */}
              {filteredPayins.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                  <div className="text-4xl mb-2">📸</div>
                  <div className="text-sm">ยังไม่มีประวัติการส่งสลิป</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredPayins.map(payin => (
                    <div
                      key={payin.id}
                      className="bg-gray-800 rounded-lg p-4 border border-gray-700 flex items-center justify-between"
                    >
                      <div className="flex-1">
                        <div className="text-2xl font-bold text-white">
                          ฿{payin.amount?.toLocaleString('th-TH') || '0'}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {(() => {
                            const dt = formatPayinDateTime(payin);
                            return `${dt.date} ${dt.time}`;
                          })()}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(
                            payin.status
                          )}`}
                        >
                          {getPayinStatusText(payin.status)}
                        </span>
                        <button
                          onClick={() => setSelectedPayin(payin)}
                          className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-gray-300 active:bg-gray-600"
                        >
                          <Eye size={20} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* FAB - Add Payment */}
              <button
                onClick={() => navigate('/resident/submit')}
                className="fixed bottom-20 right-4 w-14 h-14 bg-primary-500 rounded-full shadow-lg flex items-center justify-center text-white text-2xl active:bg-primary-600 z-20"
              >
                +
              </button>
            </div>
          ) : (
            <div className="p-4 space-y-4">
              {/* Filter Buttons */}
              <div className="flex gap-2 overflow-x-auto pb-2">
                {invoiceFilterButtons.map(btn => (
                  <button
                    key={btn.id}
                    onClick={() => setInvoiceFilter(btn.id)}
                    className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                      invoiceFilter === btn.id
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-700 text-gray-300 active:bg-gray-600'
                    }`}
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
              
              {/* Invoice List */}
              {sortedInvoices.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                  <div className="text-4xl mb-2">📄</div>
                  <div className="text-sm">ยังไม่มีใบแจ้งหนี้</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {sortedInvoices.map(invoice => {
                    // Format cycle display
                    const thaiMonths = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
                    let cycleLabel = invoice.cycle;
                    if (invoice.cycle && invoice.cycle !== 'MANUAL') {
                      const [y, m] = invoice.cycle.split('-').map(Number);
                      if (y && m) cycleLabel = `${thaiMonths[m]} ${y + 543}`;
                    } else if (invoice.cycle === 'MANUAL') {
                      cycleLabel = invoice.manual_reason || 'ใบแจ้งหนี้พิเศษ';
                    }
                    
                    // Status badge
                    const statusMap = {
                      'ISSUED': { text: 'รอชำระ', color: 'bg-orange-500/20 text-orange-400' },
                      'PARTIALLY_PAID': { text: 'ชำระบางส่วน', color: 'bg-yellow-500/20 text-yellow-400' },
                      'PAID': { text: 'ชำระแล้ว', color: 'bg-green-500/20 text-green-400' },
                      'CANCELLED': { text: 'ยกเลิก', color: 'bg-gray-500/20 text-gray-400' },
                      'CREDITED': { text: 'เครดิตแล้ว', color: 'bg-gray-500/20 text-gray-400' },
                    };
                    const st = statusMap[invoice.status] || { text: invoice.status, color: 'bg-gray-500/20 text-gray-400' };
                    
                    return (
                      <div
                        key={invoice.id}
                        className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <div className="text-sm font-medium text-gray-300">
                              {cycleLabel}
                            </div>
                            <div className="text-2xl font-bold text-white mt-1">
                              ฿{(invoice.total || 0).toLocaleString('th-TH', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                            </div>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${st.color}`}>
                            {st.text}
                          </span>
                        </div>
                        
                        {/* Payment progress for unpaid/partial */}
                        {['ISSUED', 'PARTIALLY_PAID'].includes(invoice.status) && (
                          <div className="mb-2">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-400">ชำระแล้ว ฿{(invoice.paid || 0).toLocaleString('th-TH')}</span>
                              <span className="text-orange-400">ค้าง ฿{(invoice.outstanding || 0).toLocaleString('th-TH')}</span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-1.5">
                              <div 
                                className="bg-green-500 h-1.5 rounded-full transition-all"
                                style={{ width: `${invoice.total > 0 ? Math.min(((invoice.paid || 0) / invoice.total) * 100, 100) : 0}%` }}
                              />
                            </div>
                          </div>
                        )}
                        
                        {/* Credit note info */}
                        {invoice.total_credited > 0 && (
                          <div className="text-xs text-blue-400 mb-1">
                            เครดิตโนต: -฿{invoice.total_credited.toLocaleString('th-TH')}
                          </div>
                        )}
                        
                        <div className="flex items-center justify-between">
                          {invoice.due_date && (
                            <div className="text-xs text-gray-400">
                              ครบกำหนด: {new Date(invoice.due_date).toLocaleDateString('th-TH')}
                            </div>
                          )}
                          {invoice.items?.[0]?.description && invoice.items[0].description !== 'ค่าส่วนกลาง' && (
                            <div className="text-xs text-gray-500 truncate ml-2">
                              {invoice.items[0].description}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Payin Detail Modal */}
      {selectedPayin && (
        <PayinDetailModal
          payin={selectedPayin}
          onClose={() => setSelectedPayin(null)}
          onDelete={async (payinId) => {
            try {
              await payinsAPI.delete(payinId);
              setSelectedPayin(null);
              loadData();
            } catch (err) {
              const msg = err.response?.data?.detail?.message || 'ลบไม่สำเร็จ';
              toast.error(msg);
            }
          }}
          onUpdate={loadData}
        />
      )}
    </MobileLayout>
  );
}
