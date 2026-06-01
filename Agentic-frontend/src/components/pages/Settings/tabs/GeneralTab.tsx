import React from "react";
import { motion } from "framer-motion";
import { toast } from "react-hot-toast";
import { FiClock, FiMonitor, FiInfo, FiSettings } from "react-icons/fi";
import { useTheme } from "../../../../contexts/ThemeContext";
import { useSettings } from "../../../../contexts/SettingsContext";

const GeneralTab: React.FC = () => {
  const { isDarkMode, setTheme } = useTheme();
  const { showExecutionTime, selectedTheme, setShowExecutionTime, setSelectedTheme } = useSettings();

  const themeOptions = [
    { id: 'system', name: 'System', description: 'Use system preference', disabled: true },
    { id: 'light', name: 'Light', description: 'Always light mode' },
    { id: 'dark', name: 'Dark', description: 'Always dark mode' },
  ];

  const handleExecutionTimeToggle = () => {
    const newValue = !showExecutionTime;
    setShowExecutionTime(newValue);
    toast.success(`Execution time ${newValue ? 'enabled' : 'disabled'}`, {
      duration: 2000,
    });
  };

  const handleThemeChange = (themeId: string) => {
    setSelectedTheme(themeId);
    
    if (themeId === 'light') {
      setTheme('light');
      toast.success('Theme changed to light');
    } else if (themeId === 'dark') {
      setTheme('dark');
      toast.success('Theme changed to dark');
    } else if (themeId === 'system') {
      toast('System theme (Coming Soon)', { icon: 'ℹ️' });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      transition={{ duration: 0.2 }}
      className="space-y-6"
    >
      {/* Preferences */}
      <div className={`p-4 rounded-lg border ${
        isDarkMode 
          ? 'bg-gray-800/30 border-gray-700/30' 
          : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-1.5 rounded-lg ${
            isDarkMode ? 'bg-purple-600/20' : 'bg-purple-100'
          }`}>
            <FiSettings className={`w-4 h-4 ${
              isDarkMode ? 'text-purple-400' : 'text-purple-600'
            }`} />
          </div>
          <div>
            <h2 className={`text-lg font-semibold ${
              isDarkMode ? 'text-gray-100' : 'text-gray-900'
            }`}>
              Preferences
            </h2>
            <p className={`text-sm ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Customize your experience
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {/* Execution Time Toggle */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FiClock className={`w-4 h-4 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-600'
              }`} />
              <div>
                <p className={`font-medium ${
                  isDarkMode ? 'text-gray-100' : 'text-gray-900'
                }`}>
                  Show Execution Time
                </p>
                <p className={`text-sm ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Display AI response processing time
                </p>
              </div>
            </div>
            
            <motion.button
              onClick={handleExecutionTimeToggle}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                showExecutionTime
                  ? 'bg-purple-600'
                  : isDarkMode
                    ? 'bg-gray-600'
                    : 'bg-gray-300'
              }`}
              whileTap={{ scale: 0.95 }}
            >
              <motion.span
                className="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                animate={{
                  x: showExecutionTime ? 24 : 4
                }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            </motion.button>
          </div>

          {/* Theme Selection */}
          <div>
            <div className="flex items-center gap-3 mb-3">
              <FiMonitor className={`w-4 h-4 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-600'
              }`} />
              <div>
                <p className={`font-medium ${
                  isDarkMode ? 'text-gray-100' : 'text-gray-900'
                }`}>
                  Theme
                </p>
                <p className={`text-sm ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Choose your preferred appearance
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-2 ml-7">
              {themeOptions.map((theme) => (
                <motion.div
                  key={theme.id}
                  onClick={() => !theme.disabled && handleThemeChange(theme.id)}
                  className={`p-3 rounded-lg border transition-all ${
                    theme.disabled
                      ? isDarkMode
                        ? 'bg-gray-700/20 border-gray-700/20 cursor-not-allowed opacity-60'
                        : 'bg-gray-50/50 border-gray-200/50 cursor-not-allowed opacity-60'
                      : selectedTheme === theme.id
                        ? isDarkMode
                          ? 'bg-purple-600/20 border-purple-500/50 cursor-pointer'
                          : 'bg-purple-100 border-purple-300 cursor-pointer'
                        : isDarkMode
                          ? 'bg-gray-700/30 border-gray-600/30 hover:bg-gray-700/50 cursor-pointer'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100 cursor-pointer'
                  }`}
                  whileHover={theme.disabled ? {} : { scale: 1.01 }}
                  whileTap={theme.disabled ? {} : { scale: 0.99 }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h3 className={`font-medium text-sm ${
                        isDarkMode ? 'text-gray-100' : 'text-gray-900'
                      }`}>
                        {theme.name}
                      </h3>
                      {theme.disabled && (
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          isDarkMode 
                            ? 'bg-yellow-600/20 text-yellow-400' 
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          Coming Soon
                        </span>
                      )}
                    </div>
                    
                    <div className={`w-4 h-4 rounded-full border-2 transition-all ${
                      selectedTheme === theme.id
                        ? 'border-purple-500 bg-purple-500'
                        : isDarkMode
                          ? 'border-gray-500'
                          : 'border-gray-300'
                    }`}>
                      {selectedTheme === theme.id && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="w-full h-full rounded-full bg-white"
                          style={{ transform: 'scale(0.4)' }}
                        />
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Application Info */}
      <div className={`p-4 rounded-lg border ${
        isDarkMode 
          ? 'bg-gray-800/30 border-gray-700/30' 
          : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center gap-3 mb-3">
          <div className={`p-1.5 rounded-lg ${
            isDarkMode ? 'bg-blue-600/20' : 'bg-blue-100'
          }`}>
            <FiInfo className={`w-4 h-4 ${
              isDarkMode ? 'text-blue-400' : 'text-blue-600'
            }`} />
          </div>
          <div>
            <h2 className={`text-lg font-semibold ${
              isDarkMode ? 'text-gray-100' : 'text-gray-900'
            }`}>
              Application Info
            </h2>
          </div>
        </div>

        <div className={`space-y-2 text-sm ${
          isDarkMode ? 'text-gray-400' : 'text-gray-600'
        }`}>
          <div className="flex justify-between">
            <span>Version</span>
            <span className={isDarkMode ? 'text-gray-300' : 'text-gray-700'}>1.0.0</span>
          </div>
          <div className="flex justify-between">
            <span>Environment</span>
            <span className={isDarkMode ? 'text-gray-300' : 'text-gray-700'}>Development</span>
          </div>
          <div className="flex justify-between">
            <span>Last Updated</span>
            <span className={isDarkMode ? 'text-gray-300' : 'text-gray-700'}>
              {new Date().toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default GeneralTab; 