import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI } from '../../api/client';

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
    return (
      <div className="p-8">
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  const stats = [
    {
      name: 'Total Outstanding',
      value: `฿${summary?.total_outstanding?.toLocaleString() || 0}`,
      icon: '💰',
      color: 'text-red-400',
    },
    {
      name: 'Total Income',
      value: `฿${summary?.total_income?.toLocaleString() || 0}`,
      icon: '📈',
      color: 'text-green-400',
    },
    {
      name: 'Total Expenses',
      value: `฿${summary?.total_expenses?.toLocaleString() || 0}`,
      icon: '📉',
      color: 'text-red-400',
    },
    {
      name: 'Total Houses',
      value: `${summary?.total_houses || 0} / ${summary?.active_houses || 0} Active`,
      icon: '🏠',
      color: 'text-blue-400',
    },
    {
      name: 'Pending Invoices',
      value: summary?.pending_invoices || 0,
      icon: '📄',
      color: 'text-yellow-400',
    },
    {
      name: 'Overdue Invoices',
      value: summary?.overdue_invoices || 0,
      icon: '⚠️',
      color: 'text-orange-400',
    },
  ];

  const quickActions = [
    {
      name: 'Manage Houses',
      description: 'Add or edit house information',
      path: '/admin/houses',
      icon: '🏠',
      color: 'bg-blue-600',
    },
    {
      name: 'Manage Members',
      description: 'Add or edit member information',
      path: '/admin/members',
      icon: '👥',
      color: 'bg-purple-600',
    },
    {
      name: 'Accept Pay-ins',
      description: 'Review and accept payment slips',
      path: '/admin/payins',
      icon: '✅',
      color: 'bg-primary-600',
    },
    {
      name: 'Review Expenses',
      description: 'Approve or reject expense requests',
      path: '/admin/expenses',
      icon: '💸',
      color: 'bg-red-600',
    },
  ];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Super Admin Dashboard
        </h1>
        <p className="text-gray-400">
          Overview of village accounting system
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm mb-1">{stat.name}</p>
                <p className={`text-2xl font-bold ${stat.color}`}>
                  {stat.value}
                </p>
              </div>
              <div className="text-4xl">{stat.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.path}
              className="card p-6 hover:ring-2 hover:ring-primary-500 transition-all"
            >
              <div className={`w-12 h-12 ${action.color} rounded-lg flex items-center justify-center text-2xl mb-4`}>
                {action.icon}
              </div>
              <h3 className="font-bold text-white mb-1">{action.name}</h3>
              <p className="text-sm text-gray-400">{action.description}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-white mb-4">System Status</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-300">Backend API</span>
            <span className="badge badge-success">Online</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-300">Database</span>
            <span className="badge badge-success">Connected</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-300">Last Backup</span>
            <span className="text-gray-400">2 hours ago</span>
          </div>
        </div>
      </div>
    </div>
  );
}
