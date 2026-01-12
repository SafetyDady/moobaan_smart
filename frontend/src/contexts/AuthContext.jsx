import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  // Check for existing auth on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Check localStorage first (remember me)
      let storedToken = localStorage.getItem('auth_token');
      let storedUser = localStorage.getItem('user');

      // If not in localStorage, check sessionStorage
      if (!storedToken) {
        storedToken = sessionStorage.getItem('auth_token');
        storedUser = sessionStorage.getItem('user');
      }

      if (storedToken && storedUser) {
        // Verify token is still valid
        try {
          const response = await api.get(`/api/auth/verify?token=${storedToken}`);
          if (response.data.valid) {
            setToken(storedToken);
            setUser(response.data.user);
          } else {
            // Token invalid, clear storage
            clearAuth();
          }
        } catch (error) {
          // Token expired or invalid
          clearAuth();
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = (authToken, userData, rememberMe = false) => {
    setToken(authToken);
    setUser(userData);

    // Store in appropriate storage
    if (rememberMe) {
      localStorage.setItem('auth_token', authToken);
      localStorage.setItem('user', JSON.stringify(userData));
    } else {
      sessionStorage.setItem('auth_token', authToken);
      sessionStorage.setItem('user', JSON.stringify(userData));
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await api.post('/api/auth/logout', null, {
          params: { token }
        });
      }
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      clearAuth();
    }
  };

  const clearAuth = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('user');
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
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
