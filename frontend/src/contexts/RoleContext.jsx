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

      // Get user info from token or AuthContext
      const userStr = localStorage.getItem('user');
      if (!userStr) {
        setLoading(false);
        return;
      }

      const user = JSON.parse(userStr);

      // If resident, get their house ID from members endpoint
      if (user.role === 'resident') {
        try {
          const membersRes = await fetch('http://127.0.0.1:8000/api/members', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (membersRes.ok) {
            const members = await membersRes.json();
            
            // Find member record for this user
            const userMember = members.find(m => m.user_id === user.id);
            if (userMember) {
              setCurrentHouseId(userMember.house_id);
            }
          }
        } catch (error) {
          console.error('Failed to load house membership:', error);
        }
      }
    } catch (error) {
      console.error('Failed to load user house:', error);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    currentRole,
    setCurrentRole,
    currentHouseId,
    setCurrentHouseId,
    isAdmin: currentRole === ROLES.SUPER_ADMIN,
    isAccounting: currentRole === ROLES.ACCOUNTING,
    isResident: currentRole === ROLES.RESIDENT,
    loading,
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
