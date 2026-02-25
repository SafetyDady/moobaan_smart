import { useState, useEffect } from 'react';
import { reportsAPI, housesAPI } from '../../api/client';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';


/**
 * Phase E.2: Cash Flow vs AR Report
 * 
 * Compares Accrual (AR) vs Cash received.
 * READ-ONLY - does not modify any data.
 */
export default function CashFlowReport() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [houses, setHouses] = useState([]);
  const [selectedHouse, setSelectedHouse] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [groupBy, setGroupBy] = useState('month');

  // Set default dates (current year)
  useEffect(() => {
    const today = new Date();
    const startOfYear = new Date(today.getFullYear(), 0, 1);
    setFromDate(startOfYear.toISOString().split('T')[0]);
    setToDate(today.toISOString().split('T')[0]);
  }, []);

  // Load houses for filter
  useEffect(() => {
    housesAPI.list()
      .then(res => setHouses(res.data || []))
      .catch(err => console.error('Failed to load houses:', err));
  }, []);

  // Load report when filters change
  useEffect(() => {
    if (fromDate && toDate) {
      loadReport();
    }
  }, [selectedHouse, fromDate, toDate, groupBy]);

  const loadReport = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        from_date: fromDate,
        to_date: toDate,
        group_by: groupBy
      };
      if (selectedHouse) params.house_id = selectedHouse;
      
      const res = await reportsAPI.cashflowVsAr(params);
      setReport(res.data);
    } catch (err) {
      console.error('Failed to load cash flow report:', err);
      setError(err.response?.data?.detail || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  // Gap color coding
  const getGapColor = (gap) => {
    if (gap > 0) return 'text-red-400';  // Under-collected
    if (gap < 0) return 'text-green-400';  // Over-collected
    return 'text-gray-400';  // Balanced
  };

  const getGapBgColor = (gap) => {
    if (gap > 0) return 'bg-red-500/10';
    if (gap < 0) return 'bg-green-500/10';
    return 'bg-slate-700/50';
  };

  // Export to CSV
  const handleExportCSV = () => {
    if (!report || !report.rows.length) return;
    
    const headers = ['Period', 'AR (Accrual)', 'Cash Received', 'Gap', 'Gap %'];
    const rows = report.rows.map(r => [
      r.period,
      r.ar_amount,
      r.cash_amount,
      r.gap,
      r.gap_percent !== null ? `${r.gap_percent}%` : ''
    ]);
    
    // Add totals row
    rows.push([
      'TOTAL',
      report.summary.total_ar,
      report.summary.total_cash,
      report.summary.total_gap,
      report.summary.gap_percent !== null ? `${report.summary.gap_percent}%` : ''
    ]);
    
    const csvContent = [
      `Cash Flow vs AR Report`,
      `Period: ${report.from_date} to ${report.to_date}`,
      '',
      headers.join(','),
      ...rows.map(r => r.join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `cashflow-vs-ar-${report.from_date}-to-${report.to_date}.csv`;
    link.click();
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">{t('reports.cashFlowTitle')}</h1>
        <p className="text-gray-400 mt-1">เปรียบเทียบยอดค้างรับ (AR) vs เงินสดรับจริง</p>
      </div>

      {/* Filters */}
      <div className="bg-slate-800 rounded-xl p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          {/* From Date */}
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm text-gray-400 mb-1">จากวันที่</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            />
          </div>
          
          {/* To Date */}
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm text-gray-400 mb-1">ถึงวันที่</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            />
          </div>
          
          {/* House Filter */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-gray-400 mb-1">บ้าน</label>
            <select
              value={selectedHouse}
              onChange={(e) => setSelectedHouse(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            >
              <option value="">ทุกบ้าน</option>
              {houses.map(h => (
                <option key={h.id} value={h.id}>
                  {h.house_code} - {h.owner_name}
                </option>
              ))}
            </select>
          </div>
          
          {/* Group By */}
          <div className="min-w-[120px]">
            <label className="block text-sm text-gray-400 mb-1">จัดกลุ่มตาม</label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            >
              <option value="month">เดือน</option>
              <option value="week">สัปดาห์</option>
            </select>
          </div>
          
          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={loadReport}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500"
            >
              โหลดใหม่
            </button>
            <button
              onClick={handleExportCSV}
              disabled={!report?.rows?.length}
              className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 disabled:opacity-50"
            >
              Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 mb-6">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Summary Cards */}
      {report && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {/* AR Total */}
          <div className="bg-slate-800 rounded-lg p-4">
            <p className="text-gray-400 text-xs">AR (Accrual)</p>
            <p className="text-2xl font-bold text-blue-400">
              ฿{report.summary.total_ar.toLocaleString('th-TH')}
            </p>
            <p className="text-xs text-gray-500 mt-1">{report.invoice_count} invoices</p>
          </div>
          
          {/* Cash Total */}
          <div className="bg-slate-800 rounded-lg p-4">
            <p className="text-gray-400 text-xs">{t('reports.cashReceived')}</p>
            <p className="text-2xl font-bold text-green-400">
              ฿{report.summary.total_cash.toLocaleString('th-TH')}
            </p>
            <p className="text-xs text-gray-500 mt-1">{report.payin_count} pay-ins</p>
          </div>
          
          {/* Gap */}
          <div className={`rounded-lg p-4 ${getGapBgColor(report.summary.total_gap)}`}>
            <p className="text-gray-400 text-xs">{t('reports.gapArCash')}</p>
            <p className={`text-2xl font-bold ${getGapColor(report.summary.total_gap)}`}>
              {report.summary.total_gap >= 0 ? '+' : ''}฿{report.summary.total_gap.toLocaleString('th-TH')}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {report.summary.total_gap > 0 ? 'Under-collected' : 
               report.summary.total_gap < 0 ? 'Over-collected' : 'Balanced'}
            </p>
          </div>
          
          {/* Gap Percent */}
          <div className="bg-slate-800 rounded-lg p-4 border-l-4 border-primary-500">
            <p className="text-gray-400 text-xs">{t('reports.gapPercent')}</p>
            <p className={`text-2xl font-bold ${getGapColor(report.summary.total_gap)}`}>
              {report.summary.gap_percent !== null 
                ? `${report.summary.gap_percent >= 0 ? '+' : ''}${report.summary.gap_percent}%`
                : 'N/A'}
            </p>
            <p className="text-xs text-gray-500 mt-1">of AR amount</p>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
        </div>
      )}

      {/* Report Info */}
      {report && !loading && (
        <div className="mb-4 text-sm text-gray-400">
          ช่วงเวลา: <span className="text-white">{report.from_date}</span> ถึง <span className="text-white">{report.to_date}</span>
          {' | '}
          จัดกลุ่ม: <span className="text-white">{report.group_by === 'month' ? 'รายเดือน' : 'รายสัปดาห์'}</span>
        </div>
      )}

      {/* Data Table */}
      {report && !loading && (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">งวด</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">AR (Accrual)</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">{t('reports.cashReceived')}</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">{t('reports.gap')}</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">{t('reports.gapPercent')}</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">สถานะ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {report.rows.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                      ไม่มีข้อมูลในช่วงเวลาที่เลือก
                    </td>
                  </tr>
                ) : (
                  <>
                    {report.rows.map((row) => (
                      <tr key={row.period} className={`hover:bg-slate-700/50 ${getGapBgColor(row.gap)}`}>
                        <td className="px-4 py-3 text-white font-medium">{row.period}</td>
                        <td className="px-4 py-3 text-right text-blue-400">
                          ฿{row.ar_amount.toLocaleString('th-TH')}
                        </td>
                        <td className="px-4 py-3 text-right text-green-400">
                          ฿{row.cash_amount.toLocaleString('th-TH')}
                        </td>
                        <td className={`px-4 py-3 text-right font-medium ${getGapColor(row.gap)}`}>
                          {row.gap >= 0 ? '+' : ''}฿{row.gap.toLocaleString('th-TH')}
                        </td>
                        <td className={`px-4 py-3 text-right ${getGapColor(row.gap)}`}>
                          {row.gap_percent !== null 
                            ? `${row.gap_percent >= 0 ? '+' : ''}${row.gap_percent}%`
                            : '-'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {row.gap > 0 ? (
                            <span className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400">
                              Under
                            </span>
                          ) : row.gap < 0 ? (
                            <span className="px-2 py-1 rounded text-xs bg-green-500/20 text-green-400">
                              Over
                            </span>
                          ) : (
                            <span className="px-2 py-1 rounded text-xs bg-gray-500/20 text-gray-400">
                              OK
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {/* Totals Row */}
                    <tr className="bg-slate-700 font-bold">
                      <td className="px-4 py-3 text-white">TOTAL</td>
                      <td className="px-4 py-3 text-right text-blue-300">
                        ฿{report.summary.total_ar.toLocaleString('th-TH')}
                      </td>
                      <td className="px-4 py-3 text-right text-green-300">
                        ฿{report.summary.total_cash.toLocaleString('th-TH')}
                      </td>
                      <td className={`px-4 py-3 text-right ${getGapColor(report.summary.total_gap)}`}>
                        {report.summary.total_gap >= 0 ? '+' : ''}฿{report.summary.total_gap.toLocaleString('th-TH')}
                      </td>
                      <td className={`px-4 py-3 text-right ${getGapColor(report.summary.total_gap)}`}>
                        {report.summary.gap_percent !== null 
                          ? `${report.summary.gap_percent >= 0 ? '+' : ''}${report.summary.gap_percent}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-3"></td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 text-xs text-gray-500">
        <p><span className="text-red-400">+Gap (Under)</span> = AR มากกว่า Cash (ยังเก็บเงินไม่ครบ)</p>
        <p><span className="text-green-400">-Gap (Over)</span> = Cash มากกว่า AR (เก็บเงินล่วงหน้า/เกิน)</p>
      </div>
    </div>
    </AdminPageWrapper>
  );
}
