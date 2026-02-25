# Progression Update — Phase 6: Village Dashboard UI Fix

**Date:** 2026-02-25  
**Branch:** `fix/village-dashboard-ui`  
**File Changed:** `frontend/src/pages/resident/mobile/VillageDashboard.jsx`

## Summary

This update addresses four visual/UX issues reported on the Village Dashboard page (`/resident/village`) that affected readability and data accuracy on mobile screens.

## Changes Made

### FIX 1: Income / Expense Cards — Side by Side Layout

The cards were already using `grid grid-cols-2` but long currency values caused overflow on narrow screens, pushing cards to separate rows. The fix adds `min-w-0` to each card container, `shrink-0` to icon containers, and `truncate` to text elements to prevent overflow while maintaining the two-column grid layout. Font size was also reduced from `text-xl` to `text-lg` for better fit.

### FIX 2: Debtor / Debt Cards — Side by Side Layout

Same overflow protection applied as FIX 1. Additionally, the "ครัวเรือน" (households) label was moved from inline with the number to a separate line below, matching the visual balance of the debt card. The debt amount now uses `maximumFractionDigits: 0` instead of `minimumFractionDigits: 2` to save horizontal space.

### FIX 3: Monthly Chart — Grouped Bar (was Stacked Bar)

The chart previously rendered income and expense as a single stacked bar per month, making it difficult to compare the two values visually. The fix changes this to a **grouped bar chart** where income (green) and expense (orange) appear as two separate bars side by side within each month.

Key code changes include modifying `chartMax` to use `flatMap` with individual values instead of summing income and expense, and replacing the stacked `flex-col` bar container with a `flex items-end gap-0.5` container holding two independently-scaled bars.

### FIX 4: Expense by Category — Exact Proportional Bars

The original code applied `Math.max(barW, m.total > 0 ? 2 : 0)` which added a minimum 2% width to any non-zero value. This caused bars with the same value (e.g., ฿38,814 in two different months) to appear at different widths depending on their position and the minimum width override.

The fix removes the minimum width hack entirely, using `style={{ width: \`${barW}%\` }}` directly. Since `barW` is calculated as `(m.total / globalMax) * 100`, identical values always produce identical bar widths — guaranteed mathematically.

The percentage change calculation was also improved to handle edge cases where the previous month was zero (showing ↑100%) and where both months are zero (hiding the change indicator).

## Testing Notes

All changes are purely frontend/visual. No API contracts or data structures were modified. The component continues to consume the same `/api/dashboard/village-summary` endpoint with the same response shape.
