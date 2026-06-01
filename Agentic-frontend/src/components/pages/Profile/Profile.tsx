import React, { useState } from "react";
import { motion } from "framer-motion";
import { useTheme } from "../../../contexts/ThemeContext";
import { useSidebar } from "../../../contexts/SidebarContext";
import { useAuth } from "../../../contexts/AuthContext";
import { FiUser, FiMail, FiCalendar, FiSettings, FiShield, FiBell, FiEye, FiEdit3 } from "react-icons/fi";

const Profile: React.FC = () => {
  const { isDarkMode } = useTheme();
  const { isOpen: sidebarOpen } = useSidebar();
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  const profileSections = [
    {
      id: "account",
      title: "Account Information",
      icon: FiUser,
      items: [
        { label: "Username", value: user?.username || "Not set", editable: true },
        { label: "Email", value: user?.email || "Not set", editable: true },
        { label: "Member since", value: "December 2024", editable: false },
        { label: "Last active", value: "Just now", editable: false }
      ]
    },
    {
      id: "preferences",
      title: "Preferences",
      icon: FiSettings,
      items: [
        { label: "Theme", value: isDarkMode ? "Dark" : "Light", editable: true },
        { label: "Language", value: "English", editable: true },
        { label: "Timezone", value: "UTC", editable: true }
      ]
    },
    {
      id: "privacy",
      title: "Privacy & Security",
      icon: FiShield,
      items: [
        { label: "Two-factor authentication", value: "Disabled", editable: true },
        { label: "Data sharing", value: "Limited", editable: true },
        { label: "Activity tracking", value: "Enabled", editable: true }
      ]
    },
    {
      id: "notifications",
      title: "Notifications",
      icon: FiBell,
      items: [
        { label: "Email notifications", value: "Enabled", editable: true },
        { label: "Push notifications", value: "Enabled", editable: true },
        { label: "Weekly summary", value: "Enabled", editable: true }
      ]
    }
  ];

  return (
    <motion.div 
      className={`fixed inset-0 ${isDarkMode ? 'bg-[#282a36]' : 'bg-white'} overflow-y-auto`}
      animate={{
        marginLeft: sidebarOpen ? "16rem" : "4rem",
      }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 30,
      }}
      style={{
        marginLeft: typeof window !== 'undefined' && window.innerWidth < 768 ? '0rem' : undefined
      }}
    >
      <div className="h-full flex flex-col">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className={`border-b ${isDarkMode ? 'border-gray-700/50' : 'border-gray-200'} px-4 py-4`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                isDarkMode ? 'bg-[#44475a]' : 'bg-gray-100'
              }`}>
                <FiUser className={`w-6 h-6 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              </div>
              <div>
                <h1 className={`text-xl font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                  Profile Settings
                </h1>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Manage your account and preferences
                </p>
              </div>
            </div>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsEditing(!isEditing)}
              className={`px-3 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                isEditing
                  ? isDarkMode 
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                  : isDarkMode 
                    ? 'bg-[#44475a] hover:bg-[#44475a]/80 text-gray-300'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              <FiEdit3 className="w-4 h-4" />
              <span className="hidden sm:inline">{isEditing ? 'Save' : 'Edit'}</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 max-w-6xl mx-auto">
            {profileSections.map((section, sectionIndex) => {
              const Icon = section.icon;
              return (
                <motion.div
                  key={section.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: sectionIndex * 0.1 }}
                  className={`rounded-lg border ${
                    isDarkMode 
                      ? 'bg-[#44475a] border-gray-700/50' 
                      : 'bg-white border-gray-200'
                  } hover:shadow-lg transition-shadow duration-300`}
                >
                  {/* Section Header */}
                  <div className="p-4 border-b border-gray-200/10">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center`}>
                        <Icon className="w-4 h-4 text-white" />
                      </div>
                      <h2 className={`text-base font-semibold ${
                        isDarkMode ? 'text-gray-100' : 'text-gray-900'
                      }`}>
                        {section.title}
                      </h2>
                    </div>
                  </div>

                  {/* Section Content */}
                  <div className="p-4">
                    <div className="space-y-3">
                      {section.items.map((item, itemIndex) => (
                        <div
                          key={itemIndex}
                          className="flex items-center justify-between py-2"
                        >
                          <div className="flex-1">
                            <span className={`text-sm font-medium ${
                              isDarkMode ? 'text-gray-300' : 'text-gray-700'
                            }`}>
                              {item.label}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {isEditing && item.editable ? (
                              <input
                                type="text"
                                defaultValue={item.value}
                                className={`px-2 py-1 text-sm rounded border ${
                                  isDarkMode 
                                    ? 'bg-[#282a36] text-gray-100 border-gray-600 focus:border-purple-500' 
                                    : 'bg-gray-50 text-gray-900 border-gray-300 focus:border-purple-500'
                                } focus:outline-none`}
                              />
                            ) : (
                              <span className={`text-sm ${
                                isDarkMode ? 'text-gray-400' : 'text-gray-600'
                              }`}>
                                {item.value}
                              </span>
                            )}
                            {item.editable && (
                              <FiEye className={`w-3 h-3 ${
                                isDarkMode ? 'text-gray-600' : 'text-gray-400'
                              }`} />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Usage Statistics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className={`mt-4 max-w-6xl mx-auto rounded-lg border ${
              isDarkMode 
                ? 'bg-[#44475a] border-gray-700/50' 
                : 'bg-white border-gray-200'
            } hover:shadow-lg transition-shadow duration-300`}
          >
            <div className="p-4 border-b border-gray-200/10">
              <h2 className={`text-base font-semibold ${
                isDarkMode ? 'text-gray-100' : 'text-gray-900'
              }`}>
                Usage Statistics
              </h2>
            </div>
            
            <div className="p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Total Chats", value: "42", trend: "+12%" },
                  { label: "Messages Sent", value: "1,284", trend: "+8%" },
                  { label: "Hours Active", value: "23.5", trend: "+15%" },
                  { label: "Favorite Topics", value: "AI, Tech", trend: "New" }
                ].map((stat, index) => (
                  <div key={index} className="text-center">
                    <div className={`text-lg font-semibold ${
                      isDarkMode ? 'text-gray-100' : 'text-gray-900'
                    }`}>
                      {stat.value}
                    </div>
                    <div className={`text-xs ${
                      isDarkMode ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      {stat.label}
                    </div>
                    <div className="text-xs text-green-500 mt-1">
                      {stat.trend}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

export default Profile;
