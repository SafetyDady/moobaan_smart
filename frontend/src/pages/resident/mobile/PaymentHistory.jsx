import { useState, useEffect } from 'react';
import { ChevronLeft, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { invoicesAPI, payinsAPI } from '../../../api/client';
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
  
  // Filter invoices
  const filteredInvoices = invoices.filter(invoice => {
    if (invoiceFilter === 'all') return true;
    if (invoiceFilter === 'paid') return invoice.status === 'PAID';
    if (invoiceFilter === 'unpaid') return invoice.status === 'UNPAID';
    return true;
  });
  
  const payinFilterButtons = [
    { id: 'all', label: 'ทั้งหมด' },
    { id: 'pending', label: 'รอตรวจสอบ' },
    { id: 'accepted', label: 'ผ่านแล้ว' },
    { id: 'rejected', label: 'ถูกปฏิเสธ' },
  ];
  
  const invoiceFilterButtons = [
    { id: 'all', label: 'ทั้งหมด' },
    { id: 'paid', label: 'ชำระแล้ว' },
    { id: 'unpaid', label: 'ยังไม่ชำระ' },
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
              {filteredInvoices.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                  <div className="text-4xl mb-2">📄</div>
                  <div className="text-sm">ยังไม่มีใบแจ้งหนี้</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredInvoices.map(invoice => (
                    <div
                      key={invoice.id}
                      className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="text-sm font-medium text-gray-300">
                            {invoice.period || 'N/A'}
                          </div>
                          <div className="text-2xl font-bold text-white mt-1">
                            ฿{invoice.total_amount?.toLocaleString('th-TH') || '0'}
                          </div>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            invoice.status === 'PAID'
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}
                        >
                          {invoice.status === 'PAID' ? 'ชำระแล้ว' : 'ยังไม่ชำระ'}
                        </span>
                      </div>
                      {invoice.due_date && (
                        <div className="text-xs text-gray-400">
                          ครบกำหนด: {new Date(invoice.due_date).toLocaleDateString('th-TH')}
                        </div>
                      )}
                    </div>
                  ))}
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
          onUpdate={loadData}
        />
      )}
    </MobileLayout>
  );
}
