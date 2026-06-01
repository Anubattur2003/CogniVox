import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { setGlobalTokenExpirationHandler } from '../contexts/AuthContext';

interface AuthWrapperProps {
  children: React.ReactNode;
}

const AuthWrapper: React.FC<AuthWrapperProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Set up the global token expiration handler
    const handleTokenExpiration = () => {
      console.log('Handling token expiration, redirecting to login...');
      
      // Clear any existing query parameters or state
      const currentPath = location.pathname;
      
      // Only redirect if not already on login/signup/landing pages
      if (!['/login', '/signup', '/'].includes(currentPath)) {
        // Navigate to login with the current location as state for redirect after login
        navigate('/login', { 
          replace: true, 
          state: { from: location } 
        });
      }
    };

    // Register the handler globally
    setGlobalTokenExpirationHandler(handleTokenExpiration);

    // Cleanup function to remove the handler when component unmounts
    return () => {
      setGlobalTokenExpirationHandler(() => {});
    };
  }, [navigate, location]);

  return <>{children}</>;
};

export default AuthWrapper; 