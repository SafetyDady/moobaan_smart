import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { invoicesAPI, payinsAPI } from '../../api/client';
import { useRole } from '../../contexts/RoleContext';

export default function ResidentDashboard() {
  const { currentHouseId } = useRole();
  const [invoices, setInvoices] = useState([]);
  const [payins, setPayins] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [currentHouseId]);

  const loadData = async () => {
    try {
      const [invoicesRes, payinsRes] = await Promise.all([
        invoicesAPI.list({ house_id: currentHouseId }),
        payinsAPI.list({ house_id: currentHouseId }),
      ]);
      setInvoices(invoicesRes.data);
      setPayins(payinsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const outstandingBalance = invoices
    .filter(inv => inv.status === 'pending' || inv.status === 'overdue')
    .reduce((sum, inv) => sum + inv.total, 0);

  const getStatusBadge = (status) => {
    const badges = {
      submitted: 'badge-info',
      rejected: 'badge-danger',
      matched: 'badge-warning',
      accepted: 'badge-success',
      pending: 'badge-warning',
      paid: 'badge-success',
      overdue: 'badge-danger',
    };
    return badges[status] || 'badge-gray';
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">My Dashboard</h1>
        <p className="text-gray-400">House #{currentHouseId} - View your invoices and payment history</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card p-6">
          <p className="text-gray-400 text-sm mb-1">Outstanding Balance</p>
          <p className="text-3xl font-bold text-red-400">฿{outstandingBalance.toLocaleString()}</p>
        </div>
        <div className="card p-6">
          <p className="text-gray-400 text-sm mb-1">Total Invoices</p>
          <p className="text-3xl font-bold text-white">{invoices.length}</p>
        </div>
        <div className="card p-6">
          <p className="text-gray-400 text-sm mb-1">Payment Submissions</p>
          <p className="text-3xl font-bold text-white">{payins.length}</p>
        </div>
      </div>

      {/* Quick Action */}
      <div className="mb-8">
        <Link to="/resident/submit" className="btn-primary inline-block">
          💳 Submit Payment Slip
        </Link>
      </div>

      {/* Invoices */}
      <div className="card mb-6">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">My Invoices</h2>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Cycle</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Due Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {invoices.length === 0 ? (
                <tr><td colSpan="5" className="text-center py-8 text-gray-400">No invoices</td></tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td className="text-gray-300">{inv.cycle || '-'}</td>
                    <td className="text-gray-300">{inv.invoice_type.replace('_', ' ')}</td>
                    <td className="font-medium text-white">฿{inv.total.toLocaleString()}</td>
                    <td className="text-gray-300">{new Date(inv.due_date).toLocaleDateString()}</td>
                    <td><span className={`badge ${getStatusBadge(inv.status)}`}>{inv.status}</span></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Payment History */}
      <div className="card">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Payment Submission History</h2>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Amount</th>
                <th>Transfer Date/Time</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {payins.length === 0 ? (
                <tr><td colSpan="5" className="text-center py-8 text-gray-400">No payment submissions</td></tr>
              ) : (
                payins.map((payin) => (
                  <tr key={payin.id}>
                    <td className="font-medium text-white">฿{payin.amount.toLocaleString()}</td>
                    <td className="text-gray-300">
                      {new Date(payin.transfer_date).toLocaleDateString()} {payin.transfer_hour}:{String(payin.transfer_minute).padStart(2, '0')}
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadge(payin.status)}`}>{payin.status}</span>
                      {payin.reject_reason && (
                        <div className="text-xs text-red-400 mt-1">{payin.reject_reason}</div>
                      )}
                    </td>
                    <td className="text-gray-400">{new Date(payin.created_at).toLocaleDateString()}</td>
                    <td>
                      {payin.status === 'rejected' && (
                        <Link to="/resident/submit" state={{ editPayin: payin }} className="text-primary-400 hover:text-primary-300 text-sm">
                          Edit & Resubmit
                        </Link>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
