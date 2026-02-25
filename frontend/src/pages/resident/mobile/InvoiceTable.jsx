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

import React from 'react';
import { FileText } from 'lucide-react';
import { t } from '../../../hooks/useLocale';

const InvoiceTable = ({ invoices = [] }) => {
  
  // Format Thai date
  const formatThaiDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const thaiMonths = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 
                        'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
    const day = date.getDate();
    const month = thaiMonths[date.getMonth()];
    const year = (date.getFullYear() + 543).toString().slice(-2);
    return `${day} ${month} ${year}`;
  };

  // Get status text in Thai
  const getStatusText = (status) => {
    const statusMap = {
      'PAID': t('invoiceTable.statusPaid'),
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
      case 'PENDING':
      case 'ISSUED':
        return {
          border: 'border-l-yellow-500',
          amount: 'text-yellow-400',
          badge: 'bg-yellow-900/30 text-yellow-400'
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
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-2 bg-gray-750 px-3 py-3 border-b border-gray-700">
        <div className="col-span-3 text-xs text-gray-400 uppercase tracking-wide">
          {t('invoiceTable.cycle')}
        </div>
        <div className="col-span-3 text-xs text-gray-400 uppercase tracking-wide text-right">
          {t('invoiceTable.amount')}
        </div>
        <div className="col-span-3 text-xs text-gray-400 uppercase tracking-wide text-center">
          {t('invoiceTable.dueDate')}
        </div>
        <div className="col-span-3 text-xs text-gray-400 uppercase tracking-wide text-center">
          {t('invoiceTable.status')}
        </div>
      </div>

      {/* Table Rows */}
      <div>
        {invoices.map((invoice, index) => {
          const colors = getStatusColor(invoice.status);
          const isLast = index === invoices.length - 1;
          
          return (
            <div
              key={invoice.id || index}
              className={`
                relative grid grid-cols-12 gap-2 px-3 py-3
                border-l-4 ${colors.border}
                hover:bg-gray-750 transition-colors
                ${!isLast ? 'border-b border-gray-700' : ''}
              `}
            >
              {/* Cycle */}
              <div className="col-span-3 flex items-center">
                <span className="text-sm text-white font-medium">
                  {invoice.cycle || '-'}
                </span>
              </div>

              {/* Amount */}
              <div className="col-span-3 flex items-center justify-end">
                <span className={`text-lg font-bold ${colors.amount}`}>
                  ฿{invoice.total?.toLocaleString() || '0'}
                </span>
              </div>

              {/* Due Date */}
              <div className="col-span-3 flex items-center justify-center">
                <span className="text-xs text-gray-400">
                  {formatThaiDate(invoice.due_date)}
                </span>
              </div>

              {/* Status Badge */}
              <div className="col-span-3 flex items-center justify-center">
                <span className={`
                  px-2 py-1 rounded-full text-xs font-semibold whitespace-nowrap
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
  );
};

export default InvoiceTable;
