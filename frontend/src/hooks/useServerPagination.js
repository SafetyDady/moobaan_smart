/**
 * Phase 4 — Task 4.1: Server-side Pagination Hook
 * 
 * Drop-in replacement for usePagination when using server-side pagination.
 * Returns the same interface as usePagination so <Pagination /> component works unchanged.
 * 
 * Usage:
 *   const paged = useServerPagination({
 *     fetchFn: (params) => invoicesAPI.list(params),
 *     extraParams: { is_manual: false },
 *     initialPageSize: 25,
 *   });
 *   
 *   // paged.currentItems, paged.currentPage, paged.totalPages, etc.
 *   // paged.loading, paged.error
 *   // paged.reload() to refresh current page
 */
import { useState, useEffect, useCallback, useRef } from 'react';

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

/**
 * Server-side pagination hook
 * @param {object} options
 * @param {function} options.fetchFn - API function that accepts { page, page_size, ...extraParams }
 * @param {object} options.extraParams - Additional query params (filters, etc.)
 * @param {number} options.initialPageSize - Default page size (default: 25)
 * @param {boolean} options.autoLoad - Auto-load on mount (default: true)
 * @returns {object} Pagination state compatible with <Pagination /> component
 */
export function useServerPagination({
  fetchFn,
  extraParams = {},
  initialPageSize = 25,
  autoLoad = true,
} = {}) {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [items, setItems] = useState([]);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Track extraParams changes with JSON serialization
  const paramsRef = useRef(JSON.stringify(extraParams));
  const paramsChanged = JSON.stringify(extraParams) !== paramsRef.current;
  if (paramsChanged) {
    paramsRef.current = JSON.stringify(extraParams);
  }

  const fetchData = useCallback(async (page, size) => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        ...extraParams,
        page,
        page_size: size,
      };
      const response = await fetchFn(params);
      const data = response.data;

      // Server returns { items, total, page, page_size, total_pages }
      if (data && data.items !== undefined) {
        setItems(data.items);
        setTotalItems(data.total);
        setTotalPages(data.total_pages);
        setCurrentPage(data.page);
      } else if (Array.isArray(data)) {
        // Fallback: server returned array (no pagination)
        setItems(data);
        setTotalItems(data.length);
        setTotalPages(1);
        setCurrentPage(1);
      }
    } catch (err) {
      setError(err);
      console.error('Server pagination fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchFn, paramsRef.current]);

  // Auto-load on mount and when params change
  useEffect(() => {
    if (autoLoad) {
      // Reset to page 1 when filters change
      setCurrentPage(1);
      fetchData(1, pageSize);
    }
  }, [paramsRef.current, autoLoad]);

  // Fetch when page or pageSize changes (but not on initial mount — handled above)
  const isInitialMount = useRef(true);
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    fetchData(currentPage, pageSize);
  }, [currentPage, pageSize]);

  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + items.length, totalItems);

  return {
    // Compatible with <Pagination /> component
    currentItems: items,
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    startIndex,
    endIndex,
    onPageChange: (page) => setCurrentPage(page),
    onPageSizeChange: (size) => {
      setPageSize(size);
      setCurrentPage(1);
    },
    // Extra server-side helpers
    loading,
    error,
    reload: () => fetchData(currentPage, pageSize),
    // Raw data access
    rawData: items,
  };
}

export default useServerPagination;
