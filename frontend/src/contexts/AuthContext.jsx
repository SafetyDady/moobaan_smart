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
        // Verify auth is still valid using /auth/me endpoint
        // Cookie is sent automatically with withCredentials: true
        try {
          const response = await api.get('/api/auth/me');
          setIsAuth(true);
          setUser(response.data);
        } catch (error) {
          // Token expired - try refresh
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

  const value = {
    user,
    loading,
    login,
    logout,
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
