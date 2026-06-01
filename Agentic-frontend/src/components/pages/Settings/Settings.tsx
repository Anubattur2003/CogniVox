import React, { useState } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { useSidebar } from "../../../contexts/SidebarContext";
import { motion, AnimatePresence } from "framer-motion";
import { FiUser, FiLock, FiSettings, FiServer } from "react-icons/fi";

// Import tab components
import ProfileTab from "./tabs/ProfileTab";
import SecurityTab from "./tabs/SecurityTab";
import GeneralTab from "./tabs/GeneralTab";
import MCPServerTab from "./tabs/MCPServerTab";

// Tab configuration
interface TabConfig {
  id: "general" | "profile" | "security" | "mcp";
  label: string;
  icon: React.ComponentType<any>;
  description: string;
}

const Settings: React.FC = () => {
  const { isDarkMode } = useTheme();
  const { isOpen: isSidebarOpen } = useSidebar();

  // Active tab state - Default to 'general' first
  const [activeTab, setActiveTab] = useState<
    "general" | "profile" | "security" | "mcp"
  >("general");

  const tabs: TabConfig[] = [
    {
      id: "general",
      label: "General",
      icon: FiSettings,
      description: "Application preferences and display options",
    },
    {
      id: "profile",
      label: "Profile",
      icon: FiUser,
      description: "Personal information and account details",
    },
    {
      id: "security",
      label: "Security",
      icon: FiLock,
      description: "Password and security settings",
    },
    {
      id: "mcp",
      label: "MCP Servers",
      icon: FiServer,
      description: "Model Context Protocol server configurations",
    },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case "general":
        return <GeneralTab />;
      case "profile":
        return <ProfileTab />;
      case "security":
        return <SecurityTab />;
      case "mcp":
        return <MCPServerTab />;
      default:
        return <GeneralTab />;
    }
  };

  return (
    <div
      className={`fixed inset-0 ${
        isDarkMode ? "bg-[#282a36]" : "bg-white"
      } overflow-hidden flex flex-col`}
    >
      {/* Header - Made more minimal */}
      <motion.div
        className={`border-b ${
          isDarkMode
            ? "border-gray-700/30 bg-[#282a36]"
            : "border-gray-200 bg-white"
        }`}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <motion.div
          className="px-4 py-4"
          animate={{
            marginLeft: isSidebarOpen ? "16rem" : "4rem",
          }}
          transition={{
            type: "spring",
            stiffness: 300,
            damping: 30,
          }}
          style={{
            marginLeft:
              typeof window !== "undefined" && window.innerWidth < 768
                ? "0rem"
                : undefined,
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className={`p-2 rounded-lg ${
                isDarkMode ? "bg-purple-600/20" : "bg-purple-100"
              }`}
            >
              <FiSettings
                className={`w-4 h-4 ${
                  isDarkMode ? "text-purple-400" : "text-purple-600"
                }`}
              />
            </div>
            <div>
              <h1
                className={`text-xl font-semibold ${
                  isDarkMode ? "text-gray-100" : "text-gray-900"
                }`}
              >
                Settings
              </h1>
              <p
                className={`text-sm ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                Manage your account and preferences
              </p>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <motion.div
          className="h-full flex"
          animate={{
            marginLeft: isSidebarOpen ? "16rem" : "4rem",
          }}
          transition={{
            type: "spring",
            stiffness: 300,
            damping: 30,
          }}
          style={{
            marginLeft:
              typeof window !== "undefined" && window.innerWidth < 768
                ? "0rem"
                : undefined,
          }}
        >
          {/* Settings Sidebar - Made more minimal */}
          <div
            className={`w-52 border-r ${
              isDarkMode
                ? "border-gray-700/30 bg-gray-800/10"
                : "border-gray-200 bg-gray-50/30"
            } flex-shrink-0`}
          >
            <div className="p-3">
              <nav className="space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;

                  return (
                    <motion.button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all ${
                        isActive
                          ? isDarkMode
                            ? "bg-purple-600/20 text-purple-300 border border-purple-500/30"
                            : "bg-purple-100 text-purple-700 border border-purple-200"
                          : isDarkMode
                          ? "text-gray-400 hover:text-gray-300 hover:bg-gray-700/30"
                          : "text-gray-600 hover:text-gray-900 hover:bg-white"
                      }`}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <Icon
                        className={`w-4 h-4 flex-shrink-0 ${
                          isActive
                            ? isDarkMode
                              ? "text-purple-400"
                              : "text-purple-600"
                            : ""
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <div
                          className={`text-sm font-medium ${
                            isActive
                              ? isDarkMode
                                ? "text-purple-300"
                                : "text-purple-700"
                              : isDarkMode
                              ? "text-gray-300"
                              : "text-gray-900"
                          }`}
                        >
                          {tab.label}
                        </div>
                        <div
                          className={`text-xs mt-0.5 line-clamp-2 ${
                            isActive
                              ? isDarkMode
                                ? "text-purple-400/70"
                                : "text-purple-600/70"
                              : isDarkMode
                              ? "text-gray-500"
                              : "text-gray-500"
                          }`}
                        >
                          {tab.description}
                        </div>
                      </div>
                    </motion.button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Content Area - Made more minimal */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 max-w-4xl">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {renderTabContent()}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Settings;
