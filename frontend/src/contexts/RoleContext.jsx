import { createContext, useContext, useState, useEffect } from 'react';

const RoleContext = createContext();

export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ACCOUNTING: 'accounting',
  RESIDENT: 'resident',
};

export function RoleProvider({ children }) {
  const [currentRole, setCurrentRole] = useState(ROLES.SUPER_ADMIN);
  const [currentHouseId, setCurrentHouseId] = useState(null);
  const [currentHouseCode, setCurrentHouseCode] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserHouse();
  }, []);

  const loadUserHouse = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setLoading(false);
        return;
      }

      // Get user info from /api/auth/me endpoint
      try {
        const response = await fetch('http://127.0.0.1:8000/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const userData = await response.json();
          console.log('✅ RoleContext - User data from /api/auth/me:', userData);
          
          // Set role
          setCurrentRole(userData.role);
          
          // Set house_id and house_code if resident
          if (userData.role === 'resident') {
            if (userData.house_id) {
              setCurrentHouseId(userData.house_id);
              setCurrentHouseCode(userData.house_code || null);
              console.log('✅ RoleContext - Set currentHouseId:', userData.house_id);
              console.log('✅ RoleContext - Set currentHouseCode:', userData.house_code);
            } else {
              console.warn('⚠️ RoleContext - Resident has no house_id!');
              console.warn('⚠️ This user may not be linked to a house via HouseMember table');
              console.warn('⚠️ User data:', userData);
            }
          }
        } else {
          console.error('❌ RoleContext - Failed to fetch user data:', response.status);
        }
      } catch (error) {
        console.error('❌ RoleContext - Failed to load user data:', error);
      }
    } catch (error) {
      console.error('❌ RoleContext - Outer error:', error);
    } finally {
      setLoading(false);
    }
  };

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
    loading,
  };
  
  // Debug logging for troubleshooting
  console.log('🔍 RoleContext Value:', {
    currentRole,
    isAdmin: currentRole === ROLES.SUPER_ADMIN,
    isAccounting: currentRole === ROLES.ACCOUNTING,
    isResident: currentRole === ROLES.RESIDENT,
    ROLES
  });

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}

export function useRole() {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error('useRole must be used within RoleProvider');
  }
  return context;
}
