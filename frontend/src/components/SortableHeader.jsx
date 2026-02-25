/**
 * Phase 2 - Task 2.4: Sortable Table Header Component
 * 
 * Provides clickable column headers with sort indicators.
 * 
 * Usage:
 *   const { sortConfig, requestSort, sortedData } = useSort(data);
 *   
 *   <thead>
 *     <tr>
 *       <SortableHeader
 *         label="ชื่อ"
 *         sortKey="full_name"
 *         sortConfig={sortConfig}
 *         onSort={requestSort}
 *       />
 *     </tr>
 *   </thead>
 */
import React from 'react';

/**
 * Custom hook for sorting data
 * @param {Array} data - The data array to sort
 * @param {object} initialConfig - Initial sort config { key, direction }
 * @returns {object} { sortConfig, requestSort, sortedData }
 */
export function useSort(data = [], initialConfig = { key: null, direction: null }) {
  const [sortConfig, setSortConfig] = React.useState(initialConfig);

  const requestSort = (key) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        // Cycle: asc -> desc -> none
        if (prev.direction === 'asc') return { key, direction: 'desc' };
        if (prev.direction === 'desc') return { key: null, direction: null };
      }
      return { key, direction: 'asc' };
    });
  };

  const sortedData = React.useMemo(() => {
    if (!sortConfig.key || !sortConfig.direction) return data;

    return [...data].sort((a, b) => {
      let aVal = a[sortConfig.key];
      let bVal = b[sortConfig.key];

      // Handle null/undefined
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      // Handle nested keys (e.g., "house.house_code")
      if (sortConfig.key.includes('.')) {
        const keys = sortConfig.key.split('.');
        aVal = keys.reduce((obj, k) => obj?.[k], a);
        bVal = keys.reduce((obj, k) => obj?.[k], b);
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
      }

      // Numeric comparison
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }

      // String comparison (case-insensitive)
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig]);

  return { sortConfig, requestSort, sortedData };
}

/**
 * Sortable Table Header Cell
 */
export default function SortableHeader({
  label,
  sortKey,
  sortConfig,
  onSort,
  className = '',
}) {
  const isActive = sortConfig?.key === sortKey;
  const direction = isActive ? sortConfig.direction : null;

  return (
    <th
      className={`cursor-pointer select-none hover:bg-slate-600/50 transition-colors ${className}`}
      onClick={() => onSort(sortKey)}
    >
      <div className="flex items-center gap-1.5">
        <span>{label}</span>
        <span className="inline-flex flex-col text-[10px] leading-none">
          <span className={`${direction === 'asc' ? 'text-blue-400' : 'text-gray-600'}`}>▲</span>
          <span className={`${direction === 'desc' ? 'text-blue-400' : 'text-gray-600'}`}>▼</span>
        </span>
      </div>
    </th>
  );
}
