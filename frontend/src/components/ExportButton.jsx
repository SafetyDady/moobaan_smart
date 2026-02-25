import { useState } from 'react';
import { Download, FileSpreadsheet, FileText, ChevronDown } from 'lucide-react';
import { api } from '../api/client';
import { t } from '../hooks/useLocale';

/**
 * Phase 5.2: ExportButton Component
 * 
 * Dropdown button for exporting report data as PDF or Excel.
 * 
 * Usage:
 *   <ExportButton reportType="invoices" period="2026-01" />
 *   <ExportButton reportType="houses" />
 * 
 * Props:
 *   - reportType: "invoices" | "payins" | "houses" | "members" | "expenses"
 *   - period: optional YYYY-MM filter
 *   - status: optional status filter
 *   - className: optional additional CSS classes
 */
export default function ExportButton({ reportType, period, status, className = '' }) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(null); // 'pdf' or 'xlsx'

  const handleExport = async (format) => {
    setLoading(format);
    setIsOpen(false);

    try {
      const params = { format };
      if (period) params.period = period;
      if (status) params.status = status;

      const response = await api.get(`/api/reports/export/${reportType}`, {
        params,
        responseType: 'blob',
      });

      // Extract filename from Content-Disposition header
      const disposition = response.headers['content-disposition'];
      let filename = `${reportType}_export.${format}`;
      if (disposition) {
        const match = disposition.match(/filename="?([^";\n]+)"?/);
        if (match) filename = match[1];
      }

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      alert(t('common.exportFailed') || 'Export failed');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
      >
        {loading ? (
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <Download size={16} />
        )}
        <span>{t('common.export')}</span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-1 w-44 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-20 overflow-hidden">
            <button
              onClick={() => handleExport('xlsx')}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            >
              <FileSpreadsheet size={16} className="text-green-400" />
              <span>Excel (.xlsx)</span>
            </button>
            <button
              onClick={() => handleExport('pdf')}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            >
              <FileText size={16} className="text-red-400" />
              <span>PDF (.pdf)</span>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
