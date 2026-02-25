import { useState, useEffect } from 'react';
import { invoicesAPI, housesAPI, creditNotesAPI } from '../../api/client';
import ApplyPaymentModal from '../../components/ApplyPaymentModal';
import CreditNoteModal from '../../components/CreditNoteModal';
import ConfirmModal from '../../components/ConfirmModal';
import { useToast } from '../../components/Toast';

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

  // Manual Invoice Modal state (Phase D.1)
  const [showManualModal, setShowManualModal] = useState(false);
  const [houses, setHouses] = useState([]);
  const [manualForm, setManualForm] = useState({
    house_id: '',
    amount: '',
    description: '',
    due_date: '',
    note: ''
  });
  const [submitting, setSubmitting] = useState(false);

  // Credit Note Modal state (Phase D.2)
  const [showCreditNoteModal, setShowCreditNoteModal] = useState(false);
  const [creditNoteInvoice, setCreditNoteInvoice] = useState(null);

  const toast = useToast();

  // Confirm modal state
  const [confirmGenerate, setConfirmGenerate] = useState(false);

  useEffect(() => {
    loadInvoices();
  }, [activeTab]);

  // Load houses for manual invoice form
  useEffect(() => {
    loadHouses();
  }, []);

  const loadHouses = async () => {
    try {
      const response = await housesAPI.list({ status: 'active' });
      setHouses(response.data || []);
    } catch (error) {
      console.error('Failed to load houses:', error);
    }
  };

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const params = { is_manual: activeTab === 'manual' };
      const response = await invoicesAPI.list(params);
      setInvoices(response.data);
    } catch (error) {
      console.error('Failed to load invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMonthly = async () => {
    try {
      await invoicesAPI.generateMonthly();
      toast.success('สร้างใบแจ้งหนี้รายเดือนสำเร็จ');
      loadInvoices();
    } catch (error) {
      console.error('Failed to generate invoices:', error);
      toast.error('ไม่สามารถสร้างใบแจ้งหนี้ได้');
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

  const getStatusBadge = (status, outstanding, total) => {
    // Phase D.2: Credit Note status badges
    // Priority: Check outstanding-based credit status first
    if (outstanding === 0 && total > 0) {
      // Fully credited/paid
      return 'bg-gray-500/20 text-gray-400';
    }
    if (outstanding > 0 && outstanding < total) {
      // Partially credited/paid
      return 'bg-orange-500/20 text-orange-400';
    }
    
    const badges = {
      pending: 'bg-yellow-500/20 text-yellow-400',
      ISSUED: 'bg-yellow-500/20 text-yellow-400',
      paid: 'bg-green-500/20 text-green-400',
      PAID: 'bg-green-500/20 text-green-400',
      PARTIALLY_PAID: 'bg-blue-500/20 text-blue-400',
      CREDITED: 'bg-gray-500/20 text-gray-400',
      PARTIALLY_CREDITED: 'bg-orange-500/20 text-orange-400',
      overdue: 'bg-red-500/20 text-red-400',
    };
    return badges[status] || 'bg-yellow-500/20 text-yellow-400';
  };

  const formatStatus = (status, outstanding, total) => {
    // Phase D.2: Dynamic status based on outstanding
    if (outstanding === 0 && total > 0) {
      return 'Credited';
    }
    if (outstanding > 0 && outstanding < total) {
      return 'Partial';
    }
    
    const labels = {
      pending: 'Pending',
      ISSUED: 'Pending',
      paid: 'Paid',
      PAID: 'Paid',
      PARTIALLY_PAID: 'Partial',
      CREDITED: 'Credited',
      PARTIALLY_CREDITED: 'Partial',
      overdue: 'Overdue',
    };
    return labels[status] || status;
  };

  // Credit Note handler (Phase D.2)
  const handleOpenCreditNote = (invoice, e) => {
    e?.stopPropagation();
    setCreditNoteInvoice({
      ...invoice,
      outstanding: invoice.outstanding ?? (invoice.total - (invoice.paid || 0))
    });
    setShowCreditNoteModal(true);
  };

  const handleCreditNoteSuccess = () => {
    loadInvoices();
    // Refresh detail if open
    if (showDetailModal && selectedInvoice) {
      handleRowClick(selectedInvoice);
    }
  };

  // Manual Invoice Handlers (Phase D.1)
  const openManualModal = () => {
    // Set default due date to 15 days from now
    const defaultDue = new Date();
    defaultDue.setDate(defaultDue.getDate() + 15);
    setManualForm({
      house_id: '',
      amount: '',
      description: '',
      due_date: defaultDue.toISOString().split('T')[0],
      note: ''
    });
    setShowManualModal(true);
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    
    if (!manualForm.house_id || !manualForm.amount || !manualForm.description || !manualForm.due_date) {
      toast.warning('กรุณากรอกข้อมูลให้ครบ');
      return;
    }
    
    if (parseFloat(manualForm.amount) <= 0) {
      toast.warning('จำนวนเงินต้องมากกว่า 0');
      return;
    }
    
    setSubmitting(true);
    try {
      await invoicesAPI.createManual({
        house_id: parseInt(manualForm.house_id),
        amount: parseFloat(manualForm.amount),
        description: manualForm.description,
        due_date: manualForm.due_date,
        note: manualForm.note || null
      });
      toast.success('สร้าง Manual Invoice สำเร็จ');
      setShowManualModal(false);
      setActiveTab('manual'); // Switch to manual tab
      loadInvoices();
    } catch (error) {
      console.error('Failed to create manual invoice:', error);
      toast.error(error.response?.data?.detail || 'ไม่สามารถสร้าง Invoice ได้');
    } finally {
      setSubmitting(false);
    }
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
        
        {/* Action buttons based on tab */}
        <div className="ml-auto flex gap-2">
          {activeTab === 'auto' && (
            <button onClick={() => setConfirmGenerate(true)} className="btn-primary">
              Generate Monthly Invoices
            </button>
          )}
          {activeTab === 'manual' && (
            <button onClick={openManualModal} className="btn-primary">
              + Create Manual Invoice
            </button>
          )}
        </div>
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
                      <td className="font-medium text-white">
                        {inv.house_number}
                        {inv.is_manual && (
                          <span className="ml-2 px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded-full">
                            Manual
                          </span>
                        )}
                      </td>
                      <td className="text-gray-300">
                        {inv.is_manual ? (
                          <span className="text-purple-400" title={inv.manual_reason}>
                            {inv.manual_reason?.substring(0, 30) || 'Manual'}{inv.manual_reason?.length > 30 ? '...' : ''}
                          </span>
                        ) : (
                          inv.cycle || '-'
                        )}
                      </td>
                      <td className="text-gray-300">฿{inv.total.toLocaleString()}</td>
                      <td className="text-green-400">฿{paid.toLocaleString()}</td>
                      <td className={outstanding > 0 ? 'text-yellow-400' : 'text-gray-400'}>
                        ฿{outstanding.toLocaleString()}
                      </td>
                      <td>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(inv.status, outstanding, inv.total)}`}>
                          {formatStatus(inv.status, outstanding, inv.total)}
                        </span>
                      </td>
                      <td className="text-gray-300">{new Date(inv.due_date).toLocaleDateString()}</td>
                      <td className="space-x-1">
                        {/* Apply Payment Button */}
                        {canApply && (
                          <button
                            onClick={(e) => handleApplyPayment(inv, e)}
                            className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-500 transition-colors"
                          >
                            Apply
                          </button>
                        )}
                        {/* Credit Note Button - Phase D.2 */}
                        {outstanding > 0 && (
                          <button
                            onClick={(e) => handleOpenCreditNote(inv, e)}
                            className="px-2 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-500 transition-colors"
                            title="Create Credit Note / ลดยอดค้าง"
                          >
                            + Credit
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
                          invoiceDetail.outstanding_amount === 0 ? 'text-gray-400' :
                          invoiceDetail.outstanding_amount < invoiceDetail.total_amount ? 'text-orange-400' :
                          invoiceDetail.status === 'PAID' ? 'text-green-400' :
                          invoiceDetail.status === 'PARTIALLY_PAID' ? 'text-blue-400' :
                          'text-yellow-400'
                        }`}>
                          {formatStatus(invoiceDetail.status, invoiceDetail.outstanding_amount || 0, invoiceDetail.total_amount || 0)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  {(invoiceDetail.outstanding_amount || 0) > 0 && (
                    <div className="mb-6 flex gap-3">
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
                        className="flex-1 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-500 transition-colors font-medium"
                      >
                        Apply Payment / ชำระเงิน
                      </button>
                      {/* Credit Note Button - Phase D.2 */}
                      <button
                        onClick={() => {
                          setShowDetailModal(false);
                          handleOpenCreditNote({
                            ...selectedInvoice,
                            house_id: invoiceDetail.house_id,
                            house_code: invoiceDetail.house_code,
                            house_number: invoiceDetail.house_code,
                            total: invoiceDetail.total_amount,
                            outstanding: invoiceDetail.outstanding_amount
                          });
                        }}
                        className="flex-1 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-500 transition-colors font-medium"
                      >
                        + Credit Note / ลดยอด
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

      {/* Manual Invoice Modal (Phase D.1) */}
      {showManualModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl shadow-xl w-full max-w-md mx-4">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-white">Create Manual Invoice</h2>
                <p className="text-gray-400 text-sm">สร้างใบแจ้งหนี้พิเศษ</p>
              </div>
              <button
                onClick={() => setShowManualModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleManualSubmit} className="p-6 space-y-4">
              {/* House Selection */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  บ้าน <span className="text-red-400">*</span>
                </label>
                <select
                  value={manualForm.house_id}
                  onChange={(e) => setManualForm({ ...manualForm, house_id: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                >
                  <option value="">-- เลือกบ้าน --</option>
                  {houses.map((house) => (
                    <option key={house.id} value={house.id}>
                      {house.house_code} - {house.owner_name || 'N/A'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Amount */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  จำนวนเงิน (บาท) <span className="text-red-400">*</span>
                </label>
                <input
                  type="number"
                  min="1"
                  step="0.01"
                  value={manualForm.amount}
                  onChange={(e) => setManualForm({ ...manualForm, amount: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="0.00"
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  รายละเอียด / เหตุผล <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={manualForm.description}
                  onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="เช่น ค่าปรับจอดรถผิดที่, ค่าซ่อมแซม"
                  required
                />
              </div>

              {/* Due Date */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  วันครบกำหนด <span className="text-red-400">*</span>
                </label>
                <input
                  type="date"
                  value={manualForm.due_date}
                  onChange={(e) => setManualForm({ ...manualForm, due_date: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Note */}
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  หมายเหตุ (ถ้ามี)
                </label>
                <textarea
                  value={manualForm.note}
                  onChange={(e) => setManualForm({ ...manualForm, note: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={2}
                  placeholder="หมายเหตุเพิ่มเติม..."
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowManualModal(false)}
                  className="flex-1 px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 transition-colors"
                >
                  ยกเลิก
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 transition-colors disabled:opacity-50"
                >
                  {submitting ? 'กำลังสร้าง...' : 'สร้าง Invoice'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Credit Note Modal (Phase D.2) */}
      <CreditNoteModal
        isOpen={showCreditNoteModal}
        onClose={() => setShowCreditNoteModal(false)}
        invoice={creditNoteInvoice}
        onSuccess={handleCreditNoteSuccess}
      />

      {/* Generate Monthly Confirm Modal */}
      <ConfirmModal
        open={confirmGenerate}
        title="สร้างใบแจ้งหนี้รายเดือน"
        message="ต้องการสร้างใบแจ้งหนี้รายเดือนสำหรับบ้านที่ Active ทั้งหมดใช่หรือไม่?"
        variant="info"
        confirmText="สร้าง"
        onConfirm={handleGenerateMonthly}
        onCancel={() => setConfirmGenerate(false)}
      />
    </div>
  );
}
