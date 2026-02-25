import { useState, useEffect } from 'react';
import { payinsAPI, bankReconciliationAPI } from '../../api/client';
import { useRole } from '../../contexts/RoleContext';
import ConfirmModal from '../../components/ConfirmModal';
import { useToast } from '../../components/Toast';
import { SkeletonTable } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';

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
      toast.error(error.response?.data?.detail || 'Failed to load candidate bank transactions');
    } finally {
      setLoadingTransactions(false);
    }
  };

  const handleMatch = async (txnId) => {
    try {
      await bankReconciliationAPI.matchTransaction(txnId, selectedPayin.id);
      toast.success('จับคู่กับรายการธนาคารสำเร็จ');
      setShowMatchModal(false);
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to match:', error);
      toast.error(error.response?.data?.detail || 'Failed to match transaction');
    }
  };

  const handleUnmatch = async (payin) => {
    try {
      await bankReconciliationAPI.unmatchTransaction(payin.matched_statement_txn_id);
      toast.success('Unmatch สำเร็จ');
      loadPayins();
    } catch (error) {
      console.error('Failed to unmatch:', error);
      toast.error(error.response?.data?.detail || 'Failed to unmatch');
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
      toast.warning('กรุณาระบุเหตุผลในการปฏิเสธ');
      return;
    }
    try {
      await payinsAPI.reject(selectedPayin.id, rejectReason);
      toast.success('ปฏิเสธรายการสำเร็จ');
      setShowRejectModal(false);
      setRejectReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to reject:', error);
      toast.error(error.response?.data?.detail || 'Failed to reject pay-in');
    }
  };

  const handleConfirmAndPost = async (payin) => {
    setPosting(payin.id);
    try {
      const result = await bankReconciliationAPI.confirmAndPost(payin.matched_statement_txn_id);
      const data = result.data;
      const allocCount = data.allocations?.length || 0;
      if (data.status === 'already_posted') {
        toast.info('รายการนี้ถูก Post ไปแล้ว (idempotent)');
      } else {
        toast.success(`Posted สำเร็จ! Ledger #${data.income_transaction_id} / จัดสรร ${allocCount} ใบแจ้งหนี้`);
      }
      loadPayins();
    } catch (error) {
      console.error('Failed to confirm & post:', error);
      const detail = error.response?.data?.detail;
      if (typeof detail === 'object' && detail.code === 'AMBIGUOUS') {
        toast.warning(detail.message);
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Failed to confirm & post');
      }
    } finally {
      setPosting(null);
    }
  };

  const handleReverse = async () => {
    if (!reverseReason.trim()) {
      toast.warning('กรุณาระบุเหตุผลในการ Reverse');
      return;
    }
    try {
      const result = await bankReconciliationAPI.reverseTransaction(
        selectedPayin.matched_statement_txn_id,
        reverseReason
      );
      toast.success(`Reversed สำเร็จ: ${result.data.message}`);
      setShowReverseModal(false);
      setReverseReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to reverse:', error);
      toast.error(error.response?.data?.detail || 'Failed to reverse');
    }
  };

  const handleDeleteSubmission = async () => {
    if (!deleteReason.trim()) {
      toast.warning('กรุณาระบุเหตุผลในการลบ');
      return;
    }
    try {
      await payinsAPI.cancel(selectedPayin.id, deleteReason);
      toast.success('ลบรายการส่งเงินสำเร็จ');
      setShowDeleteModal(false);
      setDeleteReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to delete submission:', error);
      toast.error(error.response?.data?.detail || 'ไม่สามารถลบรายการส่งเงินได้');
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
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('payins.title')}</h1>
        <p className="text-gray-400">{t('payins.subtitle')}</p>
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
                <th>{t('payins.house')}</th>
                <th>{t('payins.amount')}</th>
                <th>{t('payins.transferDate')}</th>
                <th>{t('payins.slip')}</th>
                <th>{t('payins.matchBank')}</th>
                <th>{t('common.status')}</th>
                <th>{t('common.createdAt')}</th>
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonTable rows={5} cols={8} />
              ) : payins.length === 0 ? (
                <tr><td colSpan="8" className="text-center py-8 text-gray-400">
                  {(statusFilter === 'PENDING' || statusFilter === 'SUBMITTED') ? 'No pay-ins pending review' : 'No pay-ins found'}
                </td></tr>
              ) : (
                payins.map((payin) => (
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
                          📎 View
                        </button>
                      ) : (
                        <span className="text-gray-500 text-sm">{t('payins.noSlip')}</span>
                      )}
                    </td>
                    <td>
                      {payin.is_matched ? (
                        <span className="badge badge-success text-xs">✓ Matched</span>
                      ) : (
                        <span className="badge badge-warning text-xs">○ Unmatched</span>
                      )}
                      {/* Posting status badge */}
                      {payin.posting_status === 'POSTED' && (
                        <span className="badge bg-green-700 text-green-100 text-xs ml-1">📌 Posted</span>
                      )}
                      {payin.posting_status === 'REVERSED' && (
                        <span className="badge bg-red-700 text-red-100 text-xs ml-1">↩️ Reversed</span>
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
                            👁️ View Slip
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
                                🔗 Match
                              </button>
                            ) : (
                              <button
                                onClick={() => setConfirmUnmatch({ open: true, payin })}
                                className="bg-orange-600 hover:bg-orange-700 text-white text-sm px-3 py-1 rounded"
                              >
                                🔓 Unmatch
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
                              title={!payin.is_matched ? 'Must match with bank statement first' : 'Confirm & Post: Ledger + Invoice allocation'}
                            >
                              {posting === payin.id ? '⏳ Posting...' : '✅ Confirm & Post'}
                            </button>
                            <button
                              onClick={() => {
                                setSelectedPayin(payin);
                                setShowRejectModal(true);
                              }}
                              className="btn-danger text-sm px-3 py-1"
                            >
                              ✗ Reject
                            </button>
                            <button
                              onClick={() => {
                                setSelectedPayin(payin);
                                setShowDeleteModal(true);
                              }}
                              className="btn-secondary text-sm px-3 py-1"
                            >
                              🗑 Delete
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
                            🗑 Delete
                          </button>
                        )}

                        {/* REJECTED_NEEDS_FIX - waiting for resident to fix and resubmit */}
                        {payin.status === 'REJECTED_NEEDS_FIX' && canManagePayins && (
                          <div className="flex items-center gap-2">
                            <span className="text-orange-400 text-sm" title="ไม่สามารถจับคู่ได้จนกว่าลูกบ้านจะส่งใหม่">
                              ⏳ รอลูกบ้านแก้ไข
                            </span>
                            <button
                              onClick={() => {
                                setSelectedPayin(payin);
                                setShowDeleteModal(true);
                              }}
                              className="btn-secondary text-sm px-3 py-1"
                            >
                              🗑 Delete
                            </button>
                          </div>
                        )}
                        
                        {/* Status indicators */}
                        {payin.status === 'ACCEPTED' && (
                          <div className="flex items-center gap-2">
                            <span className="text-green-400 text-sm">✓ Ledger created</span>
                            {canManagePayins && payin.matched_statement_txn_id && (
                              <button
                                onClick={() => {
                                  setSelectedPayin(payin);
                                  setShowReverseModal(true);
                                }}
                                className="bg-red-600 hover:bg-red-700 text-white text-xs px-2 py-1 rounded"
                                title={t("payins.reverse")}
                              >
                                ↩️ Reverse
                              </button>
                            )}
                          </div>
                        )}
                        {payin.status === 'REJECTED' && (
                          <span className="text-red-400 text-sm">ลูกบ้านสามารถส่งใหม่ได้</span>
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

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">✗ ปฏิเสธรายการ (Reject Submission)</h2>
            <p className="text-gray-300 mb-2">
              บ้าน: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              ยอด: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString('th-TH')}</span>
            </p>
            <div className="bg-orange-900 bg-opacity-30 border border-orange-600 rounded p-3 mb-4">
              <p className="text-orange-400 text-sm">
                ⚠️ รายการจะถูกเปลี่ยนเป็น REJECTED — เก็บ record ไว้เพื่อ audit ไม่มีผลบัญชี
              </p>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                เหตุผลในการปฏิเสธ *
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder="เช่น ยอดเงินไม่ตรง, สลิปไม่ชัด, วันที่ไม่ถูกต้อง..."
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleReject} className="btn-danger flex-1">
                ✗ Reject
              </button>
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReason('');
                  setSelectedPayin(null);
                }}
                className="btn-secondary flex-1"
              >
                ยกเลิก
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Submission Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">🗑 ลบรายการส่งเงิน (Delete Submission)</h2>
            <p className="text-gray-300 mb-2">
              บ้าน: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              ยอด: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString('th-TH')}</span>
            </p>
            <div className="bg-yellow-900 bg-opacity-30 border border-yellow-600 rounded p-3 mb-4">
              <p className="text-yellow-400 text-sm">
                ⚠️ ระบบจะลบรายการส่งเงินนี้ออก — ไม่มีผลต่อบัญชี เพราะยังไม่ได้ Confirm & Post
              </p>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                เหตุผลในการลบ *
              </label>
              <textarea
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder="เช่น ข้อมูลทดสอบ, ส่งซ้ำ, ยอดไม่ตรง..."
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleDeleteSubmission} className="btn-danger flex-1">
                🗑 Delete
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteReason('');
                  setSelectedPayin(null);
                }}
                className="btn-secondary flex-1"
              >
                ยกเลิก
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
                Select Matching Bank Transaction
                {bankTransactions.length > 0 && (
                  <span className="text-sm text-gray-400 ml-2">
                    ({bankTransactions.length} candidates - Amount exact, Time ±1 min)
                  </span>
                )}
              </h3>
              
              {loadingTransactions ? (
                <div className="text-center py-8 text-gray-400">{t('common.loading')}</div>
              ) : bankTransactions.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-yellow-400 mb-2">⚠️ No matching bank transactions found</p>
                  <p className="text-sm text-gray-400 mb-2">
                    Matching criteria: Amount exactly ฿{selectedPayin?.amount?.toLocaleString('th-TH')}, Time within ±1 minute
                  </p>
                  <p className="text-xs text-gray-500">
                    Check if: (1) Bank statement imported, (2) Amount matches exactly, (3) Time within ±1 minute of transfer_datetime
                  </p>
                  {/* Debug info for troubleshooting */}
                  {matchDebugInfo && (
                    <div className="mt-4 text-left bg-gray-800 rounded p-3 text-xs font-mono">
                      <p className="text-gray-300 mb-1">🔍 Debug Info:</p>
                      <p className="text-gray-400">เวลาชำระ (UTC): {matchDebugInfo.payin_time_utc}</p>
                      <p className="text-gray-400">โซนเวลา: {matchDebugInfo.payin_time_tzinfo}</p>
                      <p className="text-gray-400">รายการเครดิตที่ยังไม่จับคู่: {matchDebugInfo.total_unmatched_credit}</p>
                      <p className="text-gray-400">จำนวนที่ตรงกัน: {matchDebugInfo.amount_matches}</p>
                      {matchDebugInfo.near_misses?.length > 0 && (
                        <div className="mt-2">
                          <p className="text-yellow-400">รายการใกล้เคียง (จำนวนตรง เวลาต่าง):</p>
                          {matchDebugInfo.near_misses.map((nm, i) => (
                            <p key={i} className="text-gray-400 ml-2">
                              txn {nm.txn_id}: bank_time={nm.bank_time_utc}, diff={nm.time_diff_seconds}s ({nm.time_diff_hours}h), reason={nm.reason}
                            </p>
                          ))}
                        </div>
                      )}
                      {matchDebugInfo.errors?.length > 0 && (
                        <div className="mt-2">
                          <p className="text-red-400">ข้อผิดพลาด:</p>
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
                              {isPerfectMatch && <span className="ml-2 text-green-400 text-xs font-semibold">✓ Perfect Match</span>}
                              {amountDiff > 0 && <span className="ml-2 text-yellow-400 text-xs">ส่วนต่าง: ฿{amountDiff.toFixed(2)}</span>}
                            </div>
                            <div className="text-sm text-gray-400">
                              {txnDate.toLocaleDateString('th-TH')} {txnDate.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                              <span className="ml-2 text-green-300">
                                ({timeDiffSeconds < 60 ? `${Math.floor(timeDiffSeconds)}s` : `${Math.floor(timeDiffSeconds / 60)}m ${Math.floor(timeDiffSeconds % 60)}s`} diff)
                              </span>
                            </div>
                            {txn.description && (
                              <div className="text-xs text-gray-500 mt-1">{txn.description}</div>
                            )}
                            {txn.channel && (
                              <div className="text-xs text-gray-600 mt-1">ช่องทาง: {txn.channel}</div>
                            )}
                            <div className="text-xs text-gray-600 mt-1">รหัสรายการ: {txn.id.substring(0, 8)}...</div>
                          </div>
                          <button
                            onClick={() => handleMatch(txn.id)}
                            className={`px-4 py-2 rounded text-sm font-medium whitespace-nowrap ${
                              isPerfectMatch 
                                ? 'bg-green-600 hover:bg-green-700 text-white' 
                                : 'bg-blue-600 hover:bg-blue-700 text-white'
                            }`}
                            title={`Match with bank transaction (${Math.floor(timeDiffSeconds)}s time difference)`}
                          >
                            {isPerfectMatch ? '✓ Match (Perfect)' : '🔗 Match'}
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
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Unmatch Confirm Modal */}
      <ConfirmModal
        open={confirmUnmatch.open}
        title={t("payins.unmatch")}
        message="ต้องการยกเลิกการจับคู่กับรายการธนาคารใช่หรือไม่?"
        variant="warning"
        confirmText="Unmatch"
        onConfirm={() => handleUnmatch(confirmUnmatch.payin)}
        onCancel={() => setConfirmUnmatch({ open: false, payin: null })}
      />

      {/* Confirm & Post Modal */}
      <ConfirmModal
        open={confirmPost.open}
        title={t("payins.post")}
        message={confirmPost.payin ? `Confirm & Post ฿${confirmPost.payin.amount} จากบ้าน ${confirmPost.payin.house_number}?\n\nระบบจะสร้าง Ledger + จัดสรรยอดเข้าใบแจ้งหนี้อัตโนมัติ` : ''}
        variant="info"
        confirmText="Confirm & Post"
        onConfirm={() => { if (confirmPost.payin) handleConfirmAndPost(confirmPost.payin); }}
        onCancel={() => setConfirmPost({ open: false, payin: null })}
      />

      {/* Reverse Modal (Phase P1) */}
      {showReverseModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">↩️ Reverse Posting</h2>
            <p className="text-gray-300 mb-2">
              House: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              Amount: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString('th-TH')}</span>
            </p>
            <div className="bg-red-900 bg-opacity-30 border border-red-600 rounded p-3 mb-4">
              <p className="text-red-400 text-sm">
                ⚠️ การ Reverse จะยกเลิก Ledger entry และคืนสถานะใบแจ้งหนี้ รายการจะยังอยู่ในระบบ (ไม่ถูกลบ)
              </p>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                เหตุผลในการ Reverse *
              </label>
              <textarea
                value={reverseReason}
                onChange={(e) => setReverseReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder="เช่น ยอดเงินไม่ตรง, จับคู่ผิดบ้าน, ทดสอบ..."
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleReverse} className="btn-danger flex-1">
                ↩️ Reverse
              </button>
              <button
                onClick={() => {
                  setShowReverseModal(false);
                  setReverseReason('');
                  setSelectedPayin(null);
                }}
                className="btn-secondary flex-1"
              >
                ยกเลิก
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
