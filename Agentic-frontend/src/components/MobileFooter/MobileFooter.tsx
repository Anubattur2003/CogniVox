import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Compass, Box, BookOpen, LogOut } from 'lucide-react';
import { useTheme } from '../../../src/contexts/ThemeContext';
import { useAuth } from '../../../src/contexts/AuthContext';

const MobileFooter: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, isDarkMode } = useTheme();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };

  const navItems = [
    { path: '/home', icon: Home, label: 'Home' },
    { path: '/discover', icon: Compass, label: 'Blogs' },
    { path: '/spaces', icon: Box, label: 'Spaces' },
    { path: '/library', icon: BookOpen, label: 'Library' },
  ];

  return (
    <nav 
      className="md:hidden fixed bottom-0 left-0 right-0 bg-background border-t z-50"
      style={{
        backgroundColor: theme.colors.background,
        borderColor: isDarkMode ? '#2d2d3d' : '#e5e7eb'
      }}
    >
      <div className="flex justify-around items-center h-14">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center flex-1 h-full transition-colors duration-200 ${
                isActive 
                  ? isDarkMode 
                    ? 'text-white' 
                    : 'text-primary'
                  : isDarkMode 
                    ? 'text-gray-400 hover:text-white' 
                    : 'text-gray-500 hover:text-primary'
              }`}
            >
              <Icon size={20} />
              <span className="text-xs mt-0.5">{item.label}</span>
            </Link>
          );
        })}
        
        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className={`flex flex-col items-center justify-center flex-1 h-full transition-colors duration-200 ${
            isDarkMode 
              ? 'text-red-400 hover:text-red-300' 
              : 'text-red-500 hover:text-red-600'
          }`}
        >
          <LogOut size={20} />
          <span className="text-xs mt-0.5">Logout</span>
        </button>
      </div>
    </nav>
  );
};

export default MobileFooter; 