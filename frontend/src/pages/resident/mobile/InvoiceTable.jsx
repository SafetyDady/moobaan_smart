/**
 * InvoiceTable Component
 * 
 * Displays invoices in a table format with:
 * - Status indicator line (left border)
 * - Color-coded amounts
 * - Status badges
 * - Mobile-optimized layout
 * 
 * @param {Array} invoices - Array of invoice objects
 */

import React, { useCallback, useMemo } from 'react';
import { FileText } from 'lucide-react';
import { t } from '../../../hooks/useLocale';
import { formatThaiDate, formatThaiTime } from '../../../utils/payinStatus';

// Monthly bills follow their billing cycle, even when created retrospectively.
// Special bills have no cycle, so place them by their due date.
const invoiceDisplayDate = (invoice) => (
  /^\d{4}-\d{2}$/.test(invoice.cycle || '')
    ? `${invoice.cycle}-01`
    : invoice.due_date || ''
);

const columns = 'grid grid-cols-[minmax(0,0.6fr)_minmax(0,1.35fr)_minmax(0,0.85fr)_minmax(0,1fr)_minmax(0,1.05fr)] gap-1 px-1 sm:gap-2 sm:px-3';

const InvoiceDate = ({ value }) => (
  <>
    <span className="sm:hidden">{formatThaiDate(value, { month: 'numeric' })}</span>
    <span className="hidden sm:inline">{formatThaiDate(value)}</span>
  </>
);

