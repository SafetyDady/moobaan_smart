import { useState, useEffect } from 'react';
import { invoicesAPI } from '../../api/client';

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('auto'); // 'auto' or 'manual'

  useEffect(() => {
    loadInvoices();
  }, [activeTab]);

  const loadInvoices = async () => {
    try {
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

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'badge-warning',
      paid: 'badge-success',
      overdue: 'badge-danger',
    };
    return badges[status] || 'badge-gray';
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
                <th>Status</th>
                <th>Due Date</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="6" className="text-center py-8">Loading...</td></tr>
              ) : invoices.length === 0 ? (
                <tr><td colSpan="6" className="text-center py-8 text-gray-400">No invoices found</td></tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td className="font-medium text-white">{inv.house_number}</td>
                    <td className="text-gray-300">{inv.cycle || '-'}</td>
                    <td className="text-gray-300">฿{inv.total.toLocaleString()}</td>
                    <td><span className={`badge ${getStatusBadge(inv.status)}`}>{inv.status}</span></td>
                    <td className="text-gray-300">{new Date(inv.due_date).toLocaleDateString()}</td>
                    <td className="text-gray-400">{new Date(inv.created_at).toLocaleDateString()}</td>
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
