/**
 * Phase 2 - Task 2.4: Empty State Component
 * 
 * Provides consistent, visually appealing empty states for tables and lists.
 * Supports two modes:
 * - Default: no data exists at all
 * - Filtered: data exists but current filters return no results
 */
import React from 'react';
import { ClipboardList } from 'lucide-react';
import { t } from '../hooks/useLocale';

export default function EmptyState({
  icon = <ClipboardList size={32} />,
  title,
  message,
  isFiltered = false,
  onClearFilters,
  colSpan = 1,
  asTableRow = true,
}) {
  const displayTitle = title || (isFiltered ? t('table.emptyFilteredTitle') : t('table.emptyTitle'));
  const displayMessage = message || (isFiltered ? t('table.emptyFilteredMessage') : t('table.emptyMessage'));

  const content = (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="text-4xl mb-3 opacity-60">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-300 mb-1">{displayTitle}</h3>
      <p className="text-sm text-gray-500 text-center max-w-sm">{displayMessage}</p>
      {isFiltered && onClearFilters && (
        <button
          onClick={onClearFilters}
          className="mt-4 px-4 py-2 text-sm bg-slate-700 hover:bg-slate-600 text-blue-400 rounded-lg transition-colors border border-slate-600"
        >
          {t('table.clearFilters')}
        </button>
      )}
    </div>
  );

  if (asTableRow) {
    return (
      <tr>
        <td colSpan={colSpan}>{content}</td>
      </tr>
    );
  }

  return content;
}
