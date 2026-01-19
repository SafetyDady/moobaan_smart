import { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

const RoleContext = createContext();

export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ACCOUNTING: 'accounting',
  RESIDENT: 'resident',
};

export function RoleProvider({ children }) {
  const { user, loading: authLoading } = useAuth();
  const [currentRole, setCurrentRole] = useState(null);
  const [currentHouseId, setCurrentHouseId] = useState(null);
  const [currentHouseCode, setCurrentHouseCode] = useState(null);
  const [loading, setLoading] = useState(true);

  // Sync role/house data from AuthContext user
  useEffect(() => {
    if (authLoading) {
      return; // Wait for auth to finish loading
    }

    if (user) {
      console.log('✅ RoleContext - Syncing from AuthContext user:', user);
      setCurrentRole(user.role);
      
      if (user.role === 'resident') {
        if (user.house_id) {
          setCurrentHouseId(user.house_id);
          setCurrentHouseCode(user.house_code || null);
          console.log('✅ RoleContext - Set currentHouseId:', user.house_id);
          console.log('✅ RoleContext - Set currentHouseCode:', user.house_code);
        } else {
          console.warn('⚠️ RoleContext - Resident has no house_id!');
          setCurrentHouseId(null);
          setCurrentHouseCode(null);
        }
      } else {
        // Non-resident: clear house data
        setCurrentHouseId(null);
        setCurrentHouseCode(null);
      }
    } else {
      // No user: reset everything
      console.log('⚠️ RoleContext - No user, resetting state');
      setCurrentRole(null);
      setCurrentHouseId(null);
      setCurrentHouseCode(null);
    }
    
    setLoading(false);
  }, [user, authLoading]);

  const value = {
    currentRole,
    setCurrentRole,
    currentHouseId,
    setCurrentHouseId,
    currentHouseCode,
    setCurrentHouseCode,
    isAdmin: currentRole === ROLES.SUPER_ADMIN,
    isAccounting: currentRole === ROLES.ACCOUNTING,
    isResident: currentRole === ROLES.RESIDENT,
    loading: loading || authLoading,
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
