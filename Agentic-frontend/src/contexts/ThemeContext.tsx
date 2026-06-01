import React, { createContext, useContext, useState, useEffect } from "react";
import { draculaTheme, lightTheme } from "../themes/theme";

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  theme: typeof draculaTheme | typeof lightTheme;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  // Initialize from localStorage or default to dark
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('selectedTheme');
    if (savedTheme === 'light') return false;
    if (savedTheme === 'dark') return true;
    return true; // default to dark
  });

  const theme = isDarkMode ? draculaTheme : lightTheme;

  // Listen for changes to selectedTheme in localStorage
  useEffect(() => {
    const handleStorageChange = () => {
      const savedTheme = localStorage.getItem('selectedTheme');
      if (savedTheme === 'light') {
        setIsDarkMode(false);
      } else if (savedTheme === 'dark') {
        setIsDarkMode(true);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    // Also check periodically for changes (for same-tab updates)
    const interval = setInterval(() => {
      const savedTheme = localStorage.getItem('selectedTheme');
      const currentShouldBeDark = savedTheme === 'dark' || savedTheme === 'system';
      if (isDarkMode !== currentShouldBeDark && savedTheme !== 'system') {
        setIsDarkMode(savedTheme === 'dark');
      }
    }, 100);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, [isDarkMode]);

  const toggleTheme = () => {
    const newTheme = isDarkMode ? 'light' : 'dark';
    setIsDarkMode(!isDarkMode);
    localStorage.setItem('selectedTheme', newTheme);
  };

  const setTheme = (themeType: 'light' | 'dark') => {
    setIsDarkMode(themeType === 'dark');
    localStorage.setItem('selectedTheme', themeType);
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme, setTheme, theme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
