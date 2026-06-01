import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar/Sidebar";
import MainArea from "./components/MainArea/MainArea";
import QuickInput from "./components/QuickInput/QuickInput";
import MobileFooter from "./components/MobileFooter/MobileFooter";
import { useTheme } from "./contexts/ThemeContext";
import { useSidebar } from "./contexts/SidebarContext";

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isQuickInputOpen, setIsQuickInputOpen] = useState(false);
  const { theme } = useTheme();
  const location = useLocation();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key.toLowerCase() === "m") {
        event.preventDefault();
        setIsQuickInputOpen(true);
      }
      if (event.type === 'click') {
        setIsQuickInputOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  // Close QuickInput modal when location changes
  useEffect(() => {
    setIsQuickInputOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex flex-col md:flex-row h-screen bg-background relative">
      <Sidebar
        setIsQuickInputOpen={setIsQuickInputOpen}
      />
      <div
        className="flex-1 flex flex-col overflow-hidden md:pb-0 pb-14 pt-12 md:pt-0 relative"
        style={{ background: theme.colors.background }}
      >
        <MainArea>{children}</MainArea>
      </div>
      <QuickInput
        isOpen={isQuickInputOpen}
        onClose={() => setIsQuickInputOpen(false)}
      />
      <MobileFooter />
    </div>
  );
};

export default Layout;
