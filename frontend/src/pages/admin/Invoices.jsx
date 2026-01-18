import { useState, useEffect } from 'react';
import { invoicesAPI } from '../../api/client';
import ApplyPaymentModal from '../../components/ApplyPaymentModal';

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('auto'); // 'auto' or 'manual'
  
  // Apply Payment Modal state
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  
  // Invoice Detail Modal state
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [invoiceDetail, setInvoiceDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    loadInvoices();
  }, [activeTab]);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const params = { invoice_type: activeTab === 'auto' ? 'auto_monthly' : 'manual' };
      const response = await invoicesAPI.list(params);
      setInvoices(response.data);
    } catch (error) {
      console.error('Failed to load invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMonthly = async () => {
    if (!confirm('Generate monthly invoices for all active houses?')) return;
    try {
      await invoicesAPI.generateMonthly();
      alert('Monthly invoices generated successfully');
      loadInvoices();
    } catch (error) {
      console.error('Failed to generate invoices:', error);
      alert('Failed to generate invoices');
    }
  };

  const handleRowClick = async (invoice) => {
    setSelectedInvoice(invoice);
    setShowDetailModal(true);
    setDetailLoading(true);
    
    try {
      const [detailRes, paymentsRes] = await Promise.all([
        invoicesAPI.getDetail(invoice.id),
        invoicesAPI.getPayments(invoice.id)
      ]);
      setInvoiceDetail(detailRes.data);
      setPayments(paymentsRes.data.payments || []);
    } catch (error) {
      console.error('Failed to load invoice detail:', error);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleApplyPayment = (invoice, e) => {
    e?.stopPropagation();
    setSelectedInvoice({
      ...invoice,
      house_id: invoice.house_id,
      house_code: invoice.house_number,
      total_amount: invoice.total,
      outstanding: invoice.outstanding ?? invoice.total
    });
    setShowApplyModal(true);
  };

  const handleApplySuccess = () => {
    loadInvoices();
    // Refresh detail if open
    if (showDetailModal && selectedInvoice) {
      handleRowClick(selectedInvoice);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'bg-yellow-500/20 text-yellow-400',
      ISSUED: 'bg-yellow-500/20 text-yellow-400',
      paid: 'bg-green-500/20 text-green-400',
      PAID: 'bg-green-500/20 text-green-400',
      PARTIALLY_PAID: 'bg-blue-500/20 text-blue-400',
      overdue: 'bg-red-500/20 text-red-400',
    };
    return badges[status] || 'bg-gray-500/20 text-gray-400';
  };

  const formatStatus = (status) => {
    const labels = {
      pending: 'Pending',
      ISSUED: 'Pending',
      paid: 'Paid',
      PAID: 'Paid',
      PARTIALLY_PAID: 'Partial',
      overdue: 'Overdue',
    };
    return labels[status] || status;
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Invoices Management</h1>
        <p className="text-gray-400">Manage auto-generated and manual invoices</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('auto')}
          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
            activeTab === 'auto'
              ? 'bg-primary-600 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          Auto Monthly
        </button>
        <button
          onClick={() => setActiveTab('manual')}
          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
            activeTab === 'manual'
              ? 'bg-primary-600 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          Manual
        </button>
        {activeTab === 'auto' && (
          <button onClick={handleGenerateMonthly} className="btn-primary ml-auto">
            Generate Monthly Invoices
          </button>
        )}
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>House</th>
                <th>Cycle</th>
                <th>Total</th>
                <th>Paid</th>
                <th>Outstanding</th>
                <th>Status</th>
                <th>Due Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="8" className="text-center py-8">Loading...</td></tr>
              ) : invoices.length === 0 ? (
                <tr><td colSpan="8" className="text-center py-8 text-gray-400">No invoices found</td></tr>
              ) : (
                invoices.map((inv) => {
                  const paid = inv.paid || 0;
                  const outstanding = inv.outstanding ?? (inv.total - paid);
                  const canApply = outstanding > 0;
                  
                  return (
                    <tr 
                      key={inv.id} 
                      onClick={() => handleRowClick(inv)}
                      className="cursor-pointer hover:bg-slate-700/50 transition-colors"
                    >
                      <td className="font-medium text-white">{inv.house_number}</td>
                      <td className="text-gray-300">{inv.cycle || '-'}</td>
                      <td className="text-gray-300">฿{inv.total.toLocaleString()}</td>
                      <td className="text-green-400">฿{paid.toLocaleString()}</td>
                      <td className={outstanding > 0 ? 'text-yellow-400' : 'text-gray-400'}>
                        ฿{outstanding.toLocaleString()}
                      </td>
                      <td>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(inv.status)}`}>
                          {formatStatus(inv.status)}
                        </span>
                      </td>
                      <td className="text-gray-300">{new Date(inv.due_date).toLocaleDateString()}</td>
                      <td>
                        {canApply && (
                          <button
                            onClick={(e) => handleApplyPayment(inv, e)}
                            className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-500 transition-colors"
                          >
                            Apply
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Apply Payment Modal */}
      <ApplyPaymentModal
        isOpen={showApplyModal}
        onClose={() => setShowApplyModal(false)}
        invoice={selectedInvoice}
        onSuccess={handleApplySuccess}
      />

      {/* Invoice Detail Modal */}
      {showDetailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-white">Invoice Detail</h2>
                <p className="text-gray-400 text-sm">
                  {selectedInvoice?.house_number} - {selectedInvoice?.cycle}
                </p>
              </div>
              <button
                onClick={() => setShowDetailModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[70vh]">
              {detailLoading ? (
                <div className="text-center py-8 text-gray-400">Loading...</div>
              ) : invoiceDetail ? (
                <>
                  {/* Summary */}
                  <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
                    <div className="grid grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-gray-400 text-sm">Total</div>
                        <div className="text-white font-bold text-lg">
                          ฿{invoiceDetail.total_amount?.toLocaleString() || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-sm">Paid</div>
                        <div className="text-green-400 font-bold text-lg">
                          ฿{invoiceDetail.paid_amount?.toLocaleString() || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-sm">Outstanding</div>
                        <div className="text-yellow-400 font-bold text-lg">
                          ฿{invoiceDetail.outstanding_amount?.toLocaleString() || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-sm">Status</div>
                        <div className={`font-bold text-lg ${
                          invoiceDetail.status === 'PAID' ? 'text-green-400' :
                          invoiceDetail.status === 'PARTIALLY_PAID' ? 'text-blue-400' :
                          'text-yellow-400'
                        }`}>
                          {formatStatus(invoiceDetail.status)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Apply Payment Button */}
                  {(invoiceDetail.outstanding_amount || 0) > 0 && (
                    <div className="mb-6">
                      <button
                        onClick={() => {
                          setShowDetailModal(false);
                          handleApplyPayment({
                            ...selectedInvoice,
                            house_id: invoiceDetail.house_id,
                            house_code: invoiceDetail.house_code,
                            total_amount: invoiceDetail.total_amount,
                            outstanding: invoiceDetail.outstanding_amount
                          });
                        }}
                        className="w-full py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-500 transition-colors font-medium"
                      >
                        Apply Payment / ชำระเงิน
                      </button>
                    </div>
                  )}

                  {/* Payment History */}
                  <div>
                    <h3 className="text-white font-medium mb-3">Payment History / ประวัติการชำระ</h3>
                    {payments.length === 0 ? (
                      <div className="text-center py-6 text-gray-400 bg-slate-700/30 rounded-lg">
                        No payments recorded yet
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {payments.map((payment, idx) => (
                          <div key={idx} className="bg-slate-700/50 rounded-lg p-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="text-green-400 font-bold">
                                  ฿{payment.amount?.toLocaleString()}
                                </div>
                                <div className="text-gray-400 text-sm mt-1">
                                  From Ledger #{payment.ledger_id || payment.income_transaction_id}
                                </div>
                                {payment.note && (
                                  <div className="text-gray-500 text-sm mt-1">
                                    Note: {payment.note}
                                  </div>
                                )}
                              </div>
                              <div className="text-gray-400 text-sm">
                                {payment.applied_at ? new Date(payment.applied_at).toLocaleString('th-TH') : '-'}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-400">Failed to load invoice detail</div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-slate-700 flex justify-end">
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-6 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
