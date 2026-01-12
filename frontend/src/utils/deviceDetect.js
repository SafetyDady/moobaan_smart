/**
 * Detect if the user is on a mobile device
 * Uses combination of:
 * - User agent pattern matching
 * - Screen width
 * - Touch capability (pointer: coarse)
 * 
 * @returns {boolean} true if mobile device
 */
export const isMobileDevice = () => {
  // Check user agent
  const userAgent = navigator.userAgent || navigator.vendor || window.opera;
  
  // Mobile patterns
  const mobilePatterns = [
    /Android/i,
    /webOS/i,
    /iPhone/i,
    /iPad/i,
    /iPod/i,
    /BlackBerry/i,
    /Windows Phone/i
  ];
  
  // Check if any pattern matches
  const isMobileUA = mobilePatterns.some(pattern => userAgent.match(pattern));
  
  // Check screen width
  const isSmallScreen = window.innerWidth <= 768;
  
  // Check if device has touch capability (pointer: coarse)
  // This helps distinguish between:
  // - Desktop browser resized to mobile width (pointer: fine)
  // - Real mobile device (pointer: coarse)
  const isTouchDevice = window.matchMedia("(pointer: coarse)").matches;
  
  // Mobile device must satisfy:
  // 1. Mobile user agent OR
  // 2. Small screen AND touch capability
  return isMobileUA || (isSmallScreen && isTouchDevice);
};

/**
 * Detect if user is on iOS device
 * @returns {boolean} true if iOS
 */
export const isIOS = () => {
  const userAgent = navigator.userAgent || navigator.vendor || window.opera;
  return /iPad|iPhone|iPod/.test(userAgent) && !window.MSStream;
};

/**
 * Detect if user is on Android device
 * @returns {boolean} true if Android
 */
export const isAndroid = () => {
  const userAgent = navigator.userAgent || navigator.vendor || window.opera;
  return /android/i.test(userAgent);
};

/**
 * Check if device has touch capability
 * @returns {boolean} true if touch device
 */
export const isTouchDevice = () => {
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    window.matchMedia("(pointer: coarse)").matches
  );
};

/**
 * Get device type
 * @returns {'mobile'|'tablet'|'desktop'}
 */
export const getDeviceType = () => {
  const width = window.innerWidth;
  const hasTouch = isTouchDevice();
  
  if (width < 768 && hasTouch) {
    return 'mobile';
  } else if (width < 1024 && hasTouch) {
    return 'tablet';
  } else {
    return 'desktop';
  }
};

/**
 * Check if viewport height is reduced (keyboard is open)
 * Useful for detecting when mobile keyboard is visible
 * @returns {boolean} true if keyboard might be open
 */
export const isKeyboardOpen = () => {
  if (typeof window === 'undefined') return false;
  
  // On mobile, when keyboard opens, visualViewport.height < window.innerHeight
  if (window.visualViewport) {
    return window.visualViewport.height < window.innerHeight * 0.75;
  }
  
  return false;
};
