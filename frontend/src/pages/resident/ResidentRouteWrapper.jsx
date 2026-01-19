/**
 * Resident Route Wrappers
 * 
 * IMPORTANT: Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Section 2.1:
 * "Resident Desktop UI is intentionally removed by design."
 * 
 * These wrappers ALWAYS render mobile components regardless of device.
 * Desktop browsers will see the mobile layout with max-width constraint.
 */

// Mobile versions ONLY - Desktop versions removed by design
import MobileDashboard from './mobile/MobileDashboard';
import MobileSubmitPayment from './mobile/MobileSubmitPayment';
import VillageDashboard from './mobile/VillageDashboard';

/**
 * Resident Dashboard - ALWAYS mobile layout
 * Per spec: "If accessed from desktop browser, Resident must see mobile responsive layout only"
 */
export const ResidentDashboardWrapper = () => {
  // MOBILE ONLY - No device detection needed
  // Desktop users see same mobile UI with max-width constraint
  return <MobileDashboard />;
};

/**
 * Resident Submit Payment - ALWAYS mobile layout
 * Per spec: "Desktop-specific layouts, tables, or hover interactions are forbidden"
 */
export const ResidentSubmitPaymentWrapper = () => {
  // MOBILE ONLY - No device detection needed
  return <MobileSubmitPayment />;
};

/**
 * Village Dashboard - ALWAYS mobile layout
 * Shows overall village financial statistics (PDPA compliant - no personal data)
 */
export const ResidentVillageDashboardWrapper = () => {
  // MOBILE ONLY - No device detection needed
  return <VillageDashboard />;
};
