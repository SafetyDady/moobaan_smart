/**
 * Pay-in Status Utilities
 * 
 * Centralized rules for Pay-in status-based actions.
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md
 * 
 * AUTHORITATIVE SOURCE for:
 * - Which statuses allow edit/delete
 * - Status display text (Thai/English)
 * - Status badge colors
 */

// =============================================================================
// STATUS DEFINITIONS
// =============================================================================

/**
 * Pay-in Status enum values
 */
export const PayinStatus = {
  DRAFT: 'DRAFT',
  PENDING: 'PENDING',  // Legacy
  SUBMITTED: 'SUBMITTED',
  REJECTED_NEEDS_FIX: 'REJECTED_NEEDS_FIX',
  REJECTED: 'REJECTED',  // Legacy
  ACCEPTED: 'ACCEPTED',
};

/**
 * Pay-in Source enum values
 */
export const PayinSource = {
  RESIDENT: 'RESIDENT',
  ADMIN_CREATED: 'ADMIN_CREATED',
  LINE_RECEIVED: 'LINE_RECEIVED',
};

// =============================================================================
// STATUS-BASED ACTION RULES (Per Spec)
// =============================================================================

/**
 * Statuses where Resident CAN edit Pay-in
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Section 6.1
 * PENDING can be edited but NOT deleted
 */
const EDITABLE_STATUSES = [
  PayinStatus.DRAFT,
  PayinStatus.PENDING,           // Can edit, cannot delete
  PayinStatus.REJECTED_NEEDS_FIX,
  PayinStatus.REJECTED,          // Legacy - treat as editable
];

/**
 * Statuses where Resident CAN delete Pay-in (if not matched)
 * Rule: any unmatched, non-ACCEPTED pay-in can be deleted
 */
const DELETABLE_STATUSES = [
  PayinStatus.DRAFT,
  PayinStatus.PENDING,
  PayinStatus.SUBMITTED,
  PayinStatus.REJECTED_NEEDS_FIX,
  PayinStatus.REJECTED,          // Legacy
];

/**
 * Statuses that block creating new Pay-in
 * Per A.1.2 spec - Single-open rule:
 * - DRAFT, PENDING, REJECTED_NEEDS_FIX, SUBMITTED all block
 * - Only ACCEPTED allows creating new
 */
export const BLOCKING_STATUSES = [
  PayinStatus.DRAFT,
  PayinStatus.PENDING,
  PayinStatus.REJECTED_NEEDS_FIX,
  PayinStatus.REJECTED,  // Legacy
  PayinStatus.SUBMITTED,
];

/**
 * Statuses where Resident CANNOT edit/delete Pay-in
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Section 6.2
 */
const READONLY_STATUSES = [
  PayinStatus.SUBMITTED,
  PayinStatus.ACCEPTED,
];

/**
 * Check if Resident can edit this Pay-in
 * @param {object} payin - Pay-in object with status property
 * @returns {boolean}
 */
export const canEditPayin = (payin) => {
  if (!payin?.status) return false;
  return EDITABLE_STATUSES.includes(payin.status);
};

/**
 * Check if Resident can delete this Pay-in
 * Rule: deletable status AND not matched
 * @param {object} payin - Pay-in object with status property
 * @returns {boolean}
 */
export const canDeletePayin = (payin) => {
  if (!payin?.status) return false;
  if (payin.is_matched) return false; // matched pay-ins cannot be deleted
  return DELETABLE_STATUSES.includes(payin.status);
};

/**
 * Check if this pay-in blocks creating new ones
 * @param {object} payin - Pay-in object with status property
 * @returns {boolean}
 */
export const isBlockingPayin = (payin) => {
  if (!payin?.status) return false;
  return BLOCKING_STATUSES.includes(payin.status);
};

/**
 * Check if Pay-in is in read-only state
 * @param {object} payin - Pay-in object with status property
 * @returns {boolean}
 */
export const isReadOnlyPayin = (payin) => {
  if (!payin?.status) return true;
  return READONLY_STATUSES.includes(payin.status);
};

// =============================================================================
// STATUS DISPLAY (Thai Labels)
// =============================================================================

/**
 * Get Thai display text for status
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Appendix B
 */
export const getStatusText = (status) => {
  const texts = {
    [PayinStatus.DRAFT]: 'แบบร่าง',
    [PayinStatus.PENDING]: 'รอตรวจสอบ',
    [PayinStatus.SUBMITTED]: 'ส่งแล้ว',
    [PayinStatus.REJECTED_NEEDS_FIX]: 'ถูกปฏิเสธ - กรุณาแก้ไข',
    [PayinStatus.REJECTED]: 'ถูกปฏิเสธ',
    [PayinStatus.ACCEPTED]: 'ยืนยันแล้ว',
  };
  return texts[status] || status;
};

/**
 * Get English display text for status
 */
