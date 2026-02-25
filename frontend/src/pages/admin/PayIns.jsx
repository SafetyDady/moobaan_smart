import { useState, useEffect } from 'react';
import { CreditCard, Search } from 'lucide-react';
import { payinsAPI, bankReconciliationAPI } from '../../api/client';
import { useRole } from '../../contexts/RoleContext';
import ConfirmModal from '../../components/ConfirmModal';
import { useToast } from '../../components/Toast';
import { SkeletonTable } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';
import Pagination, { usePagination } from '../../components/Pagination';
import SortableHeader, { useSort } from '../../components/SortableHeader';
import EmptyState from '../../components/EmptyState';
import AdminPageWrapper from '../../components/AdminPageWrapper';
import ExportButton from '../../components/ExportButton';


export default function PayIns() {
  const { isAdmin, isAccounting, currentRole, loading: roleLoading } = useRole();
  
  // Allow super_admin and accounting roles to manage pay-ins
  const canManagePayins = currentRole === 'super_admin' || currentRole === 'accounting';
  
  const [payins, setPayins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('PENDING'); // Default to PENDING for review queue
  const [selectedPayin, setSelectedPayin] = useState(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showMatchModal, setShowMatchModal] = useState(false);
  const [showReverseModal, setShowReverseModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [deleteReason, setDeleteReason] = useState('');
  const [reverseReason, setReverseReason] = useState('');
  const [bankTransactions, setBankTransactions] = useState([]);
  const [loadingTransactions, setLoadingTransactions] = useState(false);
  const [matchDebugInfo, setMatchDebugInfo] = useState(null);
  const [posting, setPosting] = useState(null); // payin id currently being posted
  const [confirmUnmatch, setConfirmUnmatch] = useState({ open: false, payin: null });
  const [confirmPost, setConfirmPost] = useState({ open: false, payin: null });
  const toast = useToast();

  // Pagination
  const { sortConfig, requestSort, sortedData: sortedPayins } = useSort(payins);
  const paged = usePagination(sortedPayins);

  useEffect(() => {
    if (!roleLoading) {
      loadPayins();
    }
  }, [statusFilter, roleLoading]);

  const loadPayins = async () => {
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const response = await payinsAPI.list(params);
      setPayins(response.data);
    } catch (error) {
      console.error('Failed to load pay-ins:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadBankTransactions = async (payin) => {
    setLoadingTransactions(true);
    try {
      // Use the new Pay-in Centric endpoint that returns pre-filtered candidates
      const response = await bankReconciliationAPI.getCandidatesForPayin(payin.id);
      const candidates = response.data.candidates || [];
      
      setBankTransactions(candidates);
      
      // Log debug info to console for troubleshooting
      if (response.data.debug) {
        console.log('[Match Debug]', JSON.stringify(response.data.debug, null, 2));
        setMatchDebugInfo(response.data.debug);
      }
    } catch (error) {
      console.error('Failed to load candidate bank transactions:', error);
      toast.error(error.response?.data?.detail || t('payins.loadBankFailed'));
    } finally {
      setLoadingTransactions(false);
    }
  };

  const handleMatch = async (txnId) => {
    try {
      await bankReconciliationAPI.matchTransaction(txnId, selectedPayin.id);
      toast.success(t('payins.matchSuccess'));
      setShowMatchModal(false);
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to match:', error);
      toast.error(error.response?.data?.detail || t('payins.matchFailed'));
    }
  };

  const handleUnmatch = async (payin) => {
    try {
      await bankReconciliationAPI.unmatchTransaction(payin.matched_statement_txn_id);
      toast.success(t('payins.unmatchSuccess'));
      loadPayins();
    } catch (error) {
      console.error('Failed to unmatch:', error);
      toast.error(error.response?.data?.detail || t('payins.unmatchFailed'));
    }
  };

  const openMatchModal = async (payin) => {
    setSelectedPayin(payin);
    setShowMatchModal(true);
    setMatchDebugInfo(null);
    await loadBankTransactions(payin);
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      toast.warning(t('payins.rejectReasonRequired'));
      return;
    }
    try {
      await payinsAPI.reject(selectedPayin.id, rejectReason);
      toast.success(t('payins.rejectSuccess'));
      setShowRejectModal(false);
      setRejectReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to reject:', error);
      toast.error(error.response?.data?.detail || t('payins.rejectFailed'));
    }
  };

  const handleConfirmAndPost = async (payin) => {
    setPosting(payin.id);
    try {
      const result = await bankReconciliationAPI.confirmAndPost(payin.matched_statement_txn_id);
      const data = result.data;
      const allocCount = data.allocations?.length || 0;
      if (data.status === 'already_posted') {
        toast.info(t('payins.alreadyPosted'));
      } else {
        toast.success(`${t('payins.postSuccess')} #${data.income_transaction_id} / ${allocCount} ${t('payins.invoicesAllocated')}`);
      }
      loadPayins();
    } catch (error) {
      console.error('Failed to confirm & post:', error);
      const detail = error.response?.data?.detail;
      if (typeof detail === 'object' && detail.code === 'AMBIGUOUS') {
        toast.warning(detail.message);
      } else {
        toast.error(typeof detail === 'string' ? detail : t('payins.postFailed'));
      }
    } finally {
      setPosting(null);
    }
  };

  const handleReverse = async () => {
    if (!reverseReason.trim()) {
      toast.warning(t('payins.reverseReasonRequired'));
      return;
    }
    try {
      const result = await bankReconciliationAPI.reverseTransaction(
        selectedPayin.matched_statement_txn_id,
        reverseReason
      );
      toast.success(`${t('payins.reverseSuccess')}: ${result.data.message}`);
      setShowReverseModal(false);
      setReverseReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to reverse:', error);
      toast.error(error.response?.data?.detail || t('payins.reverseFailed'));
    }
  };

  const handleDeleteSubmission = async () => {
    if (!deleteReason.trim()) {
      toast.warning(t('payins.deleteReasonRequired'));
      return;
    }
    try {
      await payinsAPI.cancel(selectedPayin.id, deleteReason);
      toast.success(t('payins.deleteSuccess'));
      setShowDeleteModal(false);
      setDeleteReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to delete submission:', error);
      toast.error(error.response?.data?.detail || t('payins.deleteFailed'));
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      PENDING: 'badge-warning',
      SUBMITTED: 'badge-warning',
      REJECTED_NEEDS_FIX: 'badge-danger',
      ACCEPTED: 'badge-success',
      REJECTED: 'badge-danger',
    };
    return badges[status] || 'badge-gray';
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('payins.title')}</h1>
          <p className="text-gray-400">{t('payins.subtitle')}</p>
        </div>
        <ExportButton reportType="payins" />
      </div>

      {/* Filter */}
      <div className="card p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">{t('payins.statusFilter')}</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-full"
            >
              <option value="">{t('payins.allStatus')}</option>
              <option value="SUBMITTED">{t('payins.needsReview')}</option>
              <option value="PENDING">{t('payins.pendingReview')}</option>
              <option value="REJECTED_NEEDS_FIX">{t('payins.rejectedNeedsFix')}</option>
              <option value="ACCEPTED">{t('payins.accepted')}</option>
              <option value="REJECTED">{t('payins.rejected')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <SortableHeader label={t('payins.house')} sortKey="house_number" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('payins.amount')} sortKey="amount" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('payins.transferDate')} sortKey="transfer_date" sortConfig={sortConfig} onSort={requestSort} />
                <th>{t('payins.slip')}</th>
                <th>{t('payins.matchBank')}</th>
                <SortableHeader label={t('common.status')} sortKey="status" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.createdAt')} sortKey="created_at" sortConfig={sortConfig} onSort={requestSort} />
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonTable rows={5} cols={8} />
              ) : payins.length === 0 ? (
                <EmptyState
                  icon={<CreditCard size={32} />}
                  colSpan={8}
                  isFiltered={!!statusFilter}
                  onClearFilters={() => setStatusFilter('')}
                />
              ) : (
                paged.currentItems.map((payin) => (
                  <tr key={payin.id}>
                    <td className="font-medium text-white">{payin.house_number}</td>
                    <td className="text-primary-400 font-semibold">฿{payin.amount.toLocaleString('th-TH')}</td>
                    <td className="text-gray-300">
                      {new Date(payin.transfer_date).toLocaleDateString('th-TH')}
                      <br />
                      <span className="text-sm text-gray-400">
                        {String(payin.transfer_hour).padStart(2, '0')}:{String(payin.transfer_minute).padStart(2, '0')}
                      </span>
                    </td>
                    <td>
                      {payin.slip_image_url ? (
                        <button
                          onClick={() => window.open(payinsAPI.slipUrl(payin.id), '_blank')}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          {t('payins.viewSlip')}
                        </button>
                      ) : (
                        <span className="text-gray-500 text-sm">{t('payins.noSlip')}</span>
                      )}
                    </td>
                    <td>
                      {payin.is_matched ? (
                        <span className="badge badge-success text-xs">{t('payins.matchedBadge')}</span>
                      ) : (
                        <span className="badge badge-warning text-xs">{t('payins.unmatchedBadge')}</span>
                      )}
                      {/* Posting status badge */}
                      {payin.posting_status === 'POSTED' && (
                        <span className="badge bg-green-700 text-green-100 text-xs ml-1">{t('payins.postedBadge')}</span>
                      )}
                      {payin.posting_status === 'REVERSED' && (
                        <span className="badge bg-red-700 text-red-100 text-xs ml-1">{t('payins.reversedBadge')}</span>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadge(payin.status)}`}>
                        {payin.status}
                      </span>
                      {payin.reject_reason && (
                        <div className="text-xs text-red-400 mt-1 max-w-xs truncate" title={payin.reject_reason}>
                          {payin.reject_reason}
                        </div>
                      )}
                    </td>
                    <td className="text-gray-400 text-sm">
                      {new Date(payin.created_at).toLocaleDateString('th-TH')}
                    </td>
                    <td>
                      <div className="flex gap-2 flex-wrap">
                        {/* View Slip - always visible */}
                        {payin.slip_image_url && (
                          <button
                            onClick={() => window.open(payinsAPI.slipUrl(payin.id), '_blank')}
                            className="text-blue-400 hover:text-blue-300 text-sm px-2 py-1 border border-blue-400 rounded"
                          >
                            {t('payins.viewSlipFull')}
                          </button>
                        )}
                        
                        {/* Actions for PENDING or SUBMITTED status */}
                        {(payin.status === 'PENDING' || payin.status === 'SUBMITTED') && canManagePayins && (
                          <>
                            {/* Match/Unmatch button */}
                            {!payin.is_matched ? (
                              <button
                                onClick={() => openMatchModal(payin)}
                                className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded"
                              >
                                {t('payins.matchBtn')}
                              </button>
                            ) : (
                              <button
                                onClick={() => setConfirmUnmatch({ open: true, payin })}
                                className="bg-orange-600 hover:bg-orange-700 text-white text-sm px-3 py-1 rounded"
                              >
                                {t('payins.unmatchBtn')}
                              </button>
                            )}
                            
                            {/* Confirm & Post button — replaces old Accept (Phase P1) */}
                            <button
                              onClick={() => setConfirmPost({ open: true, payin })}
                              disabled={!payin.is_matched || posting === payin.id}
                              className={`text-sm px-3 py-1 rounded font-medium ${
                                payin.is_matched && posting !== payin.id
                                  ? 'bg-green-600 hover:bg-green-700 text-white' 
                                  : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                              }`}
                              title={!payin.is_matched ? t('payins.mustMatchFirst') : t('payins.confirmAndPostTooltip')}
                            >
                              {posting === payin.id ? t('payins.posting') : t('payins.confirmAndPost')}
                            </button>
                            <button
                              onClick={() => {
                                setSelectedPayin(payin);
                                setShowRejectModal(true);
                              }}
                              className="btn-danger text-sm px-3 py-1"
                            >
                              {t('payins.rejectBtn')}
                            </button>
                            <button
                              onClick={() => {
                                setSelectedPayin(payin);
                                setShowDeleteModal(true);
                              }}
                              className="btn-secondary text-sm px-3 py-1"
                            >
                              {t('payins.deleteBtn')}
                            </button>
                          </>
                        )}
                        
                        {/* Delete option for REJECTED status */}
                        {payin.status === 'REJECTED' && canManagePayins && (
                          <button
                            onClick={() => {
                              setSelectedPayin(payin);
                              setShowDeleteModal(true);
                            }}
                            className="btn-secondary text-sm px-3 py-1"
                          >
                            {t('payins.deleteBtn')}
                          </button>
                        )}

                        {/* REJECTED_NEEDS_FIX - waiting for resident to fix and resubmit */}
                        {payin.status === 'REJECTED_NEEDS_FIX' && canManagePayins && (
                          <div className="flex items-center gap-2">
                            <span className="text-orange-400 text-sm" title={t('payins.waitingResidentFixTooltip')}>
                              {t('payins.waitingResidentFix')}
                            </span>
                            <button
                              onClick={() => {
                                setSelectedPayin(payin);
                                setShowDeleteModal(true);
                              }}
                              className="btn-secondary text-sm px-3 py-1"
                            >
                              {t('payins.deleteBtn')}
                            </button>
                          </div>
                        )}
                        
                        {/* Status indicators */}
                        {payin.status === 'ACCEPTED' && (
                          <div className="flex items-center gap-2">
                            <span className="text-green-400 text-sm">{t('payins.accountPosted')}</span>
                            {canManagePayins && payin.matched_statement_txn_id && (
                              <button
                                onClick={() => {
                                  setSelectedPayin(payin);
                                  setShowReverseModal(true);
                                }}
                                className="bg-red-600 hover:bg-red-700 text-white text-xs px-2 py-1 rounded"
                                title={t("payins.reverse")}
                              >
                                {t('payins.reverseBtn')}
                              </button>
                            )}
                          </div>
                        )}
                        {payin.status === 'REJECTED' && (
                          <span className="text-red-400 text-sm">{t('payins.residentCanResubmit')}</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {!loading && payins.length > 0 && <Pagination {...paged} />}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">{t('payins.rejectModalTitle')}</h2>
            <p className="text-gray-300 mb-2">
              {t('payins.reverseHouse')}: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              {t('payins.reverseAmount')}: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString('th-TH')}</span>
            </p>
            <div className="bg-orange-900 bg-opacity-30 border border-orange-600 rounded p-3 mb-4">
              <p className="text-orange-400 text-sm">
                {t('payins.rejectWarning')}
              </p>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                {t('payins.rejectReasonLabel')}
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder={t('payins.rejectReasonPlaceholder')}
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleReject} className="btn-danger flex-1">
                {t('payins.rejectBtn')}
              </button>
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReason('');
                  setSelectedPayin(null);
                }}
                className="btn-secondary flex-1"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Submission Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">{t('payins.deleteModalTitle')}</h2>
            <p className="text-gray-300 mb-2">
              {t('payins.reverseHouse')}: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              {t('payins.reverseAmount')}: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString('th-TH')}</span>
            </p>
            <div className="bg-yellow-900 bg-opacity-30 border border-yellow-600 rounded p-3 mb-4">
              <p className="text-yellow-400 text-sm">
                {t('payins.deleteWarning')}
              </p>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                {t('payins.deleteReasonLabel')}
              </label>
              <textarea
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder={t('payins.deleteReasonPlaceholder')}
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleDeleteSubmission} className="btn-danger flex-1">
                {t('payins.deleteBtn')}
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteReason('');
                  setSelectedPayin(null);
                }}
                className="btn-secondary flex-1"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Match Modal */}
      {showMatchModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="card p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-white mb-4">{t('payins.matchBank')}</h2>
            
            {/* Pay-in Details */}
            <div className="bg-blue-900 bg-opacity-20 border border-blue-600 rounded p-4 mb-4">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">{t('payins.payinDetails')}</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-400">{t('payins.house')}:</div>
                <div className="text-white font-medium">{selectedPayin?.house_number}</div>
                <div className="text-gray-400">{t('payins.amount')}:</div>
                <div className="text-primary-400 font-semibold">฿{selectedPayin?.amount?.toLocaleString('th-TH')}</div>
                <div className="text-gray-400">{t('payins.transferTime')}:</div>
                <div className="text-white">
                  {selectedPayin && new Date(selectedPayin.transfer_date).toLocaleDateString('th-TH')} {' '}
                  {selectedPayin && String(selectedPayin.transfer_hour).padStart(2, '0')}:{String(selectedPayin.transfer_minute).padStart(2, '0')}
                </div>
              </div>
            </div>

            {/* Bank Transactions List */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white mb-3">
                {t('payins.selectBankTxn')}
                {bankTransactions.length > 0 && (
                  <span className="text-sm text-gray-400 ml-2">
                    ({bankTransactions.length} {t('payins.matchedItems')})
                  </span>
                )}
              </h3>
              
              {loadingTransactions ? (
                <div className="text-center py-8 text-gray-400">{t('common.loading')}</div>
              ) : bankTransactions.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-yellow-400 mb-2">{t('payins.noMatchFound')}</p>
                  <p className="text-sm text-gray-400 mb-2">
                    {t('payins.matchConditionSummary')} ฿{selectedPayin?.amount?.toLocaleString('th-TH')}
                  </p>
                  <p className="text-xs text-gray-500">
                    {t('payins.matchConditionDetail')}
                  </p>
                  {/* Debug info for troubleshooting */}
                  {matchDebugInfo && (
                    <div className="mt-4 text-left bg-gray-800 rounded p-3 text-xs font-mono">
                      <p className="text-gray-300 mb-1"><Search size={14} className="inline mr-1" />Debug Info:</p>
                      <p className="text-gray-400">{t('payins.payinTimeUtc')}: {matchDebugInfo.payin_time_utc}</p>
                      <p className="text-gray-400">{t('payins.payinTimezone')}: {matchDebugInfo.payin_time_tzinfo}</p>
                      <p className="text-gray-400">{t('payins.unmatchedCredits')}: {matchDebugInfo.total_unmatched_credit}</p>
                      <p className="text-gray-400">{t('payins.amountMatches')}: {matchDebugInfo.amount_matches}</p>
                      {matchDebugInfo.near_misses?.length > 0 && (
                        <div className="mt-2">
                          <p className="text-yellow-400">{t('payins.nearMisses')}</p>
                          {matchDebugInfo.near_misses.map((nm, i) => (
                            <p key={i} className="text-gray-400 ml-2">
                              txn {nm.txn_id}: bank_time={nm.bank_time_utc}, diff={nm.time_diff_seconds}s ({nm.time_diff_hours}h), reason={nm.reason}
                            </p>
                          ))}
                        </div>
                      )}
                      {matchDebugInfo.errors?.length > 0 && (
                        <div className="mt-2">
                          <p className="text-red-400">{t('payins.errorOccurred')}</p>
                          {matchDebugInfo.errors.map((e, i) => (
                            <p key={i} className="text-red-300 ml-2">txn {e.txn_id}: {e.error}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {bankTransactions.map((txn) => {
                    // Use time_diff_seconds from backend response (already calculated)
                    const timeDiffSeconds = txn.time_diff_seconds || 0;
                    const amountDiff = txn.amount_diff || 0;
                    const isPerfectMatch = txn.is_perfect_match || false;
                    
                    const txnDate = new Date(txn.effective_at);
                    
                    return (
                      <div 
                        key={txn.id} 
                        className={`border rounded p-3 hover:bg-gray-800 transition ${
                          isPerfectMatch ? 'border-green-500 bg-green-900 bg-opacity-10' : 'border-gray-600'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <div className="text-white font-medium mb-1">
                              ฿{parseFloat(txn.credit).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 
                              {isPerfectMatch && <span className="ml-2 text-green-400 text-xs font-semibold">{t('payins.perfectMatch')}</span>}
                              {amountDiff > 0 && <span className="ml-2 text-yellow-400 text-xs">{t('payins.amountDiff')}: ฿{amountDiff.toFixed(2)}</span>}
                            </div>
                            <div className="text-sm text-gray-400">
                              {txnDate.toLocaleDateString('th-TH')} {txnDate.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                              <span className="ml-2 text-green-300">
                                ({timeDiffSeconds < 60 ? `${Math.floor(timeDiffSeconds)}s` : `${Math.floor(timeDiffSeconds / 60)}m ${Math.floor(timeDiffSeconds % 60)}s`} {t('payins.timeDiff')})
                              </span>
                            </div>
                            {txn.description && (
                              <div className="text-xs text-gray-500 mt-1">{txn.description}</div>
                            )}
                            {txn.channel && (
                              <div className="text-xs text-gray-600 mt-1">{t('payins.channelLabel')}: {txn.channel}</div>
                            )}
                            <div className="text-xs text-gray-600 mt-1">{t('payins.txnId')}: {txn.id.substring(0, 8)}...</div>
                          </div>
                          <button
                            onClick={() => handleMatch(txn.id)}
                            className={`px-4 py-2 rounded text-sm font-medium whitespace-nowrap ${
                              isPerfectMatch 
                                ? 'bg-green-600 hover:bg-green-700 text-white' 
                                : 'bg-blue-600 hover:bg-blue-700 text-white'
                            }`}
                            title={`${t('payins.matchBtn')} (${Math.floor(timeDiffSeconds)}s)`}
                          >
                            {isPerfectMatch ? t('payins.matchPerfect') : t('payins.matchWithDiff')}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Close Button */}
            <div className="flex justify-end">
              <button
                onClick={() => {
                  setShowMatchModal(false);
                  setSelectedPayin(null);
                  setBankTransactions([]);
                }}
                className="btn-secondary px-6"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Unmatch Confirm Modal */}
      <ConfirmModal
        open={confirmUnmatch.open}
        title={t("payins.unmatch")}
        message={t('payins.unmatchConfirmMsg')}
        variant="warning"
        confirmText={t('payins.unmatchConfirmBtn')}
        onConfirm={() => handleUnmatch(confirmUnmatch.payin)}
        onCancel={() => setConfirmUnmatch({ open: false, payin: null })}
      />

      {/* Confirm & Post Modal */}
      <ConfirmModal
        open={confirmPost.open}
        title={t("payins.post")}
        message={confirmPost.payin ? `${t('payins.confirmPostMsg')} ฿${confirmPost.payin.amount} ${t('payins.fromHouse')} ${confirmPost.payin.house_number}?\n\n${t('payins.confirmPostDetail')}` : ''}
        variant="info"
        confirmText={t('payins.confirmAndPostBtn')}
        onConfirm={() => { if (confirmPost.payin) handleConfirmAndPost(confirmPost.payin); }}
        onCancel={() => setConfirmPost({ open: false, payin: null })}
      />

      {/* Reverse Modal (Phase P1) */}
      {showReverseModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">{t('payins.reverseTitle')}</h2>
            <p className="text-gray-300 mb-2">
              {t('payins.reverseHouse')}: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              {t('payins.reverseAmount')}: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString('th-TH')}</span>
            </p>
            <div className="bg-red-900 bg-opacity-30 border border-red-600 rounded p-3 mb-4">
              <p className="text-red-400 text-sm">
                {t('payins.reverseWarning')}
              </p>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                {t('payins.reverseReasonLabel')}
              </label>
              <textarea
                value={reverseReason}
                onChange={(e) => setReverseReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder={t('payins.reverseReasonPlaceholder')}
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleReverse} className="btn-danger flex-1">
                {t('payins.reverseBtn')}
              </button>
              <button
                onClick={() => {
                  setShowReverseModal(false);
                  setReverseReason('');
                  setSelectedPayin(null);
                }}
                className="btn-secondary flex-1"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </AdminPageWrapper>
  );
}
