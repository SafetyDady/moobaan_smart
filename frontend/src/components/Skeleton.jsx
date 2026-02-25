/**
 * Skeleton Loading Components
 *
 * Reusable shimmer/pulse placeholders to replace plain "Loading..." text.
 * All variants follow the existing dark theme (slate-700/800).
 */

/* ─── Base shimmer block ─── */
export function SkeletonBlock({ className = '' }) {
  return (
    <div className={`animate-pulse bg-slate-700 rounded ${className}`} />
  );
}

/* ─── Table row skeleton ─── */
export function SkeletonTableRow({ cols = 6 }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="animate-pulse bg-slate-700 rounded h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}

/**
 * SkeletonTable — renders multiple skeleton rows inside a <tbody>
 *
 * Usage:
 *   {loading ? (
 *     <SkeletonTable rows={5} cols={6} />
 *   ) : ( ... )}
 */
export function SkeletonTable({ rows = 5, cols = 6 }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonTableRow key={i} cols={cols} />
      ))}
    </>
  );
}

/* ─── Card skeleton (for dashboard cards) ─── */
export function SkeletonCard({ className = '' }) {
  return (
    <div className={`animate-pulse bg-slate-800 border border-slate-700 rounded-xl p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="bg-slate-700 rounded h-4 w-24" />
        <div className="bg-slate-700 rounded-full h-10 w-10" />
      </div>
      <div className="bg-slate-700 rounded h-8 w-32 mb-2" />
      <div className="bg-slate-700 rounded h-3 w-20" />
    </div>
  );
}

/* ─── Dashboard skeleton (4 cards + table) ─── */
export function SkeletonDashboard() {
  return (
    <div className="p-8 space-y-8">
      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
      {/* Table placeholder */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <div className="animate-pulse bg-slate-700 rounded h-5 w-48 mb-6" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="animate-pulse bg-slate-700 rounded h-4 w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── List item skeleton (for mobile views) ─── */
export function SkeletonListItem() {
  return (
    <div className="animate-pulse bg-slate-800 border border-slate-700 rounded-xl p-4 flex items-center gap-4">
      <div className="bg-slate-700 rounded-full h-10 w-10 flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="bg-slate-700 rounded h-4 w-3/4" />
        <div className="bg-slate-700 rounded h-3 w-1/2" />
      </div>
      <div className="bg-slate-700 rounded h-6 w-16" />
    </div>
  );
}

/* ─── Mobile list skeleton ─── */
export function SkeletonMobileList({ items = 4 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <SkeletonListItem key={i} />
      ))}
    </div>
  );
}

/* ─── Full page loading (replaces simple "Loading..." text) ─── */
export function SkeletonPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="animate-pulse">
        <div className="bg-slate-700 rounded h-8 w-64 mb-2" />
        <div className="bg-slate-700 rounded h-4 w-96" />
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <div className="space-y-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-pulse bg-slate-700 rounded h-4 w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}
