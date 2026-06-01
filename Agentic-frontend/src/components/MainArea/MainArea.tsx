import React from "react";
import { useTheme } from "../../contexts/ThemeContext";

const MainArea: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { theme } = useTheme();
  
  return (
    <main 
      className="flex-1 w-full flex flex-col overflow-y-auto"
      style={{ 
        background: theme.colors.background,
        height: 'calc(100vh - 48px - 56px)', // 48px for header, 56px for footer
      }}
    >
      <div className="w-full max-w-3xl mx-auto px-4 md:px-6 lg:px-8 py-4">
        {children}
      </div>
    </main>
  );
};

export default MainArea;
