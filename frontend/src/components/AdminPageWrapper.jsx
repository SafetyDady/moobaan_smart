/**
 * Phase 2 - Task 2.3: Admin Page Wrapper
 * 
 * Wraps admin page content with the MobileNav component.
 * Since we cannot modify App.jsx or Layout.jsx, each admin page
 * imports this wrapper to get mobile navigation support.
 * 
 * Usage in any admin page:
 *   import AdminPageWrapper from '../../components/AdminPageWrapper';
 *   // Then wrap your return JSX:
 *   return (
 *     <AdminPageWrapper>
 *       <div className="p-6">... your page content ...</div>
 *     </AdminPageWrapper>
 *   );
 */
import React from 'react';
import MobileNav from './MobileNav';

export default function AdminPageWrapper({ children }) {
  return (
    <>
      <MobileNav />
      {children}
    </>
  );
}
