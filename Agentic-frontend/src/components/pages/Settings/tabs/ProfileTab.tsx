import React, { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "react-hot-toast";
import { FiUser, FiMail, FiEdit3, FiSave, FiX, FiInfo } from "react-icons/fi";
import { useTheme } from "../../../../contexts/ThemeContext";
import { useAuth } from "../../../../contexts/AuthContext";

const ProfileTab: React.FC = () => {
  const { isDarkMode } = useTheme();
  const { user } = useAuth();
  
  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    firstName: user?.firstName || '',
    lastName: user?.lastName || '',
    username: user?.username || '',
    email: user?.email || ''
  });

  const handleEditToggle = () => {
    if (isEditing) {
      // Reset form data if canceling
      setFormData({
        firstName: user?.firstName || '',
        lastName: user?.lastName || '',
        username: user?.username || '',
        email: user?.email || ''
      });
    }
    setIsEditing(!isEditing);
  };

  const handleSave = () => {
    // TODO: Implement API call to update user profile
    toast.success('Profile updated successfully!');
    setIsEditing(false);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      transition={{ duration: 0.2 }}
      className="space-y-4"
    >
      {/* Profile Information */}
      <div className={`p-4 rounded-lg border ${
        isDarkMode 
          ? 'bg-gray-800/30 border-gray-700/30' 
          : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-1.5 rounded-lg ${
              isDarkMode ? 'bg-purple-600/20' : 'bg-purple-100'
            }`}>
              <FiUser className={`w-4 h-4 ${
                isDarkMode ? 'text-purple-400' : 'text-purple-600'
              }`} />
            </div>
            <div>
              <h2 className={`text-lg font-semibold ${
                isDarkMode ? 'text-gray-100' : 'text-gray-900'
              }`}>
                Profile Information
              </h2>
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-400' : 'text-gray-600'
              }`}>
                Manage your personal information and account details
              </p>
            </div>
          </div>
          
          <motion.button
            onClick={handleEditToggle}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              isEditing
                ? isDarkMode
                  ? 'bg-red-600/20 text-red-300 hover:bg-red-600/30'
                  : 'bg-red-100 text-red-700 hover:bg-red-200'
                : isDarkMode
                  ? 'bg-purple-600/20 text-purple-300 hover:bg-purple-600/30'
                  : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isEditing ? (
              <>
                <FiX className="w-4 h-4" />
                Cancel
              </>
            ) : (
              <>
                <FiEdit3 className="w-4 h-4" />
                Edit
              </>
            )}
          </motion.button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* First Name */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              First Name
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.firstName}
                onChange={(e) => handleInputChange('firstName', e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border text-sm transition-colors ${
                  isDarkMode
                    ? 'bg-gray-700/50 border-gray-600/50 text-gray-100 focus:border-purple-500'
                    : 'bg-white border-gray-300 text-gray-900 focus:border-purple-500'
                } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
              />
            ) : (
              <div className={`px-3 py-2 rounded-lg border text-sm ${
                isDarkMode
                  ? 'bg-gray-700/30 border-gray-600/30 text-gray-200'
                  : 'bg-gray-50 border-gray-200 text-gray-800'
              }`}>
                {formData.firstName || 'Not set'}
              </div>
            )}
          </div>

          {/* Last Name */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Last Name
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.lastName}
                onChange={(e) => handleInputChange('lastName', e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border text-sm transition-colors ${
                  isDarkMode
                    ? 'bg-gray-700/50 border-gray-600/50 text-gray-100 focus:border-purple-500'
                    : 'bg-white border-gray-300 text-gray-900 focus:border-purple-500'
                } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
              />
            ) : (
              <div className={`px-3 py-2 rounded-lg border text-sm ${
                isDarkMode
                  ? 'bg-gray-700/30 border-gray-600/30 text-gray-200'
                  : 'bg-gray-50 border-gray-200 text-gray-800'
              }`}>
                {formData.lastName || 'Not set'}
              </div>
            )}
          </div>

          {/* Username */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Username
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border text-sm transition-colors ${
                  isDarkMode
                    ? 'bg-gray-700/50 border-gray-600/50 text-gray-100 focus:border-purple-500'
                    : 'bg-white border-gray-300 text-gray-900 focus:border-purple-500'
                } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
              />
            ) : (
              <div className={`px-3 py-2 rounded-lg border text-sm ${
                isDarkMode
                  ? 'bg-gray-700/30 border-gray-600/30 text-gray-200'
                  : 'bg-gray-50 border-gray-200 text-gray-800'
              }`}>
                {formData.username || 'Not set'}
              </div>
            )}
          </div>

          {/* Email Address */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Email Address
            </label>
            <div className={`px-3 py-2 rounded-lg border text-sm ${
              isDarkMode
                ? 'bg-gray-700/30 border-gray-600/30 text-gray-200'
                : 'bg-gray-50 border-gray-200 text-gray-800'
            }`}>
              {formData.email || 'Not set'}
            </div>
          </div>
        </div>

        {/* Save Button */}
        {isEditing && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex justify-end"
          >
            <motion.button
              onClick={handleSave}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm ${
                isDarkMode
                  ? 'bg-purple-600 text-white hover:bg-purple-700'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              } transition-colors`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <FiSave className="w-4 h-4" />
              Save Changes
            </motion.button>
          </motion.div>
        )}
      </div>

      {/* Account Information */}
      <div className={`p-4 rounded-lg border ${
        isDarkMode 
          ? 'bg-gray-800/30 border-gray-700/30' 
          : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center gap-3 mb-4">
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
              Account Information
            </h2>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Account ID
            </label>
            <div className={`px-3 py-2 rounded-lg border text-sm font-mono ${
              isDarkMode
                ? 'bg-gray-700/30 border-gray-600/30 text-gray-300'
                : 'bg-gray-50 border-gray-200 text-gray-700'
            }`}>
              {user?.id || 'N/A'}
            </div>
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Account Role
            </label>
            <div className={`px-3 py-2 rounded-lg border text-sm ${
              isDarkMode
                ? 'bg-gray-700/30 border-gray-600/30 text-gray-300'
                : 'bg-gray-50 border-gray-200 text-gray-700'
            }`}>
              {user?.role || 'user'}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ProfileTab; 