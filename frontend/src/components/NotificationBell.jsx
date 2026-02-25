import { useState, useEffect, useRef } from 'react';
import { Bell, Check, CheckCheck, X, FileText, CreditCard, AlertTriangle, Info } from 'lucide-react';
import { api } from '../api/client';
import { t } from '../hooks/useLocale';

/**
 * Phase 5.1: NotificationBell Component
 * 
 * Displays a bell icon with unread count badge.
 * Clicking opens a dropdown with notification list.
 * 
 * Usage: <NotificationBell />
 * Place in Layout header or MobileNav.
 */
export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  // Poll unread count every 30 seconds
  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const res = await api.get('/api/notifications/count');
      setUnreadCount(res.data.unread_count || 0);
    } catch (err) {
      // Silently fail — notification count is non-critical
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/notifications', { params: { limit: 20 } });
      setNotifications(res.data.items || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    if (!isOpen) {
      fetchNotifications();
    }
    setIsOpen(!isOpen);
  };

  const handleMarkRead = async (id) => {
    try {
      await api.post(`/api/notifications/${id}/read`);
      setNotifications(prev =>
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/api/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'INVOICE_CREATED':
      case 'INVOICE_OVERDUE':
        return <FileText size={16} className="text-blue-400" />;
      case 'PAYIN_SUBMITTED':
      case 'PAYIN_ACCEPTED':
        return <CreditCard size={16} className="text-green-400" />;
      case 'PAYIN_REJECTED':
        return <AlertTriangle size={16} className="text-red-400" />;
      default:
        return <Info size={16} className="text-gray-400" />;
    }
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHr = Math.floor(diffMs / 3600000);
    const diffDay = Math.floor(diffMs / 86400000);

    if (diffMin < 1) return t('notifications.justNow');
    if (diffMin < 60) return `${diffMin} ${t('notifications.minutesAgo')}`;
    if (diffHr < 24) return `${diffHr} ${t('notifications.hoursAgo')}`;
    if (diffDay < 7) return `${diffDay} ${t('notifications.daysAgo')}`;
    return date.toLocaleDateString('th-TH', { day: 'numeric', month: 'short' });
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={handleToggle}
        className="relative p-2 text-gray-400 hover:text-white transition-colors"
        aria-label={t('notifications.title')}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 max-h-96 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-white">{t('notifications.title')}</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                  title={t('notifications.markAllRead')}
                >
                  <CheckCheck size={14} />
                  {t('notifications.markAllRead')}
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-500 hover:text-gray-300"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Notification List */}
          <div className="overflow-y-auto max-h-80">
            {loading ? (
              <div className="p-4 text-center text-gray-500 text-sm">
                {t('common.loading')}
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500 text-sm">
                <Bell size={24} className="mx-auto mb-2 opacity-50" />
                {t('notifications.empty')}
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`flex items-start gap-3 px-4 py-3 border-b border-gray-700/50 hover:bg-gray-700/50 transition-colors cursor-pointer ${
                    !notif.is_read ? 'bg-gray-700/30' : ''
                  }`}
                  onClick={() => !notif.is_read && handleMarkRead(notif.id)}
                >
                  {/* Icon */}
                  <div className="mt-0.5 flex-shrink-0">
                    {getIcon(notif.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${!notif.is_read ? 'text-white font-medium' : 'text-gray-400'}`}>
                      {notif.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">
                      {notif.message}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      {formatTime(notif.created_at)}
                    </p>
                  </div>

                  {/* Unread dot */}
                  {!notif.is_read && (
                    <div className="flex-shrink-0 mt-1.5">
                      <div className="w-2 h-2 bg-blue-500 rounded-full" />
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
