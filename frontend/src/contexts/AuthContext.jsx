import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

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
      // Check localStorage first 
      let storedToken = localStorage.getItem('auth_token');
      
      if (storedToken) {
        // Set Authorization header
        api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        
        // Verify token is still valid using /auth/me endpoint
        try {
          const response = await api.get('/api/auth/me');
          setToken(storedToken);
          setUser(response.data);
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

  const login = async (formData) => {
    try {
      const response = await api.post('/api/auth/login', formData);
      const { access_token } = response.data;

      // Store token in localStorage FIRST before setting state
      localStorage.setItem('auth_token', access_token);
      
      // Set Authorization header for future requests
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Get user info
      const userResponse = await api.get('/api/auth/me');
      
      // Set both token and user in state together
      setToken(access_token);
      setUser(userResponse.data);

      return true;
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await api.post('/api/auth/logout');
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
    delete api.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: !!user && (!!token || !!localStorage.getItem('auth_token')),
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
