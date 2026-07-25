import { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('omnimind_token');
      if (token) {
        // In a full app, we might verify token or fetch user profile here
        // For now, we'll just set a mock user if token exists
        setUser({ email: 'user@omnimind.ai' });
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    localStorage.setItem('omnimind_token', response.data.access_token);
    setUser({ email });
    return response.data;
  };

  const register = async (email, password, full_name) => {
    const response = await api.post('/auth/register', { email, password, full_name });
    // After register, you usually log them in, or just return success
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('omnimind_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
