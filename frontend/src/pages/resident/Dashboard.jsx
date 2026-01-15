import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { invoicesAPI, payinsAPI, api } from '../../api/client';
import { useRole } from '../../contexts/RoleContext';

export default function ResidentDashboard() {
  const { currentHouseId, currentHouseCode } = useRole();
  const [invoices, setInvoices] = useState([]);
  const [payins, setPayins] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloadingStatement, setDownloadingStatement] = useState(false);

  useEffect(() => {
    loadData();
  }, [currentHouseId]);

  const loadData = async () => {
    try {
      const [invoicesRes, payinsRes, summaryRes] = await Promise.all([
        invoicesAPI.list({ house_id: currentHouseId }),
        payinsAPI.list({ house_id: currentHouseId }),
        api.get('/api/dashboard/summary'),
      ]);
      setInvoices(invoicesRes.data);
      setPayins(payinsRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadStatement = async (format = 'pdf') => {
    setDownloadingStatement(true);
    try {
      // Get current month/year
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth() + 1;

      const response = await fetch(
        `/api/accounting/statement/${currentHouseId}?year=${year}&month=${month}&format=${format}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error_en || errorData.error || 'Download failed');
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `statement_${currentHouseId}_${year}_${month}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      console.error('Download failed:', error);
      alert(`Download failed: ${error.message}`);
    } finally {
      setDownloadingStatement(false);
    }
  };

  // Get balance from summary API (negative = owe, positive = overpaid)
  const currentBalance = summary?.current_balance || 0;
  const totalOutstanding = summary?.total_outstanding || 0;
  const totalIncome = summary?.total_income || 0;
  
  // Calculate display values
  const isOverpaid = currentBalance > 0;
  const displayAmount = Math.abs(currentBalance);

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
        <h1 className="text-3xl font-bold text-white mb-2">แดชบอร์ด</h1>
        <p className="text-gray-400">บ้านเลขที่ {currentHouseCode || `#${currentHouseId}`} - ดูใบแจ้งหนี้และประวัติการชำระเงิน</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className={`border-2 rounded-lg p-6 ${isOverpaid ? 'bg-green-900 bg-opacity-50 border-green-600' : 'bg-red-900 bg-opacity-50 border-red-600'}`}>
          <p className={`text-sm mb-1 font-medium ${isOverpaid ? 'text-green-300' : 'text-red-300'}`}>
            {isOverpaid ? 'ชำระเกิน' : 'ยอดค้างชำระ'}
          </p>
          <p className="text-4xl font-bold text-white">฿{displayAmount.toLocaleString()}</p>
        </div>
        <div className="card p-6">
          <p className="text-gray-400 text-sm mb-1">ใบแจ้งหนี้ทั้งหมด</p>
          <p className="text-3xl font-bold text-white">{invoices.length}</p>
        </div>
        <div className="card p-6">
          <p className="text-gray-400 text-sm mb-1">ยอดชำระ</p>
          <p className="text-3xl font-bold text-white">{payins.length}</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <div className="flex flex-wrap gap-4">
          <Link to="/resident/submit" className="btn-primary">
            💳 ชำระเงิน
          </Link>
          <button 
            onClick={() => downloadStatement('pdf')}
            disabled={downloadingStatement}
            className="btn-secondary"
          >
            {downloadingStatement ? '📄 กำลังสร้าง...' : '📄 ดาวน์โหลดใบแจ้งยอด / Download Statement (PDF)'}
          </button>
          <button 
            onClick={() => downloadStatement('xlsx')}
            disabled={downloadingStatement}
            className="btn-outline"
          >
            {downloadingStatement ? '📊 กำลังสร้าง...' : '📊 Download Excel'}
          </button>
        </div>
      </div>

      {/* Invoices */}
      <div className="card mb-6">
        <div className="p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">ใบแจ้งหนี้</h2>
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
          <h2 className="text-xl font-bold text-white">ประวัติการชำระเงิน</h2>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>จำนวนเงิน</th>
                <th>วันที่/เวลาโอน</th>
                <th>สถานะ</th>
                <th>วันที่ส่ง</th>
                <th>การดำเนินการ</th>
              </tr>
            </thead>
            <tbody>
              {payins.length === 0 ? (
                <tr><td colSpan="5" className="text-center py-8 text-gray-400">ยังไม่มีการชำระเงิน</td></tr>
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
                          แก้ไขและส่งใหม่
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
