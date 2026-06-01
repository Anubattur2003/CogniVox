import React, { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "react-hot-toast";
import { FiLock, FiEye, FiEyeOff, FiShield, FiCheck, FiX } from "react-icons/fi";
import { useTheme } from "../../../../contexts/ThemeContext";

const SecurityTab: React.FC = () => {
  const { isDarkMode } = useTheme();
  
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });

  // Password strength calculation
  const calculatePasswordStrength = (password: string) => {
    let score = 0;
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      numbers: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };

    Object.values(checks).forEach(check => {
      if (check) score += 20;
    });

    return { score, checks };
  };

  const passwordStrength = calculatePasswordStrength(formData.newPassword);

  const getStrengthColor = (score: number) => {
    if (score < 40) return isDarkMode ? 'text-red-400' : 'text-red-600';
    if (score < 80) return isDarkMode ? 'text-yellow-400' : 'text-yellow-600';
    return isDarkMode ? 'text-green-400' : 'text-green-600';
  };

  const getStrengthText = (score: number) => {
    if (score < 40) return 'Weak';
    if (score < 80) return 'Medium';
    return 'Strong';
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const togglePasswordVisibility = (field: 'current' | 'new' | 'confirm') => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.currentPassword) {
      toast.error('Please enter your current password');
      return;
    }
    
    if (formData.newPassword !== formData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (passwordStrength.score < 60) {
      toast.error('Please choose a stronger password');
      return;
    }

    // TODO: Implement API call to change password
    toast.success('Password changed successfully!');
    setFormData({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      transition={{ duration: 0.2 }}
      className="space-y-4"
    >
      {/* Change Password */}
      <div className={`p-4 rounded-lg border ${
        isDarkMode 
          ? 'bg-gray-800/30 border-gray-700/30' 
          : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center gap-3 mb-4">
          <div className={`p-1.5 rounded-lg ${
            isDarkMode ? 'bg-red-600/20' : 'bg-red-100'
          }`}>
            <FiLock className={`w-4 h-4 ${
              isDarkMode ? 'text-red-400' : 'text-red-600'
            }`} />
          </div>
          <div>
            <h2 className={`text-lg font-semibold ${
              isDarkMode ? 'text-gray-100' : 'text-gray-900'
            }`}>
              Change Password
            </h2>
            <p className={`text-sm ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Update your password to keep your account secure
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Current Password */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Current Password
            </label>
            <div className="relative">
              <input
                type={showPasswords.current ? "text" : "password"}
                value={formData.currentPassword}
                onChange={(e) => handleInputChange('currentPassword', e.target.value)}
                className={`w-full px-3 py-2 pr-10 rounded-lg border text-sm transition-colors ${
                  isDarkMode
                    ? 'bg-gray-700/50 border-gray-600/50 text-gray-100 focus:border-red-500'
                    : 'bg-white border-gray-300 text-gray-900 focus:border-red-500'
                } focus:outline-none focus:ring-2 focus:ring-red-500/20`}
                placeholder="Enter your current password"
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('current')}
                className={`absolute right-3 top-1/2 transform -translate-y-1/2 ${
                  isDarkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {showPasswords.current ? <FiEyeOff className="w-4 h-4" /> : <FiEye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* New Password */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              New Password
            </label>
            <div className="relative">
              <input
                type={showPasswords.new ? "text" : "password"}
                value={formData.newPassword}
                onChange={(e) => handleInputChange('newPassword', e.target.value)}
                className={`w-full px-3 py-2 pr-10 rounded-lg border text-sm transition-colors ${
                  isDarkMode
                    ? 'bg-gray-700/50 border-gray-600/50 text-gray-100 focus:border-purple-500'
                    : 'bg-white border-gray-300 text-gray-900 focus:border-purple-500'
                } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
                placeholder="Enter your new password"
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('new')}
                className={`absolute right-3 top-1/2 transform -translate-y-1/2 ${
                  isDarkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {showPasswords.new ? <FiEyeOff className="w-4 h-4" /> : <FiEye className="w-4 h-4" />}
              </button>
            </div>

            {/* Password Strength Indicator */}
            {formData.newPassword && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-2"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-gray-500">Strength:</span>
                  <span className={`text-xs font-medium ${getStrengthColor(passwordStrength.score)}`}>
                    {getStrengthText(passwordStrength.score)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                  <motion.div
                    className={`h-1.5 rounded-full transition-all ${
                      passwordStrength.score < 40 ? 'bg-red-500' :
                      passwordStrength.score < 80 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${passwordStrength.score}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <div className="space-y-1">
                  {Object.entries(passwordStrength.checks).map(([key, passed]) => (
                    <div key={key} className="flex items-center gap-2">
                      {passed ? (
                        <FiCheck className="w-3 h-3 text-green-500" />
                      ) : (
                        <FiX className="w-3 h-3 text-red-500" />
                      )}
                      <span className={`text-xs ${
                        passed 
                          ? 'text-green-600 dark:text-green-400' 
                          : 'text-gray-500 dark:text-gray-400'
                      }`}>
                        {key === 'length' && 'At least 8 characters'}
                        {key === 'uppercase' && 'Contains uppercase letter'}
                        {key === 'lowercase' && 'Contains lowercase letter'}
                        {key === 'numbers' && 'Contains number'}
                        {key === 'special' && 'Contains special character'}
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Confirm New Password
            </label>
            <div className="relative">
              <input
                type={showPasswords.confirm ? "text" : "password"}
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                className={`w-full px-3 py-2 pr-10 rounded-lg border text-sm transition-colors ${
                  isDarkMode
                    ? 'bg-gray-700/50 border-gray-600/50 text-gray-100 focus:border-purple-500'
                    : 'bg-white border-gray-300 text-gray-900 focus:border-purple-500'
                } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
                placeholder="Confirm your new password"
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('confirm')}
                className={`absolute right-3 top-1/2 transform -translate-y-1/2 ${
                  isDarkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {showPasswords.confirm ? <FiEyeOff className="w-4 h-4" /> : <FiEye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <motion.button
            type="submit"
            className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-sm ${
              isDarkMode
                ? 'bg-purple-600 text-white hover:bg-purple-700'
                : 'bg-purple-600 text-white hover:bg-purple-700'
            } transition-colors`}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
          >
            <FiLock className="w-4 h-4" />
            Change Password
          </motion.button>
        </form>
      </div>

      {/* Security Tips */}
      <div className={`p-4 rounded-lg border ${
        isDarkMode 
          ? 'bg-gray-800/30 border-gray-700/30' 
          : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center gap-3 mb-3">
          <div className={`p-1.5 rounded-lg ${
            isDarkMode ? 'bg-blue-600/20' : 'bg-blue-100'
          }`}>
            <FiShield className={`w-4 h-4 ${
              isDarkMode ? 'text-blue-400' : 'text-blue-600'
            }`} />
          </div>
          <div>
            <h2 className={`text-lg font-semibold ${
              isDarkMode ? 'text-gray-100' : 'text-gray-900'
            }`}>
              Security Tips
            </h2>
          </div>
        </div>

        <div className="space-y-2">
          {[
            'Use a unique password for your CogniVox account',
            'Enable two-factor authentication when available',
            'Regularly update your password',
            'Never share your password with anyone',
            'Log out from shared or public devices'
          ].map((tip, index) => (
            <div key={index} className="flex items-start gap-2">
              <div className={`w-1.5 h-1.5 rounded-full mt-2 ${
                isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
              }`} />
              <span className={`text-sm ${
                isDarkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {tip}
              </span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default SecurityTab; 