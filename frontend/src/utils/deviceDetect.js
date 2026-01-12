/**
 * Detect if the user is on a mobile device
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
  
  // Also check screen width (fallback)
  const isMobileWidth = window.innerWidth <= 768;
  
  // Return true if either condition is met
  return isMobileUA || isMobileWidth;
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
 * Get device type
 * @returns {'mobile'|'tablet'|'desktop'}
 */
export const getDeviceType = () => {
  const width = window.innerWidth;
  
  if (width < 768) {
    return 'mobile';
  } else if (width < 1024) {
    return 'tablet';
  } else {
    return 'desktop';
  }
};