export const getStatusTextEn = (status) => {
  const texts = {
    [PayinStatus.DRAFT]: 'Draft',
    [PayinStatus.PENDING]: 'Pending Review',
    [PayinStatus.SUBMITTED]: 'Submitted',
    [PayinStatus.REJECTED_NEEDS_FIX]: 'Rejected - Please Fix',
    [PayinStatus.REJECTED]: 'Rejected',
    [PayinStatus.ACCEPTED]: 'Accepted',
  };
  return texts[status] || status;
};

// =============================================================================
// STATUS BADGE COLORS
// =============================================================================

/**
 * Get badge color class for status (Tailwind)
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Section 8.3
 */
export const getStatusBadgeColor = (status) => {
  const colors = {
    [PayinStatus.DRAFT]: 'bg-gray-500 text-white',
    [PayinStatus.PENDING]: 'bg-yellow-500 text-white',
    [PayinStatus.SUBMITTED]: 'bg-blue-500 text-white',
    [PayinStatus.REJECTED_NEEDS_FIX]: 'bg-red-500 text-white',
    [PayinStatus.REJECTED]: 'bg-red-500 text-white',
    [PayinStatus.ACCEPTED]: 'bg-green-500 text-white',
  };
  return colors[status] || 'bg-gray-500 text-white';
};

/**
 * Get legacy badge class (for desktop components using badge-* classes)
 */
export const getStatusBadgeClass = (status) => {
  const badges = {
    [PayinStatus.DRAFT]: 'badge-gray',
    [PayinStatus.PENDING]: 'badge-warning',
    [PayinStatus.SUBMITTED]: 'badge-info',
    [PayinStatus.REJECTED_NEEDS_FIX]: 'badge-danger',
    [PayinStatus.REJECTED]: 'badge-danger',
    [PayinStatus.ACCEPTED]: 'badge-success',
  };
  return badges[status] || 'badge-gray';
};

// =============================================================================
// SOURCE DISPLAY
// =============================================================================

/**
 * Get Thai display text for source
 * Per RESIDENT_PAYIN_MOBILE_ONLY_SPEC.md Section 9.2
 */
export const getSourceText = (source) => {
  const texts = {
    [PayinSource.RESIDENT]: 'สร้างโดยลูกบ้าน',
    [PayinSource.ADMIN_CREATED]: 'สร้างโดยผู้ดูแล',
    [PayinSource.LINE_RECEIVED]: 'รับจาก LINE',
  };
  return texts[source] || source || 'สร้างโดยลูกบ้าน';
};

/**
 * Get source badge color
 */
export const getSourceBadgeColor = (source) => {
  const colors = {
    [PayinSource.RESIDENT]: 'bg-blue-600 text-white',
    [PayinSource.ADMIN_CREATED]: 'bg-purple-600 text-white',
    [PayinSource.LINE_RECEIVED]: 'bg-green-600 text-white',
  };
  return colors[source] || 'bg-gray-600 text-white';
};

// =============================================================================
// DATE/TIME UTILITIES
// =============================================================================

/**
 * Safely parse a date value
 * @param {string|Date|null} value - Date value to parse
 * @returns {Date|null} - Parsed Date or null if invalid
 */
export const safeParseDate = (value) => {
  if (!value) return null;
  try {
    const date = new Date(value);
    // Check if valid date
    if (isNaN(date.getTime())) return null;
    return date;
  } catch {
    return null;
  }
};

/**
 * Format date for Thai display
 * @param {string|Date|null} value - Date value
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} - Formatted date or '-' if invalid
 */
export const formatThaiDate = (value, options = {}) => {
  const date = safeParseDate(value);
  if (!date) return '-';
  
  const defaultOptions = {
    day: 'numeric',
    month: 'short',
    year: '2-digit',
    ...options,
  };
  
  try {
    return date.toLocaleDateString('th-TH', defaultOptions);
  } catch {
    return '-';
  }
};

/**
 * Format time for Thai display
 * @param {string|Date|null} value - Date value with time
 * @returns {string} - Formatted time (HH:MM) or '-' if invalid
 */
export const formatThaiTime = (value) => {
  const date = safeParseDate(value);
  if (!date) return '-';
  
  try {
    return date.toLocaleTimeString('th-TH', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return '-';
  }
};

/**
 * Format transfer date/time from Pay-in data
 * Handles both transfer_datetime and legacy transfer_date + transfer_hour + transfer_minute
 * @param {object} payin - Pay-in object
 * @returns {{ date: string, time: string }} - Formatted date and time
 */
export const formatPayinDateTime = (payin) => {
  if (!payin) return { date: '-', time: '-' };
  
  // Try transfer_datetime first (new format)
  if (payin.transfer_datetime) {
    return {
      date: formatThaiDate(payin.transfer_datetime),
      time: formatThaiTime(payin.transfer_datetime),
    };
  }
  
  // Fall back to legacy format (transfer_date + hour + minute)
  const date = formatThaiDate(payin.transfer_date);
  const hour = String(payin.transfer_hour ?? 0).padStart(2, '0');
  const minute = String(payin.transfer_minute ?? 0).padStart(2, '0');
  const time = payin.transfer_date ? `${hour}:${minute}` : '-';
  
  return { date, time };
};
