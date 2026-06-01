import React from "react";
import { FaBrain, FaBars, FaSignOutAlt } from "react-icons/fa";
import { Link, useLocation } from "react-router-dom";
import { Home, Compass, BookOpen, Plus, Box, Settings } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "../../contexts/ThemeContext";
import { useSidebar } from "../../contexts/SidebarContext";
import { useAuth } from "../../contexts/AuthContext";
import AnimatedAvatar from "../AnimatedAvatar/AnimatedAvatar";
import ThemeToggle from "../../themes/ThemeToggle";

interface SidebarProps {
  setIsQuickInputOpen: (open: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ setIsQuickInputOpen }) => {
  const { theme, isDarkMode, toggleTheme } = useTheme();
  const { isOpen, toggleSidebar } = useSidebar();
  const { logout, user } = useAuth();
  const location = useLocation();

  const handleLogout = () => {
    logout();
  };

  const handleQuickInputOpen = () => {
    setIsQuickInputOpen(true);
  };

  const navigationItems = [
    { path: "/home", icon: Home, label: "Home" },
    { path: "/discover", icon: Compass, label: "Discover" },
    { path: "/library", icon: BookOpen, label: "Library" },
    { path: "/spaces", icon: Box, label: "Spaces" },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      <motion.aside
        className={`hidden md:flex ${
          isOpen ? "w-56" : "w-14"
        } h-screen flex-col sticky top-0 z-40 ${
          isDarkMode 
            ? 'bg-gray-950/95 border-r border-gray-800/30' 
            : 'bg-gray-50/80 border-r border-gray-200/50 shadow-lg'
        } backdrop-blur-md`}
        animate={{ width: isOpen ? 224 : 56 }}
        transition={{ 
          type: "spring", 
          stiffness: 300, 
          damping: 30,
          duration: 0.3 
        }}
      >
        {/* Header */}
        <div className={`flex items-center ${isOpen ? 'px-3 py-4' : 'justify-center py-4'} ${
          isDarkMode ? '' : 'border-b border-gray-200/40'
        }`}>
          <div className="w-7 h-7 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm">
            <FaBrain className="w-3.5 h-3.5 text-white" />
          </div>
          <AnimatePresence>
            {isOpen && (
              <motion.span 
                className="text-lg font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent ml-3"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
              >
                CogniVox
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Toggle Button */}
        <div className="px-3 mb-4">
          <motion.button
            onClick={toggleSidebar}
            className={`w-full p-2.5 rounded-xl transition-all duration-200 ${
              isDarkMode 
                ? 'hover:bg-gray-800/60 text-gray-400 hover:text-gray-300' 
                : 'hover:bg-white/70 text-gray-500 hover:text-gray-700 shadow-sm hover:shadow-md'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <FaBars className="w-3.5 h-3.5 mx-auto" />
          </motion.button>
        </div>

        {/* New Chat Button */}
        <div className="px-3 mb-6">
          <motion.button 
            className={`w-full flex items-center ${
              isOpen ? 'justify-start px-4 py-3' : 'justify-center p-2.5'
            } rounded-xl transition-all duration-200 ${
              isDarkMode 
                ? 'bg-purple-600/10 hover:bg-purple-600/20 border border-purple-500/20 hover:border-purple-500/30' 
                : 'bg-gradient-to-r from-purple-50 to-blue-50 hover:from-purple-100 hover:to-blue-100 border border-purple-200/60 hover:border-purple-300/60 shadow-sm hover:shadow-md'
            }`}
            onClick={handleQuickInputOpen}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Plus className="h-4 w-4 text-purple-600 flex-shrink-0" />
            <AnimatePresence>
              {isOpen && (
                <motion.span 
                  className={`ml-3 text-sm font-semibold ${
                    isDarkMode ? 'text-purple-300' : 'text-purple-700'
                  }`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  New Chat
                </motion.span>
              )}
            </AnimatePresence>
          </motion.button>
        </div>

        {/* Navigation Links */}
        <nav className="flex flex-col px-3 flex-1 space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            
            return (
              <motion.div key={item.path} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Link
                  to={item.path}
                  className={`group relative flex items-center ${
                    isOpen ? 'justify-start px-4 py-3' : 'justify-center p-2.5'
                  } rounded-xl transition-all duration-200 ${
                    active
                      ? isDarkMode 
                        ? 'bg-purple-600/20 text-purple-300 shadow-lg shadow-purple-600/10' 
                        : 'bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 shadow-md shadow-purple-200/40 border border-purple-200/50'
                      : isDarkMode 
                        ? 'hover:bg-gray-800/60 text-gray-400 hover:text-gray-300' 
                        : 'hover:bg-white/70 text-gray-600 hover:text-gray-800 hover:shadow-sm'
                  }`}
                >
                  <Icon size={16} className="flex-shrink-0" />
                  <AnimatePresence>
                    {isOpen && (
                      <motion.span 
                        className="ml-3 text-sm font-medium"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2 }}
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                  
                  {/* Active indicator */}
                  {active && (
                    <motion.div
                      className={`absolute left-0 top-1/2 w-1 h-6 rounded-r-full ${
                        isDarkMode ? 'bg-purple-400' : 'bg-purple-500'
                      }`}
                      layoutId="activeIndicator"
                      initial={{ opacity: 0, scaleY: 0.5 }}
                      animate={{ opacity: 1, scaleY: 1 }}
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                </Link>
              </motion.div>
            );
          })}
        </nav>

        {/* Settings Section */}
        <div className={`px-3 pb-3 border-t ${
          isDarkMode ? 'border-gray-800/30' : 'border-gray-200/50'
        }`}>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Link
              to="/settings"
              className={`group relative flex items-center ${
                isOpen ? 'justify-start px-4 py-3' : 'justify-center p-2.5'
              } rounded-xl transition-all duration-200 mt-3 ${
                isActive("/settings")
                  ? isDarkMode 
                    ? 'bg-purple-600/20 text-purple-300 shadow-lg shadow-purple-600/10' 
                    : 'bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 shadow-md shadow-purple-200/40 border border-purple-200/50'
                  : isDarkMode 
                    ? 'hover:bg-gray-800/60 text-gray-400 hover:text-gray-300' 
                    : 'hover:bg-white/70 text-gray-600 hover:text-gray-800 hover:shadow-sm'
              }`}
            >
              <Settings size={16} className="flex-shrink-0" />
              <AnimatePresence>
                {isOpen && (
                  <motion.span 
                    className="ml-3 text-sm font-medium"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    Settings
                  </motion.span>
                )}
              </AnimatePresence>
              
              {/* Active indicator */}
              {isActive("/settings") && (
                <motion.div
                  className={`absolute left-0 top-1/2 w-1 h-6 rounded-r-full ${
                    isDarkMode ? 'bg-purple-400' : 'bg-purple-500'
                  }`}
                  layoutId="activeIndicator"
                  initial={{ opacity: 0, scaleY: 0.5 }}
                  animate={{ opacity: 1, scaleY: 1 }}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
            </Link>
          </motion.div>
        </div>

        {/* Bottom Section */}
        <div className={`p-3 border-t ${
          isDarkMode ? 'border-gray-800/30' : 'border-gray-200/50'
        }`}>
          <AnimatePresence mode="wait">
            {!isOpen ? (
              <motion.div 
                key="collapsed"
                className="flex flex-col items-center space-y-3"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <div className={`p-1 rounded-lg ${
                  isDarkMode ? '' : 'bg-white/50 shadow-sm'
                }`}>
                  <ThemeToggle isDark={isDarkMode} onToggle={toggleTheme} />
                </div>
                
                <motion.div 
                  className={`relative p-1 rounded-lg ${
                    isDarkMode ? '' : 'bg-white/50 shadow-sm'
                  }`}
                  whileHover={{ scale: 1.05 }}
                >
                  <AnimatedAvatar 
                    name={user?.firstName || user?.username || 'User'} 
                    size="sm" 
                  />
                </motion.div>

                <motion.button
                  onClick={handleLogout}
                  className={`p-2 rounded-lg transition-all duration-200 ${
                    isDarkMode 
                      ? 'hover:bg-red-600/20 text-red-400 hover:text-red-300' 
                      : 'hover:bg-red-50 text-red-500 hover:text-red-600 bg-white/50 shadow-sm hover:shadow-md'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  title="Logout"
                >
                  <FaSignOutAlt className="w-3.5 h-3.5" />
                </motion.button>
              </motion.div>
            ) : (
              <motion.div 
                key="expanded"
                className="space-y-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2, delay: 0.1 }}
              >
                {/* User Info */}
                <div className={`flex items-center p-3 rounded-xl ${
                  isDarkMode 
                    ? 'bg-gray-800/30' 
                    : 'bg-white/60 shadow-sm border border-gray-200/30'
                }`}>
                  <AnimatedAvatar 
                    name={user?.firstName || user?.username || 'User'} 
                    size="sm" 
                  />
                  <div className="ml-3 flex-1 min-w-0">
                    <p className={`text-sm font-semibold truncate ${
                      isDarkMode ? 'text-gray-200' : 'text-gray-800'
                    }`}>
                      {user?.firstName ? `${user.firstName} ${user.lastName}` : user?.username || 'User'}
                    </p>
                    <p className={`text-xs truncate ${
                      isDarkMode ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      {user?.email ? user.email.length > 20 ? user.email.substring(0, 18) + '...' : user.email : 'user@example.com'}
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between px-1">
                  <div className={`p-1 rounded-lg ${
                    isDarkMode ? '' : 'bg-white/50 shadow-sm'
                  }`}>
                    <ThemeToggle isDark={isDarkMode} onToggle={toggleTheme} />
                  </div>

                  <motion.button
                    onClick={handleLogout}
                    className={`p-2.5 rounded-lg transition-all duration-200 ${
                      isDarkMode 
                        ? 'hover:bg-red-600/20 text-red-400 hover:text-red-300' 
                        : 'hover:bg-red-50 text-red-500 hover:text-red-600 bg-white/50 shadow-sm hover:shadow-md'
                    }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    title="Logout"
                  >
                    <FaSignOutAlt className="w-4 h-4" />
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.aside>

      {/* Mobile Navbar */}
      <nav 
        className={`md:hidden fixed top-0 left-0 right-0 z-50 ${
          isDarkMode 
            ? 'bg-gray-950/95 border-b border-gray-800/30' 
            : 'bg-gray-50/90 border-b border-gray-200/60 shadow-sm'
        } backdrop-blur-md`}
      >
        <div className="flex justify-between items-center px-4 py-3">
          <div className="flex items-center">
            <div className="w-7 h-7 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl flex items-center justify-center mr-3 shadow-sm">
              <FaBrain className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              CogniVox
            </span>
          </div>
          <div className={`p-1 rounded-lg ${
            isDarkMode ? '' : 'bg-white/50 shadow-sm'
          }`}>
            <ThemeToggle isDark={isDarkMode} onToggle={toggleTheme} />
          </div>
        </div>
      </nav>
    </>
  );
};

export default Sidebar;
