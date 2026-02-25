import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI } from '../../api/client';
import { SkeletonDashboard } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';
import { 
  DollarSign, TrendingUp, TrendingDown, Home, 
  FileText, AlertTriangle, Users, CheckCircle 
} from 'lucide-react';
import AdminPageWrapper from '../../components/AdminPageWrapper';


export default function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSummary();
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

      {/* System Status */}
      <div className="bg-slate-800 rounded-xl p-4 sm:p-6 shadow-lg">
        <h2 className="text-xl font-bold text-white mb-6">{t('dashboard.systemStatus')}</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
            <span className="text-gray-300 font-medium">{t('dashboard.backendApi')}</span>
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
              {t('common.online')}
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
            <span className="text-gray-300 font-medium">{t('dashboard.database')}</span>
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
              {t('common.connected')}
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
            <span className="text-gray-300 font-medium">{t('dashboard.lastBackup')}</span>
            <span className="text-gray-400 text-sm">2 {t('dashboard.hoursAgo')}</span>
          </div>
        </div>
      </div>
    </div>
    </AdminPageWrapper>
  );
}
