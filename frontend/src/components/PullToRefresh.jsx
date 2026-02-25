import { useState, useRef, useCallback } from 'react';

/**
 * PullToRefresh — Reusable pull-to-refresh wrapper for mobile pages.
 *
 * Usage:
 *   <PullToRefresh onRefresh={loadData}>
 *     {children}
 *   </PullToRefresh>
 *
 * Props:
 *   onRefresh  — async function to call when user pulls down (must return a Promise)
 *   threshold  — pull distance in px to trigger refresh (default 80)
 *   children   — page content
 */
const PULL_THRESHOLD = 80;
const MAX_PULL = 120;

export default function PullToRefresh({ onRefresh, threshold = PULL_THRESHOLD, children }) {
  const [pulling, setPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  const startY = useRef(0);
  const currentY = useRef(0);
  const containerRef = useRef(null);

  const isAtTop = useCallback(() => {
    if (!containerRef.current) return true;
    // Walk up to find the scrollable parent (<main> in MobileLayout)
    let el = containerRef.current;
    while (el) {
      if (el.scrollTop > 0) return false;
      el = el.parentElement;
    }
    return true;
  }, []);

  const handleTouchStart = useCallback((e) => {
    if (refreshing) return;
    if (!isAtTop()) return;
    startY.current = e.touches[0].clientY;
    currentY.current = startY.current;
    setPulling(true);
  }, [refreshing, isAtTop]);

  const handleTouchMove = useCallback((e) => {
    if (!pulling || refreshing) return;
    currentY.current = e.touches[0].clientY;
    const diff = currentY.current - startY.current;

    if (diff > 0 && isAtTop()) {
      // Apply resistance: the further you pull, the harder it gets
      const distance = Math.min(diff * 0.5, MAX_PULL);
      setPullDistance(distance);
    } else {
      setPullDistance(0);
    }
  }, [pulling, refreshing, isAtTop]);

  const handleTouchEnd = useCallback(async () => {
    if (!pulling) return;
    setPulling(false);

    if (pullDistance >= threshold && onRefresh) {
      setRefreshing(true);
      setPullDistance(threshold * 0.6); // Keep indicator visible during refresh
      try {
        await onRefresh();
      } catch (err) {
        console.error('[PullToRefresh] onRefresh error:', err);
      } finally {
        setRefreshing(false);
        setPullDistance(0);
      }
    } else {
      setPullDistance(0);
    }
  }, [pulling, pullDistance, threshold, onRefresh]);

  const progress = Math.min(pullDistance / threshold, 1);
  const showIndicator = pullDistance > 10 || refreshing;

  return (
    <div
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      className="relative"
    >
      {/* Pull indicator */}
      {showIndicator && (
        <div
          className="flex items-center justify-center overflow-hidden transition-all duration-150"
          style={{ height: `${pullDistance}px` }}
        >
          <div className="flex flex-col items-center gap-1">
            <div
              className={`rounded-full h-6 w-6 border-2 border-primary-500 ${
                refreshing ? 'animate-spin border-t-transparent' : ''
              }`}
              style={
                !refreshing
                  ? { transform: `rotate(${progress * 360}deg)`, borderTopColor: 'transparent' }
                  : undefined
              }
            />
            <span className="text-xs text-gray-400">
              {refreshing
                ? 'กำลังโหลด...'
                : progress >= 1
                  ? 'ปล่อยเพื่อรีเฟรช'
                  : 'ดึงลงเพื่อรีเฟรช'}
            </span>
          </div>
        </div>
      )}

      {/* Page content — shifted down by pull distance */}
      <div
        style={{
          transform: pullDistance > 0 && !showIndicator ? `translateY(${pullDistance}px)` : undefined,
          transition: pulling ? 'none' : 'transform 0.2s ease-out',
        }}
      >
        {children}
      </div>
    </div>
  );
}
