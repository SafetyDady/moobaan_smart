/**
 * Phase 2 - Task 2.1: Localization Hook
 * 
 * Provides access to the Thai translation dictionary.
 * Usage: const { t } = useLocale();
 *        t('dashboard.title') => 'แดชบอร์ดผู้ดูแลระบบ'
 * 
 * Also supports nested access:
 *        t('expenses.paymentMethods.CASH') => 'เงินสด'
 */

import th from '../locales/th';

/**
 * Get a nested value from an object using dot notation
 * @param {object} obj - The object to traverse
 * @param {string} path - Dot-separated path (e.g., 'dashboard.title')
 * @param {string} fallback - Fallback value if path not found
 * @returns {string} The translated string or fallback
 */
function getNestedValue(obj, path, fallback) {
  const keys = path.split('.');
  let current = obj;
  
  for (const key of keys) {
    if (current === null || current === undefined || typeof current !== 'object') {
      return fallback || path;
    }
    current = current[key];
  }
  
  return current !== undefined && current !== null ? current : (fallback || path);
}

/**
 * Translation function - retrieves Thai text from the dictionary
 * @param {string} key - Dot-separated key path (e.g., 'dashboard.title')
 * @param {string} fallback - Optional fallback text
 * @returns {string} Translated text
 */
export function t(key, fallback) {
  return getNestedValue(th, key, fallback);
}

/**
 * Hook for components that need the translation function
 * @returns {{ t: function }} Object with translation function
 */
export default function useLocale() {
  return { t };
}
