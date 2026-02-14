import { useState, useEffect } from 'react';
import { payinsAPI, bankReconciliationAPI } from '../../api/client';
import { useRole } from '../../contexts/RoleContext';

export default function PayIns() {
  const { isAdmin, isAccounting, currentRole, loading: roleLoading } = useRole();
  
  // Allow super_admin and accounting roles to manage pay-ins
  const canManagePayins = currentRole === 'super_admin' || currentRole === 'accounting';
  
  const [payins, setPayins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('SUBMITTED'); // Default to SUBMITTED for review queue (new state machine)
  const [selectedPayin, setSelectedPayin] = useState(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showMatchModal, setShowMatchModal] = useState(false);
  const [showReverseModal, setShowReverseModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [reverseReason, setReverseReason] = useState('');
  const [bankTransactions, setBankTransactions] = useState([]);
  const [loadingTransactions, setLoadingTransactions] = useState(false);
  const [posting, setPosting] = useState(null); // payin id currently being posted

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
    } catch (error) {
      console.error('Failed to load candidate bank transactions:', error);
      alert(error.response?.data?.detail || 'Failed to load candidate bank transactions');
    } finally {
      setLoadingTransactions(false);
    }
  };

  const handleMatch = async (txnId) => {
    try {
      await bankReconciliationAPI.matchTransaction(txnId, selectedPayin.id);
      alert('Successfully matched with bank transaction');
      setShowMatchModal(false);
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to match:', error);
      alert(error.response?.data?.detail || 'Failed to match transaction');
    }
  };

  const handleUnmatch = async (payin) => {
    if (!confirm(`Unmatch pay-in from bank transaction?\n\nThis will remove the reconciliation link.`)) {
      return;
    }
    try {
      await bankReconciliationAPI.unmatchTransaction(payin.matched_statement_txn_id);
      alert('Successfully unmatched');
      loadPayins();
    } catch (error) {
      console.error('Failed to unmatch:', error);
      alert(error.response?.data?.detail || 'Failed to unmatch');
    }
  };

  const openMatchModal = async (payin) => {
    setSelectedPayin(payin);
    setShowMatchModal(true);
    await loadBankTransactions(payin);
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }
    try {
      await payinsAPI.reject(selectedPayin.id, rejectReason);
      alert('Pay-in rejected successfully');
      setShowRejectModal(false);
      setRejectReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to reject:', error);
      alert(error.response?.data?.detail || 'Failed to reject pay-in');
    }
  };

  const handleConfirmAndPost = async (payin) => {
    if (!confirm(`Confirm & Post ฿${payin.amount} จากบ้าน ${payin.house_number}?\n\nระบบจะสร้าง Ledger + จัดสรรยอดเข้าใบแจ้งหนี้อัตโนมัติ`)) {
      return;
    }
    setPosting(payin.id);
    try {
      const result = await bankReconciliationAPI.confirmAndPost(payin.matched_statement_txn_id);
      const data = result.data;
      const allocCount = data.allocations?.length || 0;
      if (data.status === 'already_posted') {
        alert('รายการนี้ถูก Post ไปแล้ว (idempotent)');
      } else {
        alert(`✅ Posted สำเร็จ!\n\nLedger #${data.income_transaction_id}\nจัดสรร ${allocCount} ใบแจ้งหนี้`);
      }
      loadPayins();
    } catch (error) {
      console.error('Failed to confirm & post:', error);
      const detail = error.response?.data?.detail;
      if (typeof detail === 'object' && detail.code === 'AMBIGUOUS') {
        alert(`⚠️ ${detail.message}`);
      } else {
        alert(typeof detail === 'string' ? detail : 'Failed to confirm & post');
      }
    } finally {
      setPosting(null);
    }
  };

  const handleReverse = async () => {
    if (!reverseReason.trim()) {
      alert('กรุณาระบุเหตุผลในการ Reverse');
      return;
    }
    try {
      const result = await bankReconciliationAPI.reverseTransaction(
        selectedPayin.matched_statement_txn_id,
        reverseReason
      );
      alert(`↩️ Reversed สำเร็จ\n\n${result.data.message}`);
      setShowReverseModal(false);
      setReverseReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to reverse:', error);
      alert(error.response?.data?.detail || 'Failed to reverse');
    }
  };

  const handleCancel = async () => {
    if (!cancelReason.trim()) {
      alert('Please provide a reason for cancellation');
      return;
    }
    try {
      await payinsAPI.cancel(selectedPayin.id, cancelReason);
      alert('Pay-in cancelled and deleted');
      setShowCancelModal(false);
      setCancelReason('');
      setSelectedPayin(null);
      loadPayins();
    } catch (error) {
      console.error('Failed to cancel:', error);
      alert(error.response?.data?.detail || 'Failed to cancel pay-in');
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
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Pay-in Review Queue</h1>
        <p className="text-gray-400">Review and process resident payment submissions</p>
      </div>

      {/* Filter */}
      <div className="card p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Filter by Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-full"
            >
              <option value="">All Status</option>
              <option value="SUBMITTED">Needs Review (SUBMITTED)</option>
              <option value="PENDING">Pending Review (Legacy)</option>
              <option value="REJECTED_NEEDS_FIX">Rejected - Needs Fix</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="REJECTED">Rejected (Legacy)</option>
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
                <th>House</th>
                <th>Amount</th>
                <th>Transfer Date/Time</th>
                <th>Slip</th>
                <th>Match Status</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="8" className="text-center py-8">Loading...</td></tr>
              ) : payins.length === 0 ? (
                <tr><td colSpan="8" className="text-center py-8 text-gray-400">
                  {(statusFilter === 'PENDING' || statusFilter === 'SUBMITTED') ? 'No pay-ins pending review' : 'No pay-ins found'}
                </td></tr>
              ) : (
                payins.map((payin) => (
                  <tr key={payin.id}>
                    <td className="font-medium text-white">{payin.house_number}</td>
                    <td className="text-primary-400 font-semibold">฿{payin.amount.toLocaleString()}</td>
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
                        <span className="text-gray-500 text-sm">No slip</span>
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
                                onClick={() => handleUnmatch(payin)}
                                className="bg-orange-600 hover:bg-orange-700 text-white text-sm px-3 py-1 rounded"
                              >
                                🔓 Unmatch
                              </button>
                            )}
                            
                            {/* Confirm & Post button — replaces old Accept (Phase P1) */}
                            <button
                              onClick={() => handleConfirmAndPost(payin)}
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
                                setShowCancelModal(true);
                              }}
                              className="btn-secondary text-sm px-3 py-1"
                            >
                              🗑 Cancel
                            </button>
                          </>
                        )}
                        
                        {/* Cancel option for REJECTED status */}
                        {payin.status === 'REJECTED' && canManagePayins && (
                          <button
                            onClick={() => {
                              setSelectedPayin(payin);
                              setShowCancelModal(true);
                            }}
                            className="btn-secondary text-sm px-3 py-1"
                          >
                            🗑 Cancel
                          </button>
                        )}

                        {/* REJECTED_NEEDS_FIX - waiting for resident to fix and resubmit */}
                        {payin.status === 'REJECTED_NEEDS_FIX' && (
                          <span className="text-orange-400 text-sm" title="Cannot match until resident resubmits">
                            ⏳ Awaiting resident fix
                          </span>
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
                                title="Reverse this posting (undo ledger and invoice allocation)"
                              >
                                ↩️ Reverse
                              </button>
                            )}
                          </div>
                        )}
                        {payin.status === 'REJECTED' && (
                          <span className="text-red-400 text-sm">Resident can resubmit</span>
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
            <h2 className="text-xl font-bold text-white mb-4">Reject Pay-in</h2>
            <p className="text-gray-300 mb-2">
              House: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              Amount: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString()}</span>
            </p>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                Reason for Rejection *
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder="e.g., Wrong amount, unclear slip, incorrect date..."
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleReject} className="btn-danger flex-1">
                Reject
              </button>
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReason('');
                  setSelectedPayin(null);
                }}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">Cancel Pay-in (Test Cleanup)</h2>
            <p className="text-gray-300 mb-2">
              House: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              Amount: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString()}</span>
            </p>
            <div className="bg-yellow-900 bg-opacity-30 border border-yellow-600 rounded p-3 mb-4">
              <p className="text-yellow-400 text-sm">
                ⚠️ This will permanently delete the pay-in report. Use for test cleanup only.
              </p>
            </div>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                Reason for Cancellation *
              </label>
              <textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder="e.g., Test data, duplicate submission..."
              />
            </div>
            <div className="flex gap-3">
              <button onClick={handleCancel} className="btn-danger flex-1">
                Delete
              </button>
              <button
                onClick={() => {
                  setShowCancelModal(false);
                  setCancelReason('');
                  setSelectedPayin(null);
                }}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Match Modal */}
      {showMatchModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="card p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-white mb-4">Match Pay-in with Bank Transaction</h2>
            
            {/* Pay-in Details */}
            <div className="bg-blue-900 bg-opacity-20 border border-blue-600 rounded p-4 mb-4">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">Pay-in Details</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-400">House:</div>
                <div className="text-white font-medium">{selectedPayin?.house_number}</div>
                <div className="text-gray-400">Amount:</div>
                <div className="text-primary-400 font-semibold">฿{selectedPayin?.amount?.toLocaleString()}</div>
                <div className="text-gray-400">Transfer Time:</div>
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
                <div className="text-center py-8 text-gray-400">Loading candidate transactions...</div>
              ) : bankTransactions.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-yellow-400 mb-2">⚠️ No matching bank transactions found</p>
                  <p className="text-sm text-gray-400 mb-2">
                    Matching criteria: Amount exactly ฿{selectedPayin?.amount?.toLocaleString()}, Time within ±1 minute
                  </p>
                  <p className="text-xs text-gray-500">
                    Check if: (1) Bank statement imported, (2) Amount matches exactly, (3) Time within ±1 minute of transfer_datetime
                  </p>
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
                              {amountDiff > 0 && <span className="ml-2 text-yellow-400 text-xs">Amount diff: ฿{amountDiff.toFixed(2)}</span>}
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
                              <div className="text-xs text-gray-600 mt-1">Channel: {txn.channel}</div>
                            )}
                            <div className="text-xs text-gray-600 mt-1">Txn ID: {txn.id.substring(0, 8)}...</div>
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

      {/* Reverse Modal (Phase P1) */}
      {showReverseModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">↩️ Reverse Posting</h2>
            <p className="text-gray-300 mb-2">
              House: <span className="font-medium text-primary-400">{selectedPayin?.house_number}</span>
            </p>
            <p className="text-gray-300 mb-4">
              Amount: <span className="font-medium text-primary-400">฿{selectedPayin?.amount?.toLocaleString()}</span>
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