const InvoiceTable = ({ invoices = [] }) => {
  // Start at the newest row whenever the table opens, including after async loading.
  // Keep this ref stable so ordinary updates don't interrupt the user's scrolling.
  const startAtFirstRow = useCallback((element) => {
    if (element) element.scrollTop = 0;
  }, []);
  const sortedInvoices = useMemo(() => [...(invoices || [])].sort((a, b) => (
    invoiceDisplayDate(b).localeCompare(invoiceDisplayDate(a)) || b.id - a.id
  )), [invoices]);
  
  // Get status text in Thai
  const getStatusText = (status) => {
    const statusMap = {
      'PAID': t('invoiceTable.statusPaid'),
      'PARTIALLY_PAID': t('invoiceTable.statusPartial'),
      'CREDITED': t('invoiceTable.statusCredited'),
      'PENDING': t('invoiceTable.statusPending'),
      'OVERDUE': t('invoiceTable.statusOverdue'),
      'ISSUED': t('invoiceTable.statusIssued'),
      'DRAFT': t('invoiceTable.statusDraft'),
    };
    return statusMap[status?.toUpperCase()] || status || '-';
  };

  // Get status color classes
  const getStatusColor = (status) => {
    const upperStatus = status?.toUpperCase();
    switch (upperStatus) {
      case 'PAID':
        return {
          border: 'border-l-emerald-500',
          amount: 'text-emerald-400',
          badge: 'bg-emerald-900/30 text-emerald-400'
        };
      case 'OVERDUE':
        return {
          border: 'border-l-red-500',
          amount: 'text-red-400',
          badge: 'bg-red-900/30 text-red-400'
        };
      case 'PARTIALLY_PAID':
        return {
          border: 'border-l-amber-500',
          amount: 'text-amber-400',
          badge: 'bg-amber-900/30 text-amber-400'
        };
      case 'CREDITED':
        return {
          border: 'border-l-sky-500',
          amount: 'text-sky-400',
          badge: 'bg-sky-900/30 text-sky-400'
        };
      case 'PENDING':
        return {
          border: 'border-l-yellow-500',
          amount: 'text-yellow-400',
          badge: 'bg-yellow-900/30 text-yellow-400'
        };
      case 'ISSUED':
        return {
          border: 'border-l-slate-500',
          amount: 'text-slate-300',
          badge: 'bg-slate-700 text-slate-200'
        };
      default:
        return {
          border: 'border-l-gray-500',
          amount: 'text-gray-400',
          badge: 'bg-gray-900/30 text-gray-400'
        };
    }
  };

  // Empty state
  if (!invoices || invoices.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-8 text-center border border-gray-700">
        <FileText className="mx-auto text-gray-600 mb-3" size={48} />
        <p className="text-gray-400 font-medium">{t('invoiceTable.noInvoices')}</p>
      </div>
    );
  }

  return (
    <div
      ref={startAtFirstRow}
      className="w-full min-w-0 bg-gray-800 rounded-lg border border-gray-700 max-h-96 overflow-y-auto overscroll-contain focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-500"
      role="region"
      aria-label={t('mobileDashboard.invoiceTitle')}
      tabIndex={0}
      // Keep table scrolling from starting the page's pull-to-refresh gesture.
      onTouchStart={(event) => event.stopPropagation()}
    >
      <div className="w-full min-w-0">
      {/* Table Header */}
      <div className={`sticky top-0 z-10 ${columns} items-center bg-gray-750 py-3 border-b border-gray-700 border-l-4 border-l-transparent text-[11px] sm:text-xs leading-snug`}>
        <div className="min-w-0 text-gray-400">
          {t('invoiceTable.cycle')}
        </div>
        <div className="min-w-0 text-gray-400 text-right">
          {t('invoiceTable.amount')}
        </div>
        <div className="min-w-0 text-gray-400 text-center">
          {t('invoiceTable.dueDate')}
        </div>
        <div className="min-w-0 text-gray-400 text-center">
          {t('invoiceTable.lastPayment')}
        </div>
        <div className="min-w-0 text-gray-400 text-center">
          {t('invoiceTable.status')}
        </div>
      </div>

      {/* Table Rows */}
      <div>
        {sortedInvoices.map((invoice, index) => {
          const colors = getStatusColor(invoice.status);
          const isLast = index === sortedInvoices.length - 1;
          
          return (
            <div
              key={invoice.id || index}
              className={`
                relative ${columns} py-3
                border-l-4 ${colors.border}
                hover:bg-gray-750 transition-colors
                ${!isLast ? 'border-b border-gray-700' : ''}
              `}
            >
              {/* Cycle */}
              <div className="min-w-0 flex items-center">
                <span className="min-w-0 text-[11px] sm:text-xs text-white font-medium leading-snug">
                  {/^\d{4}-\d{2}$/.test(invoice.cycle || '') ? (
                    <time dateTime={invoice.cycle}>
                      <span className="sm:hidden">{formatThaiDate(`${invoice.cycle}-01`, { day: undefined })}</span>
                      <span className="hidden sm:inline">{invoice.cycle}</span>
                    </time>
                  ) : invoice.is_manual || invoice.cycle === 'MANUAL' ? t('invoices.manual') : invoice.cycle || '-'}
                </span>
              </div>

              {/* Amount */}
              <div className="min-w-0 flex items-center justify-end">
                <span className={`text-xs sm:text-base font-semibold tabular-nums whitespace-nowrap ${colors.amount}`}>
                  ฿{invoice.total?.toLocaleString() || '0'}
                </span>
              </div>

              {/* Due Date */}
              <div className="min-w-0 flex items-center justify-center text-center">
                <span className="text-[11px] sm:text-xs text-gray-400">
                  <InvoiceDate value={invoice.due_date} />
                </span>
              </div>

              {/* Latest confirmed receipt used for this invoice; Bangkok time. */}
              <div className="min-w-0 flex items-center justify-center text-center">
                {invoice.paid_at ? (
                  <time dateTime={invoice.paid_at} className="text-[11px] sm:text-xs text-gray-300 leading-snug">
                    <span className="block"><InvoiceDate value={invoice.paid_at} /></span>
                    <span className="block text-gray-400">{formatThaiTime(invoice.paid_at)}</span>
                  </time>
                ) : (
                  <span className="text-xs text-gray-500">-</span>
                )}
              </div>

              {/* Status Badge */}
              <div className="min-w-0 flex items-center justify-center">
                <span className={`
                  max-w-full px-1 sm:px-2 py-1 rounded-lg text-[11px] sm:text-xs font-semibold leading-snug whitespace-normal break-words text-center
                  ${colors.badge}
                `}>
                  {getStatusText(invoice.status)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
      </div>
    </div>
  );
};

export default InvoiceTable;
