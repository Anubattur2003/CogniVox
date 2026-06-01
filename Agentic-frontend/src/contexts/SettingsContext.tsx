import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface SettingsContextType {
  showExecutionTime: boolean;
  selectedTheme: string;
  setShowExecutionTime: (show: boolean) => void;
  setSelectedTheme: (theme: string) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [showExecutionTime, setShowExecutionTimeState] = useState<boolean>(() => {
    const saved = localStorage.getItem('showExecutionTime');
    return saved ? JSON.parse(saved) : true;
  });
  
  const [selectedTheme, setSelectedThemeState] = useState<string>(() => {
    return localStorage.getItem('selectedTheme') || 'dark';
  });

  // Persist settings to localStorage
  useEffect(() => {
    localStorage.setItem('showExecutionTime', JSON.stringify(showExecutionTime));
  }, [showExecutionTime]);

  useEffect(() => {
    localStorage.setItem('selectedTheme', selectedTheme);
  }, [selectedTheme]);

  const setShowExecutionTime = (show: boolean) => {
    setShowExecutionTimeState(show);
  };

  const setSelectedTheme = (theme: string) => {
    setSelectedThemeState(theme);
  };

  return (
    <SettingsContext.Provider value={{
      showExecutionTime,
      selectedTheme,
      setShowExecutionTime,
      setSelectedTheme
    }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}; 