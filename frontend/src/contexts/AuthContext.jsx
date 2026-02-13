import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

// Helper to check if CSRF cookie exists (indicates logged in via cookies)
function hasCsrfToken() {
  return document.cookie.includes('csrf_token=');
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuth, setIsAuth] = useState(false);

  // Check for existing auth on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Check if we have httpOnly cookie (via CSRF cookie presence)
      const hasAuthCookie = hasCsrfToken();
      
      if (hasAuthCookie) {
        // Try /api/auth/me first (for Admin/Accounting)
        // If it fails with 500, try /api/resident/me (for Resident OTP login)
        try {
          const response = await api.get('/api/auth/me');
          const data = response.data;
          
          // R.3: If resident has no house_id but has houses → redirect to select-house
          if (data.role === 'resident' && !data.house_id && data.houses?.length > 0) {
            console.log('[AuthContext] Resident has houses but no house_id → need select-house');
            setIsAuth(true);
            setUser(data);
            // Let RoleContext/ProtectedRoute handle the redirect
            return;
          }
          
          setIsAuth(true);
          setUser(data);
        } catch (error) {
          // PATCH-2 rev: If pending token → don't set auth, let ProtectedRoute redirect
          const detail = error.response?.data?.detail;
          if (detail?.code === 'HOUSE_NOT_SELECTED') {
            // Pending token — user needs to select house first
            // Don't set auth, loading will finish and ProtectedRoute will redirect to /login
            // User should navigate to /select-house via the LINE login flow
            setIsAuth(false);
            setUser(null);
            return;
          }
          
          // /api/auth/me failed - might be Resident, try /api/resident/me
          try {
            const residentResponse = await api.get('/api/resident/me');
            // Convert resident/me response to match user format
            const residentData = residentResponse.data;
            const membership = residentData.memberships?.[0];
            setIsAuth(true);
            setUser({
              id: residentData.user_id,
              phone: residentData.phone,
              role: 'resident',
              house_id: membership?.house_id || null,
              house_code: membership?.house_code || null,
              is_active: true,
            });
          } catch (residentError) {
            // Both failed - try refresh token
            try {
              await api.post('/api/auth/refresh');
              const response = await api.get('/api/auth/me');
              setIsAuth(true);
              setUser(response.data);
            } catch (refreshError) {
              clearAuth();
            }
          }
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (formData) => {
    try {
      // Login sets httpOnly cookies automatically
      await api.post('/api/auth/login', formData);
      
      // Get user info (cookie sent automatically)
      const userResponse = await api.get('/api/auth/me');
      const userData = userResponse.data;
      
      // Set auth state
      setIsAuth(true);
      setUser(userData);

      // Return user data so caller can determine redirect
      return userData;
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint (clears httpOnly cookies)
      await api.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      clearAuth();
    }
  };

  const clearAuth = () => {
    setIsAuth(false);
    setUser(null);
  };

  // Direct user setter for Resident OTP login (avoids race condition)
  // Called after /select-house success with user data
  const setResidentUser = (userData) => {
    setIsAuth(true);
    setUser(userData);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    checkAuth,  // For app init / page reload only
    setResidentUser,  // For Resident OTP login flow - direct state set
    // AUTHORITATIVE AUTH RULE: Cookie presence = authenticated
    // User state is for display/role info, not auth gate
    // This prevents race condition during page refresh
    isAuthenticated: isAuth || hasCsrfToken(),
    isAdmin: user?.role === 'super_admin',
    isAccounting: user?.role === 'accounting',
    isResident: user?.role === 'resident',
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
