import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiTrash2, FiX, FiAlertTriangle } from 'react-icons/fi';
import { useTheme } from '../../contexts/ThemeContext';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  isDeleting?: boolean;
  description?: string;
}

const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  isDeleting = false,
  description = "This action cannot be undone."
}) => {
  const { isDarkMode } = useTheme();

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isOpen) return;
      
      if (event.key === 'Escape' && !isDeleting) {
        onClose();
      } else if (event.key === 'Enter' && !isDeleting) {
        onConfirm();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent background scrolling
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, isDeleting, onClose, onConfirm]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4"
          >
            {/* Modal */}
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              transition={{ type: "spring", duration: 0.3 }}
              onClick={(e) => e.stopPropagation()}
              className={`relative w-full max-w-sm mx-auto rounded-xl shadow-2xl overflow-hidden backdrop-blur-md ${
                isDarkMode 
                  ? 'bg-gray-900/95 border border-gray-700/50' 
                  : 'bg-white/95 border border-gray-200/50'
              }`}
            >
              {/* Close button */}
              <button
                onClick={onClose}
                disabled={isDeleting}
                className={`absolute top-3 right-3 p-1.5 rounded-full transition-colors z-10 ${
                  isDarkMode 
                    ? 'hover:bg-gray-700/60 text-gray-400 hover:text-white' 
                    : 'hover:bg-gray-100 text-gray-400 hover:text-gray-600'
                } ${isDeleting ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <FiX className="w-4 h-4" />
              </button>

              {/* Compact Header with Icon */}
              <div className="p-4 text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.1, type: "spring" }}
                  className={`w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center ${
                    isDarkMode ? 'bg-red-500/20' : 'bg-red-50'
                  }`}
                >
                  <motion.div
                    animate={{ 
                      scale: [1, 1.1, 1],
                    }}
                    transition={{ 
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  >
                    <FiAlertTriangle className="w-6 h-6 text-red-500" />
                  </motion.div>
                </motion.div>
                
                <h3 className={`text-base font-semibold mb-2 ${
                  isDarkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  Delete Chat?
                </h3>
                
                {/* Chat title preview */}
                <div className={`px-3 py-2 rounded-lg mb-3 ${
                  isDarkMode ? 'bg-gray-800/60' : 'bg-gray-50/80'
                }`}>
                  <p className={`text-sm truncate ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    "{title}"
                  </p>
                </div>
                
                <p className={`text-xs ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  This action cannot be undone
                </p>
              </div>

              {/* Compact Actions */}
              <div className="p-4 pt-0 flex space-x-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onClose}
                  disabled={isDeleting}
                  className={`flex-1 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                    isDarkMode
                      ? 'bg-gray-700/60 hover:bg-gray-700 text-gray-300 hover:text-white'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                  } ${isDeleting ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  Cancel
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onConfirm}
                  disabled={isDeleting}
                  className={`flex-1 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 flex items-center justify-center space-x-2 ${
                    isDeleting
                      ? 'bg-red-400 cursor-not-allowed'
                      : 'bg-red-500 hover:bg-red-600 active:bg-red-700'
                  } text-white shadow-lg hover:shadow-xl`}
                >
                  {isDeleting ? (
                    <>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
                      />
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <>
                      <FiTrash2 className="w-4 h-4" />
                      <span>Delete</span>
                    </>
                  )}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default DeleteConfirmModal; 