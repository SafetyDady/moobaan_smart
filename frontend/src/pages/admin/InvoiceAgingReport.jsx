import { useState, useEffect } from 'react';
import { reportsAPI, housesAPI } from '../../api/client';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';


/**
 * Phase E.1: Invoice Aging Report
 * 
 * Shows outstanding invoices grouped by aging buckets.
 * READ-ONLY - does not modify any data.
 */
export default function InvoiceAgingReport() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [houses, setHouses] = useState([]);
  const [selectedHouse, setSelectedHouse] = useState('');
  const [asOfDate, setAsOfDate] = useState('');

  // Load houses for filter
  useEffect(() => {
    housesAPI.list()
      .then(res => setHouses(res.data || []))
      .catch(err => console.error('Failed to load houses:', err));
  }, []);

  // Load report
  useEffect(() => {
    loadReport();
  }, [selectedHouse, asOfDate]);

  const loadReport = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (selectedHouse) params.house_id = selectedHouse;
      if (asOfDate) params.as_of_date = asOfDate;
      
      const res = await reportsAPI.invoiceAging(params);
      setReport(res.data);
    } catch (err) {
      console.error('Failed to load aging report:', err);
      setError(err.response?.data?.detail || t('reports.loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  // Bucket display config
  const bucketConfig = {
    'current': { label: t('reports.agingCurrent'), color: 'bg-green-500/20 text-green-400' },
    '0_30': { label: t('reports.aging0_30'), color: 'bg-yellow-500/20 text-yellow-400' },
    '31_60': { label: t('reports.aging31_60'), color: 'bg-orange-500/20 text-orange-400' },
    '61_90': { label: t('reports.aging61_90'), color: 'bg-red-500/20 text-red-400' },
    '90_plus': { label: t('reports.aging90plus'), color: 'bg-red-600/30 text-red-300 font-bold' },
  };

  // Export to CSV
  const handleExportCSV = () => {
    if (!report || !report.rows.length) return;
    
    const headers = ['Invoice ID', 'House', 'Owner', 'Due Date', 'Days Past Due', 'Outstanding', 'Bucket', 'Cycle'];
    const rows = report.rows.map(r => [
      r.invoice_id,
      r.house,
      r.owner_name || '',
      r.due_date,
      r.days_past_due,
      r.outstanding,
      r.bucket,
      r.cycle || ''
    ]);
    
    const csvContent = [
      `Invoice Aging Report - As of ${report.as_of}`,
      '',
      headers.join(','),
      ...rows.map(r => r.join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `invoice-aging-${report.as_of}.csv`;
    link.click();
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">{t('reports.agingTitle')}</h1>
        <p className="text-gray-400 mt-1">{t('invoiceAging.subtitle')}</p>
      </div>

      {/* Filters */}
      <div className="bg-slate-800 rounded-xl p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          {/* House Filter */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-gray-400 mb-1">{t('invoiceAging.house')}</label>
            <select
              value={selectedHouse}
              onChange={(e) => setSelectedHouse(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            >
              <option value="">{t('invoiceAging.allHouses')}</option>
              {houses.map(h => (
                <option key={h.id} value={h.id}>
                  {h.house_code} - {h.owner_name}
                </option>
              ))}
            </select>
          </div>
          
          {/* As Of Date */}
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm text-gray-400 mb-1">{t('invoiceAging.asOfDate')}</label>
            <input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            />
          </div>
          
          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={loadReport}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500"
            >
              {t('common.refresh')}
            </button>
            <button
              onClick={handleExportCSV}
              disabled={!report?.rows?.length}
              className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 disabled:opacity-50"
            >
              {t('reports.exportCsv')}
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
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg p-4">
            <p className="text-gray-400 text-xs">{t('invoiceAging.current')}</p>
            <p className="text-xl font-bold text-green-400">
              ฿{(report.summary.current || 0).toLocaleString('th-TH')}
            </p>
          </div>
          <div className="bg-slate-800 rounded-lg p-4">
            <p className="text-gray-400 text-xs">{t('invoiceAging.days0_30')}</p>
            <p className="text-xl font-bold text-yellow-400">
              ฿{(report.summary['0_30'] || 0).toLocaleString('th-TH')}
            </p>
          </div>
          <div className="bg-slate-800 rounded-lg p-4">
            <p className="text-gray-400 text-xs">{t('invoiceAging.days31_60')}</p>
            <p className="text-xl font-bold text-orange-400">
              ฿{(report.summary['31_60'] || 0).toLocaleString('th-TH')}
            </p>
          </div>
          <div className="bg-slate-800 rounded-lg p-4">
            <p className="text-gray-400 text-xs">{t('invoiceAging.days61_90')}</p>
            <p className="text-xl font-bold text-red-400">
              ฿{(report.summary['61_90'] || 0).toLocaleString('th-TH')}
            </p>
          </div>
          <div className="bg-slate-800 rounded-lg p-4">
            <p className="text-gray-400 text-xs">{t('invoiceAging.days90plus')}</p>
            <p className="text-xl font-bold text-red-300">
              ฿{(report.summary['90_plus'] || 0).toLocaleString('th-TH')}
            </p>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border-l-4 border-primary-500">
            <p className="text-gray-400 text-xs">{t('invoiceAging.totalOutstanding')}</p>
            <p className="text-xl font-bold text-white">
              ฿{(report.total_outstanding || 0).toLocaleString('th-TH')}
            </p>
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
          {t('invoiceAging.asOfDate')}: <span className="text-white">{report.as_of}</span>
          {' | '}
          {t('invoiceAging.invoiceCount')}: <span className="text-white">{report.invoice_count}</span>
        </div>
      )}

      {/* Data Table */}
      {report && !loading && (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">{t('invoiceAging.invoice')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">{t('invoiceAging.house')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">{t('reports.owner')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">{t('reports.billingCycle')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">{t('reports.dueDate')}</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">{t('reports.daysOverdue')}</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">{t('reports.outstanding')}</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">{t('reports.agingBucket')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {report.rows.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                      {t('reports.noOverdueInvoices')} 🎉
                    </td>
                  </tr>
                ) : (
                  report.rows.map((row) => (
                    <tr key={row.invoice_id} className="hover:bg-slate-700/50">
                      <td className="px-4 py-3 text-white font-medium">#{row.invoice_id}</td>
                      <td className="px-4 py-3 text-white">{row.house}</td>
                      <td className="px-4 py-3 text-gray-300 text-sm">{row.owner_name || '-'}</td>
                      <td className="px-4 py-3 text-gray-300 text-sm">{row.cycle || '-'}</td>
                      <td className="px-4 py-3 text-gray-300">{row.due_date}</td>
                      <td className="px-4 py-3 text-right">
                        <span className={row.days_past_due > 0 ? 'text-red-400' : 'text-green-400'}>
                          {row.days_past_due > 0 ? `+${row.days_past_due}` : row.days_past_due}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-yellow-400">
                        ฿{row.outstanding.toLocaleString('th-TH')}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs ${bucketConfig[row.bucket]?.color || 'bg-gray-500/20 text-gray-400'}`}>
                          {bucketConfig[row.bucket]?.label || row.bucket}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
    </AdminPageWrapper>
  );
}
