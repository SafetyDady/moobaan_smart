/**
 * Phase G.1: Period Closing & Snapshot Page
 * 
 * Purpose:
 * - View period snapshots
 * - Lock periods (create snapshot)
 * - Unlock periods (super_admin only)
 * - View unlock audit logs
 * 
 * Governance Layer: "ตัวเลขเดือนนี้จบแล้ว" (This month's figures are finalized)
 */
import React, { useState, useEffect } from 'react';
import { periodsAPI, exportAPI } from '../api/client';
import { useToast } from '../components/Toast';
import { SkeletonCard } from '../components/Skeleton';
import { useAuth } from '../contexts/AuthContext';
import AdminPageWrapper from '../components/AdminPageWrapper';
import { t } from '../hooks/useLocale';


// Month names in Thai
const MONTH_NAMES_TH = [
  '', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
  'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
];

// MONTH_NAMES_EN removed - using Thai only (Phase 2 Localization)

function PeriodClosing() {
  const { user } = useAuth();
  const toast = useToast();
  const isSuperAdmin = user?.role === 'super_admin';
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  
  // State
  const [periods, setPeriods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Selected period for detail view
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [periodDetail, setPeriodDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  
  // Modal states
  const [showLockModal, setShowLockModal] = useState(false);
  const [showUnlockModal, setShowUnlockModal] = useState(false);
  const [unlockReason, setUnlockReason] = useState('');
  const [lockNotes, setLockNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  
  // Export state
  const [exporting, setExporting] = useState(false);
  
  // Unlock logs
  const [unlockLogs, setUnlockLogs] = useState([]);
  const [showLogsModal, setShowLogsModal] = useState(false);
  
  // Current year/month for quick actions
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth() + 1;
  
  // Generate period options (current month and 12 months back)
  const periodOptions = [];
  for (let i = 0; i <= 12; i++) {
    const d = new Date(currentYear, currentMonth - 1 - i, 1);
    periodOptions.push({
      year: d.getFullYear(),
      month: d.getMonth() + 1,
      label: `${MONTH_NAMES_TH[d.getMonth() + 1]} ${d.getFullYear()} (${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')})`
    });
  }
  
  // Fetch periods on mount
  useEffect(() => {
    fetchPeriods();
  }, []);
  
  const fetchPeriods = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await periodsAPI.list({ limit: 24 });
      setPeriods(response.data.items || []);
    } catch (err) {
      console.error('Error fetching periods:', err);
      setError(t('periodClosing.loadError'));
    } finally {
      setLoading(false);
    }
  };
  
  const fetchPeriodDetail = async (year, month) => {
    try {
      setDetailLoading(true);
      const response = await periodsAPI.get(year, month);
      setPeriodDetail(response.data);
    } catch (err) {
      console.error('Error fetching period detail:', err);
      setPeriodDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };
  
  const fetchUnlockLogs = async (year, month) => {
    try {
      const response = await periodsAPI.getUnlockLogs(year, month);
      setUnlockLogs(response.data.items || []);
    } catch (err) {
      console.error('Error fetching unlock logs:', err);
      setUnlockLogs([]);
    }
  };
  
  const handleSelectPeriod = (year, month) => {
    setSelectedPeriod({ year, month });
    fetchPeriodDetail(year, month);
  };
  
  const handleLockPeriod = async () => {
    if (!selectedPeriod) return;
    
    try {
      setActionLoading(true);
      await periodsAPI.lock(selectedPeriod.year, selectedPeriod.month, { notes: lockNotes });
      setShowLockModal(false);
      setLockNotes('');
      fetchPeriods();
      fetchPeriodDetail(selectedPeriod.year, selectedPeriod.month);
    } catch (err) {
      console.error('Error locking period:', err);
      toast.error(err.response?.data?.detail || t('periodClosing.lockFailed'));
    } finally {
      setActionLoading(false);
    }
  };
  
  const handleUnlockPeriod = async () => {
    if (!selectedPeriod || !unlockReason.trim()) return;
    
    if (unlockReason.trim().length < 10) {
      toast.warning(t('periodClosing.unlockReasonMinLength'));
      return;
    }
    
    try {
      setActionLoading(true);
      await periodsAPI.unlock(selectedPeriod.year, selectedPeriod.month, unlockReason.trim());
      setShowUnlockModal(false);
      setUnlockReason('');
      fetchPeriods();
      fetchPeriodDetail(selectedPeriod.year, selectedPeriod.month);
    } catch (err) {
      console.error('Error unlocking period:', err);
      toast.error(err.response?.data?.detail || t('periodClosing.unlockFailed'));
    } finally {
      setActionLoading(false);
    }
  };
  
  const handleViewLogs = (year, month) => {
    fetchUnlockLogs(year, month);
    setShowLogsModal(true);
  };
  
  // Export handler - Phase G.2
  const handleExport = async () => {
    if (!selectedPeriod || periodDetail?.status !== 'LOCKED') return;
    
    const periodStr = `${selectedPeriod.year}-${String(selectedPeriod.month).padStart(2, '0')}`;
    
    try {
      setExporting(true);
      const response = await exportAPI.accounting(periodStr, periodStr);
      
      // Create blob and trigger download
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `moobaan_accounting_export_${periodStr}_${periodStr}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      toast.error(t('periodClosing.exportFailed'));
    } finally {
      setExporting(false);
    }
  };
  
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: 'THB',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('th-TH', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const getStatusBadge = (status) => {
    if (status === 'LOCKED') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          {t('periodClosing.lockedBadge')}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
        {t('periodClosing.draftBadge')}
      </span>
    );
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('periodClosing.pageTitle')}</h1>
        <p className="mt-1 text-sm text-gray-500">
          {t('periodClosing.subtitle')}
        </p>
      </div>
      
      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-3">{t('periodClosing.selectPeriod')}</h2>
        <div className="flex flex-wrap gap-2">
          {periodOptions.slice(0, 6).map(opt => {
            const existing = periods.find(p => p.period_year === opt.year && p.period_month === opt.month);
            const isLocked = existing?.status === 'LOCKED';
            return (
              <button
                key={`${opt.year}-${opt.month}`}
                onClick={() => handleSelectPeriod(opt.year, opt.month)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedPeriod?.year === opt.year && selectedPeriod?.month === opt.month
                    ? 'bg-blue-600 text-white'
                    : isLocked
                    ? 'bg-green-100 text-green-800 hover:bg-green-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {MONTH_NAMES_TH[opt.month]} {opt.year}
                {isLocked && ' 🔒'}
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Period Detail */}
      {selectedPeriod && (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-lg font-medium text-gray-900">
                {MONTH_NAMES_TH[selectedPeriod.month]} {selectedPeriod.year}
              </h2>
              <p className="text-sm text-gray-500">
                {t('periodClosing.accountingPeriod')} {selectedPeriod.year}-{String(selectedPeriod.month).padStart(2, '0')}
              </p>
            </div>
            {periodDetail && getStatusBadge(periodDetail.status)}
          </div>
          
          {detailLoading ? (
            <div className="py-8">
              <SkeletonCard />
            </div>
          ) : periodDetail ? (
            <div>
              {/* Snapshot Data */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">{t('periodClosing.arBalance')}</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatCurrency(periodDetail.snapshot_data?.ar_total)}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">{t('periodClosing.cashReceived')}</p>
                  <p className="text-lg font-semibold text-green-600">
                    {formatCurrency(periodDetail.snapshot_data?.cash_received_total)}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">{t('periodClosing.expensesPaid')}</p>
                  <p className="text-lg font-semibold text-red-600">
                    {formatCurrency(periodDetail.snapshot_data?.expense_paid_total)}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">{t('periodClosing.expensesPending')}</p>
                  <p className="text-lg font-semibold text-yellow-600">
                    {formatCurrency(periodDetail.snapshot_data?.expense_pending_total)}
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">{t('periodClosing.creditNotes')}</p>
                  <p className="text-lg font-semibold text-purple-600">
                    {formatCurrency(periodDetail.snapshot_data?.credit_total)}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">{t('periodClosing.invoiceCount')}</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {periodDetail.snapshot_data?.invoice_count || 0} {t('periodClosing.items')}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">{t('periodClosing.occupiedHouses')}</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {periodDetail.snapshot_data?.house_count || 0} {t('periodClosing.units')}
                  </p>
                </div>
                {periodDetail.exists && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">{t('periodClosing.createdAt')}</p>
                    <p className="text-sm font-medium text-gray-900">
                      {formatDate(periodDetail.created_at)}
                    </p>
                  </div>
                )}
              </div>
              
              {periodDetail.notes && (
                <div className="bg-blue-50 rounded-lg p-3 mb-4">
                  <p className="text-xs text-blue-600 font-medium">{t('common.notes')}</p>
                  <p className="text-sm text-blue-800">{periodDetail.notes}</p>
                </div>
              )}
              
              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t">
                {periodDetail.status === 'LOCKED' ? (
                  <>
                    {isSuperAdmin && (
                      <button
                        onClick={() => setShowUnlockModal(true)}
                        className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition-colors"
                      >
                        {t('periodClosing.unlockBtn')}
                      </button>
                    )}
                    {isAdmin && (
                      <button
                        onClick={handleExport}
                        disabled={exporting}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {exporting ? t('periodClosing.exporting') : t('periodClosing.exportZip')}
                      </button>
                    )}
                    <button
                      onClick={() => handleViewLogs(selectedPeriod.year, selectedPeriod.month)}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                    >
                      {t('periodClosing.viewUnlockHistory')}
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setShowLockModal(true)}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                  >
                    {t('periodClosing.lockPeriodBtn')}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <p className="text-gray-500 py-4">{t('periodClosing.noData')}</p>
          )}
        </div>
      )}
      
      {/* Periods List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-4 py-3 border-b">
          <h2 className="text-lg font-medium text-gray-900">{t('periodClosing.historyTitle')}</h2>
        </div>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-600">{error}</div>
        ) : periods.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {t('periodClosing.noHistory')}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('periodClosing.periodLabel')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('common.status')}</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('periodClosing.arBalance')}</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('periodClosing.cashReceived')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('periodClosing.createdBy')}</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('periodClosing.createdDate')}</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {periods.map(period => (
                  <tr 
                    key={period.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleSelectPeriod(period.period_year, period.period_month)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-medium text-gray-900">
                        {MONTH_NAMES_TH[period.period_month]} {period.period_year}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {getStatusBadge(period.status)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                      {formatCurrency(period.snapshot_data?.ar_total)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm text-green-600">
                      {formatCurrency(period.snapshot_data?.cash_received_total)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {period.created_by_name || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(period.created_at)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewLogs(period.period_year, period.period_month);
                        }}
                        className="text-gray-400 hover:text-gray-600"
                        title={t("periodClosing.viewHistory")}
                      >
                        📋
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* Lock Modal */}
      {showLockModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('periodClosing.lockConfirmTitle')} {MONTH_NAMES_TH[selectedPeriod?.month]} {selectedPeriod?.year}
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              {t('periodClosing.lockWarning')}
            </p>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('periodClosing.notesOptional')}
              </label>
              <textarea
                value={lockNotes}
                onChange={(e) => setLockNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t("periodClosing.notesPlaceholder")}
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowLockModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleLockPeriod}
                disabled={actionLoading}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {actionLoading ? t('common.loading') : t('periodClosing.confirmLock')}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Unlock Modal */}
      {showUnlockModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('periodClosing.unlockConfirmTitle')} {MONTH_NAMES_TH[selectedPeriod?.month]} {selectedPeriod?.year}
            </h3>
            <p className="text-sm text-red-500 mb-4">
              {t('periodClosing.unlockWarning')}
            </p>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('periodClosing.unlockReasonLabel')} <span className="text-red-500">*</span>
              </label>
              <textarea
                value={unlockReason}
                onChange={(e) => setUnlockReason(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                placeholder={t("periodClosing.unlockReasonPlaceholder")}
                required
              />
              <p className="text-xs text-gray-400 mt-1">
                {unlockReason.length}/10 {t('periodClosing.minChars')}
              </p>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowUnlockModal(false);
                  setUnlockReason('');
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleUnlockPeriod}
                disabled={actionLoading || unlockReason.trim().length < 10}
                className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition-colors disabled:opacity-50"
              >
                {actionLoading ? t('common.loading') : t('periodClosing.confirmUnlock')}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Unlock Logs Modal */}
      {showLogsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                {t('periodClosing.unlockHistoryTitle')}
              </h3>
              <button
                onClick={() => setShowLogsModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            {unlockLogs.length === 0 ? (
              <p className="text-gray-500 text-center py-4">{t('periodClosing.noUnlockHistory')}</p>
            ) : (
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {unlockLogs.map(log => (
                  <div key={log.id} className="bg-gray-50 rounded-lg p-3">
                    <div className="flex justify-between items-start">
                      <span className="font-medium text-gray-900">{log.unlocked_by_name}</span>
                      <span className="text-xs text-gray-500">{formatDate(log.unlocked_at)}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{log.reason}</p>
                  </div>
                ))}
              </div>
            )}
            
            <div className="flex justify-end mt-4">
              <button
                onClick={() => setShowLogsModal(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </AdminPageWrapper>
  );
}

export default PeriodClosing;
