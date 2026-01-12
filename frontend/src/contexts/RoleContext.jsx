import { createContext, useContext, useState } from 'react';

const RoleContext = createContext();

export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ACCOUNTING: 'accounting',
  RESIDENT: 'resident',
};

export function RoleProvider({ children }) {
  // Mock role - in production this would come from auth
  const [currentRole, setCurrentRole] = useState(ROLES.SUPER_ADMIN);
  const [currentHouseId, setCurrentHouseId] = useState(1); // For resident role

  const value = {
    currentRole,
    setCurrentRole,
    currentHouseId,
    setCurrentHouseId,
    isAdmin: currentRole === ROLES.SUPER_ADMIN,
    isAccounting: currentRole === ROLES.ACCOUNTING,
    isResident: currentRole === ROLES.RESIDENT,
  };

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error('useRole must be used within RoleProvider');
  }
  return context;
}
