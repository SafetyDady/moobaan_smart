/**
 * @deprecated This Desktop Dashboard is no longer used.
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Section 2.1:
 * "Resident Desktop UI is intentionally removed by design."
 * 
 * All Resident users now see MobileDashboard regardless of device.
 * This file is kept for reference but is not rendered.
 * 
 * See: frontend/src/pages/resident/ResidentRouteWrapper.jsx
 */

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

  const handleDeletePayin = async (payinId) => {
    if (!confirm('คุณต้องการลบรายการชำระเงินนี้ใช่หรือไม่?')) {
      return;
    }
    try {
      await payinsAPI.delete(payinId);
      alert('ลบรายการสำเร็จ');
      loadData();
    } catch (error) {
      console.error('Failed to delete payin:', error);
      alert(error.response?.data?.detail || 'ลบรายการไม่สำเร็จ');
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
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
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
      // New state machine statuses
      DRAFT: 'badge-gray',
      SUBMITTED: 'badge-info',
      REJECTED_NEEDS_FIX: 'badge-danger',
      ACCEPTED: 'badge-success',
      // Legacy statuses (for backward compatibility)
      submitted: 'badge-info',
      rejected: 'badge-danger',
      matched: 'badge-warning',
      accepted: 'badge-success',
      pending: 'badge-warning',
      PENDING: 'badge-warning',
      REJECTED: 'badge-danger',
      // Invoice statuses
      paid: 'badge-success',
      overdue: 'badge-danger',
    };
    return badges[status] || 'badge-gray';
  };

  // Get Thai display text for pay-in status
  const getStatusText = (status) => {
    const texts = {
      DRAFT: 'ร่าง',
      SUBMITTED: 'รอตรวจสอบ',
      REJECTED_NEEDS_FIX: 'ต้องแก้ไข',
      ACCEPTED: 'รับแล้ว',
      // Legacy
      PENDING: 'รอตรวจสอบ',
      REJECTED: 'ปฏิเสธ',
    };
    return texts[status] || status;
  };

  // Check if payin can be edited by resident
  const canEditPayin = (payin) => {
    return ['DRAFT', 'REJECTED_NEEDS_FIX', 'PENDING', 'REJECTED'].includes(payin.status);
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
                <th>วันเวลาส่งข้อมูล</th>
                <th>การดำเนินการ</th>
              </tr>
            </thead>
            <tbody>
              {payins.length === 0 ? (
                <tr><td colSpan="5" className="text-center py-8 text-gray-400">ยังไม่มีการชำระเงิน</td></tr>
              ) : (
                payins.map((payin) => {
                  const submittedAt = new Date(payin.created_at);
                  const submittedDate = submittedAt.toLocaleDateString('th-TH', { 
                    year: '2-digit', 
                    month: 'short', 
                    day: 'numeric' 
                  });
                  const submittedTime = submittedAt.toLocaleTimeString('th-TH', { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: false 
                  });
                  
                  return (
                    <tr key={payin.id}>
                      <td className="font-medium text-white">฿{payin.amount.toLocaleString()}</td>
                      <td className="text-gray-300">
                        {new Date(payin.transfer_date).toLocaleDateString('th-TH', { year: '2-digit', month: 'short', day: 'numeric' })}
                        <br />
                        <span className="text-sm text-gray-400">
                          {String(payin.transfer_hour).padStart(2, '0')}:{String(payin.transfer_minute).padStart(2, '0')} น.
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${getStatusBadge(payin.status)}`}>{getStatusText(payin.status)}</span>
                        {payin.reject_reason && (
                          <div className="text-xs text-red-400 mt-1">{payin.reject_reason}</div>
                        )}
                        {payin.admin_note && payin.status === 'REJECTED_NEEDS_FIX' && (
                          <div className="text-xs text-yellow-400 mt-1">💬 {payin.admin_note}</div>
                        )}
                      </td>
                      <td className="text-gray-400 text-sm">
                        {submittedDate}
                        <br />
                        <span className="text-xs text-gray-500">{submittedTime}</span>
                      </td>
                      <td>
                        <div className="flex gap-2">
                          {payin.status === 'DRAFT' && (
                            <>
                              <Link 
                                to="/resident/submit" 
                                state={{ editPayin: payin }} 
                                className="text-blue-400 hover:text-blue-300 text-sm"
                              >
                                ✏️ แก้ไข
                              </Link>
                              <button
                                onClick={() => handleDeletePayin(payin.id)}
                                className="text-red-400 hover:text-red-300 text-sm"
                              >
                                🗑️ ลบ
                              </button>
                            </>
                          )}
                          {payin.status === 'SUBMITTED' && (
                            <span className="text-blue-400 text-sm">⏳ กำลังตรวจสอบ</span>
                          )}
                          {payin.status === 'REJECTED_NEEDS_FIX' && (
                            <Link 
                              to="/resident/submit" 
                              state={{ editPayin: payin }} 
                              className="text-primary-400 hover:text-primary-300 text-sm"
                            >
                              🔄 แก้ไขและส่งใหม่
                            </Link>
                          )}
                          {/* Legacy status support */}
                          {payin.status === 'PENDING' && (
                            <>
                              <Link 
                                to="/resident/submit" 
                                state={{ editPayin: payin }} 
                                className="text-blue-400 hover:text-blue-300 text-sm"
                              >
                                ✏️ แก้ไข
                              </Link>
                              <button
                                onClick={() => handleDeletePayin(payin.id)}
                                className="text-red-400 hover:text-red-300 text-sm"
                              >
                                🗑️ ลบ
                              </button>
                            </>
                          )}
                          {payin.status === 'REJECTED' && (
                            <Link 
                              to="/resident/submit" 
                              state={{ editPayin: payin }} 
                              className="text-primary-400 hover:text-primary-300 text-sm"
                            >
                              🔄 แก้ไขและส่งใหม่
                            </Link>
                          )}
                          {payin.status === 'ACCEPTED' && (
                            <span className="text-green-400 text-sm">✓ รับแล้ว</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
