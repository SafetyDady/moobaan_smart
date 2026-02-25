/**
 * Phase 2 - Task 2.2: Reusable Pagination Component
 * 
 * Client-side pagination that is "server-side ready":
 * - Accepts totalItems, currentPage, pageSize, onPageChange, onPageSizeChange
 * - Can be driven by either client-side slicing or server-side API params
 * - Fully localized via useLocale
 * - Responsive design for mobile/tablet/desktop
 * 
 * Usage:
 *   // Client-side: slice your data
 *   const paged = usePagination(allData);
 *   // paged.currentItems = items for current page
 *   // Render <Pagination {...paged} /> below your table
 */
import React from 'react';
import { t } from '../hooks/useLocale';

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

/**
 * Custom hook for client-side pagination logic
 * @param {Array} data - Full dataset
 * @param {number} initialPageSize - Default page size (default: 25)
 * @returns {object} Pagination state and helpers
 */
export function usePagination(data = [], initialPageSize = 25) {
  const [currentPage, setCurrentPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(initialPageSize);

  const totalItems = data.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  // Reset to page 1 when data length or pageSize changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [data.length, pageSize]);

  // Clamp currentPage within bounds using useEffect (avoids setState during render)
  React.useEffect(() => {
    setCurrentPage((prev) => {
      const maxPage = Math.max(1, Math.ceil(data.length / pageSize));
      return prev > maxPage ? maxPage : prev;
    });
  }, [data.length, pageSize]);

  const safePage = Math.min(currentPage, totalPages);
  const startIndex = (safePage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);
  const currentItems = data.slice(startIndex, endIndex);

  return {
    currentItems,
    currentPage: safePage,
    pageSize,
    totalItems,
    totalPages,
    startIndex,
    endIndex,
    onPageChange: setCurrentPage,
    onPageSizeChange: (size) => {
      setPageSize(size);
      setCurrentPage(1);
    },
  };
}

/**
 * Pagination UI Component
 */
export default function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  startIndex,
  endIndex,
  onPageChange,
  onPageSizeChange,
}) {
  if (totalItems === 0) return null;

  // Generate page numbers to show
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    
    if (totalPages <= maxVisible + 2) {
      // Show all pages
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      // Always show first page
      pages.push(1);
      
      // Calculate range around current page
      let start = Math.max(2, currentPage - 1);
      let end = Math.min(totalPages - 1, currentPage + 1);
      
      // Adjust if near the start
      if (currentPage <= 3) {
        end = Math.min(maxVisible, totalPages - 1);
      }
      // Adjust if near the end
      if (currentPage >= totalPages - 2) {
        start = Math.max(2, totalPages - maxVisible + 1);
      }
      
      if (start > 2) pages.push('...');
      for (let i = start; i <= end; i++) pages.push(i);
      if (end < totalPages - 1) pages.push('...');
      
      // Always show last page
      pages.push(totalPages);
    }
    
    return pages;
  };

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-4 px-2">
      {/* Info text */}
      <div className="text-sm text-gray-400 order-2 sm:order-1">
        {t('pagination.showing')} {startIndex + 1} {t('pagination.to')} {endIndex} {t('pagination.of')} {totalItems} {t('pagination.entries')}
      </div>

      {/* Page navigation */}
      <div className="flex items-center gap-1 order-1 sm:order-2">
        {/* First page */}
        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          className="px-2 py-1.5 text-sm rounded-md text-gray-400 hover:bg-slate-700 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title={t('pagination.first')}
        >
          «
        </button>
        
        {/* Previous page */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-2 py-1.5 text-sm rounded-md text-gray-400 hover:bg-slate-700 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title={t('pagination.previous')}
        >
          ‹
        </button>

        {/* Page numbers */}
        <div className="hidden sm:flex items-center gap-1">
          {getPageNumbers().map((page, idx) =>
            page === '...' ? (
              <span key={`ellipsis-${idx}`} className="px-2 py-1.5 text-gray-500 text-sm">
                …
              </span>
            ) : (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  page === currentPage
                    ? 'bg-blue-600 text-white font-medium'
                    : 'text-gray-400 hover:bg-slate-700 hover:text-white'
                }`}
              >
                {page}
              </button>
            )
          )}
        </div>

        {/* Mobile page indicator */}
        <span className="sm:hidden text-sm text-gray-400 px-2">
          {currentPage} / {totalPages}
        </span>

        {/* Next page */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-2 py-1.5 text-sm rounded-md text-gray-400 hover:bg-slate-700 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title={t('pagination.next')}
        >
          ›
        </button>

        {/* Last page */}
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          className="px-2 py-1.5 text-sm rounded-md text-gray-400 hover:bg-slate-700 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          title={t('pagination.last')}
        >
          »
        </button>
      </div>

      {/* Page size selector */}
      <div className="flex items-center gap-2 order-3">
        <label className="text-sm text-gray-400">{t('pagination.rowsPerPage')}</label>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="bg-slate-700 text-white text-sm rounded-md px-2 py-1.5 border border-slate-600 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        >
          {PAGE_SIZE_OPTIONS.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
