import { useState, useEffect } from 'react';
import { payinsAPI } from '../../api/client';
import { useRole } from '../../contexts/RoleContext';

export default function PayIns() {
  const { isAdmin, isAccounting, currentRole, loading: roleLoading } = useRole();
  
  // Allow super_admin and accounting roles to manage pay-ins
  const canManagePayins = currentRole === 'super_admin' || currentRole === 'accounting';
  
  // Debug logging
  console.log('PayIns - currentRole:', currentRole);
  console.log('PayIns - canManagePayins:', canManagePayins);
  console.log('PayIns - roleLoading:', roleLoading);
  
  const [payins, setPayins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('PENDING'); // Default to PENDING for review queue
  const [selectedPayin, setSelectedPayin] = useState(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [cancelReason, setCancelReason] = useState('');

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

  const handleAccept = async (payin) => {
    if (!confirm(`Accept payment of ฿${payin.amount} from House ${payin.house_number}?\n\nThis will create an immutable ledger entry and cannot be undone.`)) {
      return;
    }
    try {
      await payinsAPI.accept(payin.id);
      alert('Pay-in accepted and ledger entry created');
      loadPayins();
    } catch (error) {
      console.error('Failed to accept:', error);
      alert(error.response?.data?.detail || 'Failed to accept pay-in');
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
              <option value="PENDING">Pending Review</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="REJECTED">Rejected</option>
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
                <th>Status</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="7" className="text-center py-8">Loading...</td></tr>
              ) : payins.length === 0 ? (
                <tr><td colSpan="7" className="text-center py-8 text-gray-400">
                  {statusFilter === 'PENDING' ? 'No pending pay-ins to review' : 'No pay-ins found'}
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
                          onClick={() => window.open(payin.slip_image_url, '_blank')}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          📎 View
                        </button>
                      ) : (
                        <span className="text-gray-500 text-sm">No slip</span>
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
                            onClick={() => window.open(payin.slip_image_url, '_blank')}
                            className="text-blue-400 hover:text-blue-300 text-sm px-2 py-1 border border-blue-400 rounded"
                          >
                            👁️ View Slip
                          </button>
                        )}
                        
                        {/* Actions for PENDING status */}
                        {payin.status === 'PENDING' && canManagePayins && (
                          <>
                            <button
                              onClick={() => handleAccept(payin)}
                              className="btn-primary text-sm px-3 py-1"
                            >
                              ✓ Accept
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
                        
                        {/* Status indicators */}
                        {payin.status === 'ACCEPTED' && (
                          <span className="text-green-400 text-sm">✓ Ledger created</span>
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
    </div>
  );
}
