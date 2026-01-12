import { useState, useEffect } from 'react';
import { payinsAPI } from '../../api/client';
import { useRole } from '../../contexts/RoleContext';

export default function PayIns() {
  const { isAdmin } = useRole();
  const [payins, setPayins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedPayin, setSelectedPayin] = useState(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  useEffect(() => {
    loadPayins();
  }, [statusFilter]);

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
      alert('Pay-in rejected');
      setShowRejectModal(false);
      setRejectReason('');
      loadPayins();
    } catch (error) {
      console.error('Failed to reject:', error);
      alert('Failed to reject pay-in');
    }
  };

  const handleMatch = async (id) => {
    // Mock statement row ID
    const mockStatementRowId = Math.floor(Math.random() * 100);
    try {
      await payinsAPI.match(id, mockStatementRowId);
      alert('Pay-in marked as matched');
      loadPayins();
    } catch (error) {
      console.error('Failed to match:', error);
      alert('Failed to match pay-in');
    }
  };

  const handleAccept = async (id) => {
    if (!confirm('Accept this pay-in? This action is final and cannot be undone.')) return;
    try {
      await payinsAPI.accept(id);
      alert('Pay-in accepted and locked');
      loadPayins();
    } catch (error) {
      console.error('Failed to accept:', error);
      alert('Failed to accept pay-in');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      submitted: 'badge-info',
      rejected: 'badge-danger',
      matched: 'badge-warning',
      accepted: 'badge-success',
    };
    return badges[status] || 'badge-gray';
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Pay-in Reports</h1>
        <p className="text-gray-400">Review and process payment submissions</p>
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
              <option value="submitted">Submitted</option>
              <option value="rejected">Rejected</option>
              <option value="matched">Matched</option>
              <option value="accepted">Accepted</option>
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
                <th>Status</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="6" className="text-center py-8">Loading...</td></tr>
              ) : payins.length === 0 ? (
                <tr><td colSpan="6" className="text-center py-8 text-gray-400">No pay-ins found</td></tr>
              ) : (
                payins.map((payin) => (
                  <tr key={payin.id}>
                    <td className="font-medium text-white">{payin.house_number}</td>
                    <td className="text-gray-300">฿{payin.amount.toLocaleString()}</td>
                    <td className="text-gray-300">
                      {new Date(payin.transfer_date).toLocaleDateString()} {payin.transfer_hour}:{String(payin.transfer_minute).padStart(2, '0')}
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadge(payin.status)}`}>
                        {payin.status}
                      </span>
                      {payin.reject_reason && (
                        <div className="text-xs text-red-400 mt-1">{payin.reject_reason}</div>
                      )}
                    </td>
                    <td className="text-gray-400">{new Date(payin.created_at).toLocaleDateString()}</td>
                    <td>
                      <div className="flex gap-2 flex-wrap">
                        {payin.status !== 'accepted' && (
                          <button
                            onClick={() => {
                              setSelectedPayin(payin);
                              setShowRejectModal(true);
                            }}
                            className="text-red-400 hover:text-red-300 text-sm"
                          >
                            Reject
                          </button>
                        )}
                        {(payin.status === 'submitted' || payin.status === 'matched') && (
                          <button
                            onClick={() => handleMatch(payin.id)}
                            className="text-yellow-400 hover:text-yellow-300 text-sm"
                          >
                            Match
                          </button>
                        )}
                        {isAdmin && payin.status === 'matched' && (
                          <button
                            onClick={() => handleAccept(payin.id)}
                            className="text-primary-400 hover:text-primary-300 text-sm font-medium"
                          >
                            Accept
                          </button>
                        )}
                        <button
                          onClick={() => window.open(payin.slip_image_url, '_blank')}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          View Slip
                        </button>
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
            <p className="text-gray-300 mb-4">
              House: <span className="font-medium">{selectedPayin?.house_number}</span>
            </p>
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">
                Reason for Rejection *
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="input w-full h-24 resize-none"
                placeholder="Please provide a clear reason..."
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
