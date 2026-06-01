import React, { createContext, useContext, useState, ReactNode } from 'react';
import { toast } from 'react-hot-toast';

interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  signup: (userData: SignupData) => Promise<boolean>;
  logout: () => void;
  handleTokenExpiration: () => void;
  validateToken: () => Promise<boolean>;
  loading: boolean;
  isAuthenticated: boolean;
}

interface SignupData {
  firstName?: string;
  lastName?: string;
  username?: string;
  email: string;
  password: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const clearAuthData = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    setUser(null);
    setToken(null);
  };

  const handleTokenExpiration = () => {
    console.log('Token expired, logging out user...');
    clearAuthData();
    toast.error('Your session has expired. Please log in again.');
  };

  const validateTokenManually = async (): Promise<boolean> => {
    // Mock validation - always return true for demo
    return !!token;
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    setLoading(true);
    try {
      // Mock login - simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // For demo purposes, accept any non-empty credentials
      if (username.trim() && password.trim()) {
        const mockUser: User = {
          id: '1',
          email: username.includes('@') ? username : `${username}@example.com`,
          username: username,
          firstName: 'Demo',
          lastName: 'User',
          role: 'user'
        };
        
        const mockToken = 'mock-jwt-token-' + Date.now();
        
        setUser(mockUser);
        setToken(mockToken);
        localStorage.setItem('auth_token', mockToken);
        localStorage.setItem('user_data', JSON.stringify(mockUser));
        
        toast.success('Welcome back!');
        return true;
      } else {
        throw new Error('Please enter valid credentials');
      }
    } catch (error) {
      console.error('Login error:', error);
      clearAuthData();
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (userData: SignupData): Promise<boolean> => {
    setLoading(true);
    try {
      // Mock signup - simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // For demo purposes, accept any valid-looking data
      if (userData.email && userData.password && userData.username) {
        toast.success('Account created successfully! Please sign in.');
        return true;
      } else {
        throw new Error('Please fill in all required fields');
      }
    } catch (error) {
      console.error('Signup error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearAuthData();
    toast.success('Logged out successfully');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    signup,
    logout,
    loading,
    isAuthenticated: !!token && !!user,
    handleTokenExpiration,
    validateToken: validateTokenManually,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 