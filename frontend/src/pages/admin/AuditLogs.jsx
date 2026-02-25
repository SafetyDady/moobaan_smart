import { useState, useEffect } from 'react';
import { ClipboardList, FileDown, Home, RefreshCw, Filter } from 'lucide-react';
import { api } from '../../api/client';
import { t } from '../../hooks/useLocale';
import { SkeletonTable } from '../../components/Skeleton';
import EmptyState from '../../components/EmptyState';
import AdminPageWrapper from '../../components/AdminPageWrapper';

/**
 * Phase 5.3: Audit Log UI
 * 
 * Admin page to view audit logs:
 * - Tab 1: Export Audit Logs (who exported what and when)
 * - Tab 2: House Event Logs (resident house selection/switch)
 */
export default function AuditLogs() {
  const [activeTab, setActiveTab] = useState('exports');
  const [exportLogs, setExportLogs] = useState([]);
  const [houseLogs, setHouseLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [daysFilter, setDaysFilter] = useState(30);

  useEffect(() => {
    if (activeTab === 'exports') {
      fetchExportLogs();
    } else {
      fetchHouseLogs();
    }
  }, [activeTab, eventTypeFilter, daysFilter]);

  const fetchExportLogs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/audit-logs/exports', {
        params: { page: 1, page_size: 50 }
      });
      setExportLogs(res.data.items || []);
    } catch (err) {
      console.error('Failed to fetch export logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchHouseLogs = async () => {
    setLoading(true);
    try {
      const params = { page: 1, page_size: 50, days: daysFilter };
      if (eventTypeFilter) params.event_type = eventTypeFilter;
      const res = await api.get('/api/audit-logs/house-events', { params });
      setHouseLogs(res.data.items || []);
    } catch (err) {
      console.error('Failed to fetch house logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('th-TH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getEventBadge = (eventType) => {
    switch (eventType) {
      case 'HOUSE_SELECTED':
        return <span className="px-2 py-0.5 text-xs rounded bg-blue-500/20 text-blue-400">{t('auditLog.houseSelected')}</span>;
      case 'HOUSE_SWITCH':
        return <span className="px-2 py-0.5 text-xs rounded bg-orange-500/20 text-orange-400">{t('auditLog.houseSwitch')}</span>;
      default:
        return <span className="px-2 py-0.5 text-xs rounded bg-gray-500/20 text-gray-400">{eventType}</span>;
    }
  };

  const handleRefresh = () => {
    if (activeTab === 'exports') {
      fetchExportLogs();
    } else {
      fetchHouseLogs();
    }
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">
            <ClipboardList size={24} className="inline mr-2" />
            {t('auditLog.title')}
          </h1>
          <p className="text-gray-400">{t('auditLog.title')}</p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
        >
          <RefreshCw size={16} />
          {t('common.refresh')}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('exports')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors ${
            activeTab === 'exports'
              ? 'bg-primary-600 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          <FileDown size={16} />
          {t('auditLog.exportLogs')}
        </button>
        <button
          onClick={() => setActiveTab('house-events')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors ${
            activeTab === 'house-events'
              ? 'bg-primary-600 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          <Home size={16} />
          {t('auditLog.houseLogs')}
        </button>
      </div>

      {/* Filters for house events */}
      {activeTab === 'house-events' && (
        <div className="card p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                <Filter size={14} className="inline mr-1" />
                {t('auditLog.filterByType')}
              </label>
              <select
                value={eventTypeFilter}
                onChange={(e) => setEventTypeFilter(e.target.value)}
                className="input w-full"
              >
                <option value="">{t('auditLog.allTypes')}</option>
                <option value="HOUSE_SELECTED">{t('auditLog.houseSelected')}</option>
                <option value="HOUSE_SWITCH">{t('auditLog.houseSwitch')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">{t('auditLog.period')}</label>
              <select
                value={daysFilter}
                onChange={(e) => setDaysFilter(Number(e.target.value))}
                className="input w-full"
              >
                <option value={7}>7 {t('auditLog.daysAgo') || 'days'}</option>
                <option value={30}>30 {t('auditLog.daysAgo') || 'days'}</option>
                <option value={90}>90 {t('auditLog.daysAgo') || 'days'}</option>
                <option value={365}>365 {t('auditLog.daysAgo') || 'days'}</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <SkeletonTable rows={5} cols={5} />
      ) : activeTab === 'exports' ? (
        /* Export Logs Table */
        exportLogs.length === 0 ? (
          <EmptyState
            icon={<FileDown size={32} />}
            title={t('auditLog.noLogs')}
            message={t('auditLog.noLogs')}
          />
        ) : (
          <div className="card overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">#</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.user')}</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.period')}</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.exportType')}</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.reportsIncluded')}</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.timestamp')}</th>
                </tr>
              </thead>
              <tbody>
                {exportLogs.map((log, idx) => (
                  <tr key={log.id} className="border-b border-gray-700/50 hover:bg-slate-700/30">
                    <td className="p-4 text-gray-500 text-sm">{idx + 1}</td>
                    <td className="p-4 text-white text-sm">{log.user_name || '-'}</td>
                    <td className="p-4 text-gray-300 text-sm">{log.from_period} → {log.to_period}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 text-xs rounded bg-green-500/20 text-green-400 uppercase">
                        {log.export_type}
                      </span>
                    </td>
                    <td className="p-4 text-gray-400 text-sm max-w-xs truncate">{log.reports_included}</td>
                    <td className="p-4 text-gray-400 text-sm">{formatDate(log.exported_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        /* House Event Logs Table */
        houseLogs.length === 0 ? (
          <EmptyState
            icon={<Home size={32} />}
            title={t('auditLog.noLogs')}
            message={t('auditLog.noLogs')}
          />
        ) : (
          <div className="card overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">#</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.eventType')}</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.user')}</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.details')}</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">IP</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">{t('auditLog.timestamp')}</th>
                </tr>
              </thead>
              <tbody>
                {houseLogs.map((log, idx) => (
                  <tr key={log.id} className="border-b border-gray-700/50 hover:bg-slate-700/30">
                    <td className="p-4 text-gray-500 text-sm">{idx + 1}</td>
                    <td className="p-4">{getEventBadge(log.event_type)}</td>
                    <td className="p-4 text-white text-sm">User #{log.user_id}</td>
                    <td className="p-4 text-gray-300 text-sm">
                      {log.event_type === 'HOUSE_SWITCH' ? (
                        <span>
                          {t('auditLog.fromHouse')} <span className="text-orange-400">{log.from_house_code || '-'}</span>
                          {' → '}
                          {t('auditLog.toHouse')} <span className="text-green-400">{log.to_house_code || '-'}</span>
                        </span>
                      ) : (
                        <span>
                          {t('auditLog.houseSelected')}: <span className="text-blue-400">{log.house_code || '-'}</span>
                        </span>
                      )}
                    </td>
                    <td className="p-4 text-gray-500 text-sm font-mono">{log.ip_address || '-'}</td>
                    <td className="p-4 text-gray-400 text-sm">{formatDate(log.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
    </AdminPageWrapper>
  );
}
