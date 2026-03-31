import { useState, useEffect } from 'react';
import { FileText, Search, X, Image } from 'lucide-react';
import { invoicesAPI, housesAPI, creditNotesAPI, payinsAPI } from '../../api/client';
import ApplyPaymentModal from '../../components/ApplyPaymentModal';
import CreditNoteModal from '../../components/CreditNoteModal';
import ConfirmModal from '../../components/ConfirmModal';
import { useToast } from '../../components/Toast';
import { SkeletonTable, SkeletonBlock } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';
import Pagination, { usePagination } from '../../components/Pagination';
import SortableHeader, { useSort } from '../../components/SortableHeader';
import EmptyState from '../../components/EmptyState';
import AdminPageWrapper from '../../components/AdminPageWrapper';
import ExportButton from '../../components/ExportButton';


export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('auto');
  const [filterHouseCode, setFilterHouseCode] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const [showApplyModal, setShowApplyModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [invoiceDetail, setInvoiceDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [payments, setPayments] = useState([]);

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

  const [showCreditNoteModal, setShowCreditNoteModal] = useState(false);
  const [creditNoteInvoice, setCreditNoteInvoice] = useState(null);
  const [slipViewUrl, setSlipViewUrl] = useState(null);

  const toast = useToast();

  // Pagination
  const { sortConfig, requestSort, sortedData: sortedInvoices } = useSort(invoices);
  const paged = usePagination(sortedInvoices);
  const [confirmGenerate, setConfirmGenerate] = useState(false);

  useEffect(() => {
    loadInvoices();
  }, [activeTab, filterStatus]);

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
      if (filterStatus) params.status = filterStatus;
      // Find house_id from house_code search
      if (filterHouseCode.trim()) {
        const match = houses.find(h => h.house_code === filterHouseCode.trim());
        if (match) {
          params.house_id = match.id;
        } else {
          // No exact match → show empty
          setInvoices([]);
          setLoading(false);
          return;
        }
      }
      const response = await invoicesAPI.list(params);
      setInvoices(response.data);
    } catch (error) {
      console.error('Failed to load invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadInvoices();
  };

  const handleClearFilters = () => {
    setFilterHouseCode('');
    setFilterStatus('');
  };

  const handleGenerateMonthly = async () => {
    try {
      await invoicesAPI.generateMonthly();
      toast.success(t('invoices.generateSuccess'));
      loadInvoices();
    } catch (error) {
      console.error('Failed to generate invoices:', error);
      toast.error(t('invoices.generateFailed'));
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
    if (showDetailModal && selectedInvoice) {
      handleRowClick(selectedInvoice);
    }
  };

  const getStatusBadge = (status, outstanding, total) => {
    if (outstanding === 0 && total > 0) {
      return 'bg-gray-500/20 text-gray-400';
    }
    if (outstanding > 0 && outstanding < total) {
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
    if (outstanding === 0 && total > 0) {
      return t('status.credited');
    }
    if (outstanding > 0 && outstanding < total) {
      return t('status.partial');
    }
    
    const labels = {
      pending: t('status.pending'),
      ISSUED: t('status.pending'),
      paid: t('status.paid'),
      PAID: t('status.paid'),
      PARTIALLY_PAID: t('status.partial'),
      CREDITED: t('status.credited'),
      PARTIALLY_CREDITED: t('status.partial'),
      overdue: t('status.overdue'),
    };
    return labels[status] || status;
  };

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
    if (showDetailModal && selectedInvoice) {
      handleRowClick(selectedInvoice);
    }
  };

  const openManualModal = () => {
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
      toast.warning(t('invoices.fillRequired'));
      return;
    }
    
    if (parseFloat(manualForm.amount) <= 0) {
      toast.warning(t('invoices.amountPositive'));
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
      toast.success(t('invoices.manualSuccess'));
      setShowManualModal(false);
      setActiveTab('manual');
      loadInvoices();
    } catch (error) {
      console.error('Failed to create manual invoice:', error);
      toast.error(error.response?.data?.detail || t('invoices.manualFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('invoices.title')}</h1>
          <p className="text-gray-400">{t('invoices.subtitle')}</p>
        </div>
        <ExportButton reportType="invoices" />
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setActiveTab('auto')}
          className={`px-4 sm:px-6 py-3 rounded-lg font-medium transition-colors ${
            activeTab === 'auto'
              ? 'bg-primary-600 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          {t('invoices.autoMonthly')}
        </button>
        <button
          onClick={() => setActiveTab('manual')}
          className={`px-4 sm:px-6 py-3 rounded-lg font-medium transition-colors ${
            activeTab === 'manual'
              ? 'bg-primary-600 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          {t('invoices.manual')}
        </button>
        
        <div className="ml-auto flex gap-2 flex-wrap">
          {activeTab === 'auto' && (
            <button onClick={() => setConfirmGenerate(true)} className="btn-primary whitespace-nowrap">
              {t('invoices.generateMonthly')}
            </button>
          )}
          {activeTab === 'manual' && (
            <button onClick={openManualModal} className="btn-primary whitespace-nowrap">
              + {t('invoices.createManual')}
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div className="flex-1 min-w-[160px] max-w-[240px]">
          <label className="block text-gray-400 text-xs mb-1">{t('invoices.filterHouse')}</label>
          <div className="relative">
            <input
              type="text"
              value={filterHouseCode}
              onChange={(e) => setFilterHouseCode(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder={t('invoices.filterHousePlaceholder')}
              list="house-codes"
              className="w-full pl-3 pr-8 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <datalist id="house-codes">
              {houses.map(h => (
                <option key={h.id} value={h.house_code} />
              ))}
            </datalist>
            <Search size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
          </div>
        </div>

        <div className="min-w-[160px]">
          <label className="block text-gray-400 text-xs mb-1">{t('common.status')}</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">{t('invoices.allStatuses')}</option>
            <option value="ISSUED">{t('status.pending')}</option>
            <option value="PAID">{t('status.paid')}</option>
            <option value="PARTIALLY_PAID">{t('status.partial')}</option>
            <option value="CREDITED">{t('invoices.statusCredited')}</option>
          </select>
        </div>

        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-500 transition-colors"
        >
          {t('common.search')}
        </button>

        {(filterHouseCode || filterStatus) && (
          <button
            onClick={handleClearFilters}
            className="px-3 py-2 text-gray-400 hover:text-white text-sm transition-colors flex items-center gap-1"
          >
            <X size={14} />
            {t('invoices.clearFilters')}
          </button>
        )}
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <SortableHeader label={t('invoices.house')} sortKey="house_code" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('invoices.cycle')} sortKey="billing_month" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('invoices.total')} sortKey="total" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('invoices.paid')} sortKey="paid" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('invoices.outstanding')} sortKey="outstanding" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.status')} sortKey="status" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('invoices.dueDate')} sortKey="due_date" sortConfig={sortConfig} onSort={requestSort} />
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonTable rows={5} cols={8} />
              ) : invoices.length === 0 ? (
                <EmptyState icon={<FileText size={32} />} colSpan={8} />
              ) : (
                paged.currentItems.map((inv) => {
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
                            {t('invoices.manual')}
                          </span>
                        )}
                      </td>
                      <td className="text-gray-300">
                        {inv.is_manual ? (
                          <span className="text-purple-400" title={inv.manual_reason}>
                            {inv.manual_reason?.substring(0, 30) || t('invoices.manual')}{inv.manual_reason?.length > 30 ? '...' : ''}
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
                      <td className="text-gray-300">{new Date(inv.due_date).toLocaleDateString('th-TH')}</td>
                      <td className="space-x-1">
                        {canApply && (
                          <button
                            onClick={(e) => handleApplyPayment(inv, e)}
                            className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-500 transition-colors"
                          >
                            {t('invoices.applyPayment')}
                          </button>
                        )}
                        {outstanding > 0 && (
                          <button
                            onClick={(e) => handleOpenCreditNote(inv, e)}
                            className="px-2 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-500 transition-colors"
                            title={t('invoices.creditNote')}
                          >
                            + {t('invoices.creditNote')}
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

      {/* Pagination */}
      {!loading && invoices.length > 0 && <Pagination {...paged} />}

      {/* Apply Payment Modal */}
      <ApplyPaymentModal
        isOpen={showApplyModal}
        onClose={() => setShowApplyModal(false)}
        invoice={selectedInvoice}
        onSuccess={handleApplySuccess}
      />

      {/* Invoice Detail Modal */}
      {showDetailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-white">{t('invoices.invoiceDetail')}</h2>
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

            <div className="p-6 overflow-y-auto max-h-[70vh]">
              {detailLoading ? (
                <div className="py-8 space-y-3">{Array.from({length:4}).map((_,i)=><SkeletonBlock key={i} className="h-4 w-full" />)}</div>
              ) : invoiceDetail ? (
                <>
                  <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-gray-400 text-sm">{t('invoices.total')}</div>
                        <div className="text-white font-bold text-lg">
                          ฿{invoiceDetail.total_amount?.toLocaleString() || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-sm">{t('invoices.paid')}</div>
                        <div className="text-green-400 font-bold text-lg">
                          ฿{invoiceDetail.paid_amount?.toLocaleString() || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-sm">{t('invoices.outstanding')}</div>
                        <div className="text-yellow-400 font-bold text-lg">
                          ฿{invoiceDetail.outstanding_amount?.toLocaleString() || 0}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-400 text-sm">{t('common.status')}</div>
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

                  {(invoiceDetail.outstanding_amount || 0) > 0 && (
                    <div className="mb-6 flex flex-col sm:flex-row gap-3">
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
                        {t('invoices.applyPayment')}
                      </button>
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
                        + {t('invoices.creditNote')}
                      </button>
                    </div>
                  )}

                  <div>
                    <h3 className="text-white font-medium mb-3">{t('invoices.paymentHistory')}</h3>
                    {payments.length === 0 ? (
                      <div className="text-center py-6 text-gray-400 bg-slate-700/30 rounded-lg">
                        {t('common.noData')}
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {payments.map((payment, idx) => (
                          <div key={idx} className="bg-slate-700/50 rounded-lg p-4">
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="text-green-400 font-bold">
                                    ฿{payment.amount?.toLocaleString()}
                                  </span>
                                  {payment.payin ? (
                                    <>
                                      <span className="text-gray-500">—</span>
                                      <span className="text-gray-300 text-sm">
                                        {t('invoices.payinRef')} #{payment.payin.id}
                                      </span>
                                      {payment.payin.house_code && (
                                        <span className="text-gray-500 text-sm">
                                          ({t('invoices.house')} {payment.payin.house_code})
                                        </span>
                                      )}
                                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                        payment.payin.status === 'ACCEPTED' ? 'bg-green-500/20 text-green-400' :
                                        payment.payin.status === 'SUBMITTED' ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-gray-500/20 text-gray-400'
                                      }`}>
                                        {payment.payin.status === 'ACCEPTED' ? t('status.approved') :
                                         payment.payin.status === 'SUBMITTED' ? t('status.pending') :
                                         payment.payin.status}
                                      </span>
                                    </>
                                  ) : (
                                    <span className="text-gray-500 text-sm">
                                      Ledger #{payment.ledger?.id}
                                    </span>
                                  )}
                                </div>
                                {payment.payin?.transfer_date && (
                                  <div className="text-gray-500 text-xs mt-1">
                                    {t('invoices.transferDate')}: {new Date(payment.payin.transfer_date).toLocaleDateString('th-TH')}
                                  </div>
                                )}
                                {payment.payin?.slip_url && (
                                  <button
                                    onClick={() => setSlipViewUrl(payinsAPI.slipUrl(payment.payin.id))}
                                    className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 bg-blue-600/20 text-blue-400 text-xs rounded-lg hover:bg-blue-600/30 transition-colors"
                                  >
                                    <Image size={12} />
                                    {t('invoices.viewSlip')}
                                  </button>
                                )}
                                {payment.note && (
                                  <div className="text-gray-500 text-sm mt-1">
                                    {t('common.notes')}: {payment.note}
                                  </div>
                                )}
                              </div>
                              <div className="text-gray-400 text-sm text-right shrink-0 ml-3">
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
                <div className="text-center py-8 text-gray-400">{t('common.noData')}</div>
              )}
            </div>

            <div className="px-6 py-4 border-t border-slate-700 flex justify-end">
              <button
                onClick={() => setShowDetailModal(false)}
                className="px-6 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 transition-colors"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Invoice Modal */}
      {showManualModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-white">{t('invoices.createManual')}</h2>
              </div>
              <button
                onClick={() => setShowManualModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleManualSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  {t('invoices.house')} <span className="text-red-400">*</span>
                </label>
                <select
                  value={manualForm.house_id}
                  onChange={(e) => setManualForm({ ...manualForm, house_id: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                >
                  <option value="">-- {t('members.selectHouse')} --</option>
                  {houses.map((house) => (
                    <option key={house.id} value={house.id}>
                      {house.house_code} - {house.owner_name || '-'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  {t('common.amount')} (บาท) <span className="text-red-400">*</span>
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

              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  {t('common.description')} <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={manualForm.description}
                  onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder={t('invoices.descriptionPlaceholder')}
                  required
                />
              </div>

              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  {t('invoices.dueDate')} <span className="text-red-400">*</span>
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

              <div>
                <label className="block text-gray-300 text-sm font-medium mb-2">
                  {t('common.notes')} ({t('common.optional')})
                </label>
                <textarea
                  value={manualForm.note}
                  onChange={(e) => setManualForm({ ...manualForm, note: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={2}
                  placeholder={t('common.notesPlaceholder')}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowManualModal(false)}
                  className="flex-1 px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 transition-colors"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 transition-colors disabled:opacity-50"
                >
                  {submitting ? t('common.creating') : t('invoices.createManual')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Credit Note Modal */}
      <CreditNoteModal
        isOpen={showCreditNoteModal}
        onClose={() => setShowCreditNoteModal(false)}
        invoice={creditNoteInvoice}
        onSuccess={handleCreditNoteSuccess}
      />

      {/* Slip Lightbox */}
      {slipViewUrl && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-[60] p-4"
          onClick={() => setSlipViewUrl(null)}
        >
          <div className="relative max-w-2xl max-h-[90vh]" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setSlipViewUrl(null)}
              className="absolute -top-3 -right-3 w-8 h-8 bg-slate-700 text-white rounded-full flex items-center justify-center hover:bg-slate-600 z-10"
            >
              ×
            </button>
            <img
              src={slipViewUrl}
              alt="Slip"
              className="max-h-[85vh] rounded-lg shadow-2xl object-contain"
            />
          </div>
        </div>
      )}

      {/* Generate Monthly Confirm Modal */}
      <ConfirmModal
        open={confirmGenerate}
        title={t('invoices.confirmGenerate')}
        message={t('invoices.confirmGenerateMsg')}
        variant="info"
        confirmText={t('common.create')}
        onConfirm={handleGenerateMonthly}
        onCancel={() => setConfirmGenerate(false)}
      />
    </div>
    </AdminPageWrapper>
  );
}
