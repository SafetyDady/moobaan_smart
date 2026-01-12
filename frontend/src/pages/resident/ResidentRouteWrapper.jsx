import { useEffect, useState } from 'react';
import { isMobileDevice } from '../../utils/deviceDetect';

// Desktop versions
import DesktopDashboard from './Dashboard';
import DesktopSubmitPayment from './SubmitPayment';

// Mobile versions
import MobileDashboard from './mobile/MobileDashboard';
import MobileSubmitPayment from './mobile/MobileSubmitPayment';

/**
 * Wrapper component that automatically routes to mobile or desktop version
 * based on device detection
 */
export const ResidentDashboardWrapper = () => {
  const [isMobile, setIsMobile] = useState(isMobileDevice());

  useEffect(() => {
    // Re-check on window resize
    const handleResize = () => {
      setIsMobile(isMobileDevice());
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Render mobile or desktop version
  return isMobile ? <MobileDashboard /> : <DesktopDashboard />;
};

export const ResidentSubmitPaymentWrapper = () => {
  const [isMobile, setIsMobile] = useState(isMobileDevice());

  useEffect(() => {
    // Re-check on window resize
    const handleResize = () => {
      setIsMobile(isMobileDevice());
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Render mobile or desktop version
  return isMobile ? <MobileSubmitPayment /> : <DesktopSubmitPayment />;
};
