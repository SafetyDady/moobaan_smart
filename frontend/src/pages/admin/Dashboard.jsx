import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI, api } from '../../api/client';
import { SkeletonDashboard } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';
import { 
  DollarSign, TrendingUp, TrendingDown, Home, 
  FileText, AlertTriangle, Users, CheckCircle,
  Server, Database, Clock, Loader2
} from 'lucide-react';
import AdminPageWrapper from '../../components/AdminPageWrapper';


export default function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);

  useEffect(() => {
    loadSummary();
    loadSystemStatus();
  }, []);

  const loadSummary = async () => {
    try {
      const response = await dashboardAPI.getSummary();
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to load summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSystemStatus = async () => {
    try {
      setStatusLoading(true);
      const response = await api.get('/api/system/status');
      setSystemStatus(response.data);
    } catch (error) {
      console.error('Failed to load system status:', error);
      setSystemStatus(null);
    } finally {
      setStatusLoading(false);
    }
  };

  if (loading) {
    return <SkeletonDashboard />;
  }

  const stats = [
    {
      name: t('dashboard.totalOutstanding'),
      value: `฿${summary?.total_outstanding?.toLocaleString() || 0}`,
      icon: DollarSign,
      color: 'text-red-400',
      borderColor: 'border-red-500',
      bgColor: 'bg-red-500/10',
    },
    {
      name: t('dashboard.totalIncome'),
      value: `฿${summary?.total_income?.toLocaleString() || 0}`,
      icon: TrendingUp,
      color: 'text-green-400',
      borderColor: 'border-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      name: t('dashboard.totalExpenses'),
      value: `฿${summary?.total_expenses?.toLocaleString() || 0}`,
      icon: TrendingDown,
      color: 'text-red-400',
      borderColor: 'border-red-500',
      bgColor: 'bg-red-500/10',
    },
    {
      name: t('dashboard.totalHouses'),
      value: `${summary?.total_houses || 0}/${summary?.active_houses || 0} ${t('dashboard.activeHouses')}`,
      icon: Home,
      color: 'text-blue-400',
      borderColor: 'border-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      name: t('dashboard.pendingInvoices'),
      value: summary?.pending_invoices || 0,
      icon: FileText,
      color: 'text-yellow-400',
      borderColor: 'border-yellow-500',
      bgColor: 'bg-yellow-500/10',
    },
    {
      name: t('dashboard.overdueInvoices'),
      value: summary?.overdue_invoices || 0,
      icon: AlertTriangle,
      color: 'text-orange-400',
      borderColor: 'border-orange-500',
      bgColor: 'bg-orange-500/10',
    },
  ];

  const quickActions = [
    {
      name: t('dashboard.manageHouses'),
      description: t('dashboard.manageHousesDesc'),
      path: '/admin/houses',
      icon: Home,
      color: 'bg-blue-600',
      hoverColor: 'hover:bg-blue-700',
    },
    {
      name: t('dashboard.manageMembers'),
      description: t('dashboard.manageMembersDesc'),
      path: '/admin/members',
      icon: Users,
      color: 'bg-purple-600',
      hoverColor: 'hover:bg-purple-700',
    },
    {
      name: t('dashboard.acceptPayins'),
      description: t('dashboard.acceptPayinsDesc'),
      path: '/admin/payins',
      icon: CheckCircle,
      color: 'bg-green-600',
      hoverColor: 'hover:bg-green-700',
    },
    {
      name: t('dashboard.reviewExpenses'),
      description: t('dashboard.reviewExpensesDesc'),
      path: '/admin/expenses',
      icon: TrendingDown,
      color: 'bg-red-600',
      hoverColor: 'hover:bg-red-700',
    },
  ];

  // Helper to get status badge
  const getStatusBadge = (status, type) => {
    if (statusLoading) {
      return (
        <span className="px-3 py-1 bg-slate-600/30 text-gray-400 rounded-full text-sm font-medium flex items-center gap-1">
          <Loader2 size={12} className="animate-spin" />
          {t('common.loading')}
        </span>
      );
    }
    
    if (!systemStatus) {
      return (
        <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm font-medium">
          {t('common.error')}
        </span>
      );
    }

    if (type === 'backend') {
      const isOnline = systemStatus.backend_api?.status === 'online';
      return (
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          isOnline ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
        }`}>
          {isOnline ? t('common.online') : t('common.offline')}
        </span>
      );
    }

    if (type === 'database') {
      const isConnected = systemStatus.database?.status === 'connected';
      const responseTime = systemStatus.database?.response_time_ms;
      return (
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {isConnected ? t('common.connected') : t('common.disconnected')}
          </span>
          {isConnected && responseTime != null && (
            <span className="text-xs text-gray-500">{responseTime}ms</span>
          )}
        </div>
      );
    }

    return null;
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">
          {t('dashboard.title')}
        </h1>
        <p className="text-gray-400">
          {t('dashboard.subtitle')}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div 
              key={stat.name} 
              className={`bg-slate-800 rounded-xl p-4 sm:p-6 border-l-4 ${stat.borderColor} shadow-lg hover:shadow-xl transition-shadow`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-gray-400 text-sm mb-2">{stat.name}</p>
                  <p className={`text-2xl sm:text-3xl font-bold ${stat.color} truncate`}>
                    {stat.value}
                  </p>
                </div>
                <div className={`w-12 h-12 sm:w-14 sm:h-14 ${stat.bgColor} rounded-lg flex items-center justify-center flex-shrink-0 ml-3`}>
                  <Icon className={`w-6 h-6 sm:w-8 sm:h-8 ${stat.color}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl sm:text-2xl font-bold text-white mb-6">{t('dashboard.quickActions')}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.name}
                to={action.path}
                className={`${action.color} ${action.hoverColor} rounded-xl p-4 sm:p-6 transition-all transform hover:scale-105 shadow-lg`}
              >
                <div className="flex items-center justify-center w-12 h-12 bg-white/20 rounded-lg mb-4">
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-bold text-white text-lg mb-2">{action.name}</h3>
                <p className="text-sm text-white/80">{action.description}</p>
              </Link>
            );
          })}
        </div>
      </div>

      {/* System Status — Phase 4.2: Real data from /api/system/status */}
      <div className="bg-slate-800 rounded-xl p-4 sm:p-6 shadow-lg">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">{t('dashboard.systemStatus')}</h2>
          <button
            onClick={loadSystemStatus}
            disabled={statusLoading}
            className="text-sm text-gray-400 hover:text-white transition-colors disabled:opacity-50"
            title={t('common.refresh')}
          >
            <Loader2 size={16} className={statusLoading ? 'animate-spin' : ''} />
          </button>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Server size={16} className="text-gray-400" />
              <span className="text-gray-300 font-medium">{t('dashboard.backendApi')}</span>
            </div>
            {getStatusBadge(systemStatus, 'backend')}
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Database size={16} className="text-gray-400" />
              <span className="text-gray-300 font-medium">{t('dashboard.database')}</span>
            </div>
            {getStatusBadge(systemStatus, 'database')}
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Clock size={16} className="text-gray-400" />
              <span className="text-gray-300 font-medium">{t('dashboard.uptime')}</span>
            </div>
            <span className="text-gray-400 text-sm">
              {statusLoading ? (
                <span className="flex items-center gap-1">
                  <Loader2 size={12} className="animate-spin" />
                  {t('common.loading')}
                </span>
              ) : systemStatus?.uptime?.human || '-'}
            </span>
          </div>
        </div>
      </div>
    </div>
    </AdminPageWrapper>
  );
}
