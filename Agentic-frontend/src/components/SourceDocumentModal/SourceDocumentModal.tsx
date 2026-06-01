import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { FiX, FiDownload, FiExternalLink } from 'react-icons/fi';

interface SourceDocument {
  document_title: string;
  content: string;
  relevance: number;
  file_path: string;
  download_url: string;
  page: number;
}

interface SourceDocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: SourceDocument | null;
}

const SourceDocumentModal: React.FC<SourceDocumentModalProps> = ({
  isOpen,
  onClose,
  document
}) => {
  const { isDarkMode } = useTheme();

  if (!document) return null;

  const handleDownload = () => {
    if (document.download_url) {
      window.open(document.download_url, '_blank');
    }
  };

  const getRelevanceColor = (relevance: number) => {
    if (relevance >= 0.8) return 'bg-green-500';
    if (relevance >= 0.6) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className={`relative w-full max-w-2xl max-h-[80vh] overflow-hidden rounded-2xl shadow-xl ${
              isDarkMode ? 'bg-[#1e1f29] border border-gray-700/50' : 'bg-white border border-gray-200/50'
            }`}
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          >
            {/* Header */}
            <div className={`flex items-center justify-between px-5 py-4 border-b ${
              isDarkMode ? 'border-gray-700/50' : 'border-gray-200/50'
            }`}>
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <div className={`w-2 h-2 rounded-full ${getRelevanceColor(document.relevance)}`} />
                <div className="min-w-0 flex-1">
                  <h3 className={`text-sm font-medium truncate ${
                    isDarkMode ? 'text-gray-100' : 'text-gray-900'
                  }`}>
                    {document.document_title}
                  </h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`text-xs ${
                      isDarkMode ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      Page {document.page}
                    </span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {(document.relevance * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1 ml-2">
                {document.download_url && (
                  <motion.button
                    onClick={handleDownload}
                    className={`p-1.5 rounded-lg transition-colors ${
                      isDarkMode 
                        ? 'hover:bg-gray-700 text-gray-400 hover:text-white' 
                        : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                    }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <FiDownload className="w-4 h-4" />
                  </motion.button>
                )}
                
                <button
                  onClick={onClose}
                  className={`p-1.5 rounded-lg transition-colors ${
                    isDarkMode 
                      ? 'hover:bg-gray-700 text-gray-400 hover:text-white' 
                      : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <FiX className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="px-5 py-4 max-h-[calc(80vh-120px)] overflow-y-auto">
              {/* File Path */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <FiExternalLink className={`w-3 h-3 ${
                    isDarkMode ? 'text-gray-400' : 'text-gray-500'
                  }`} />
                  <span className={`text-xs font-medium ${
                    isDarkMode ? 'text-gray-300' : 'text-gray-700'
                  }`}>
                    File Path
                  </span>
                </div>
                <p className={`text-xs font-mono px-2 py-1 rounded ${
                  isDarkMode 
                    ? 'bg-gray-800 text-gray-400 border border-gray-700' 
                    : 'bg-gray-50 text-gray-600 border border-gray-200'
                } break-all`}>
                  {document.file_path}
                </p>
              </div>

              {/* Document Content */}
              <div>
                <h4 className={`text-xs font-medium mb-2 ${
                  isDarkMode ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Content
                </h4>
                <div className={`p-3 rounded-lg text-sm leading-relaxed ${
                  isDarkMode 
                    ? 'bg-gray-800/50 text-gray-200 border border-gray-700/30' 
                    : 'bg-gray-50 text-gray-800 border border-gray-200/50'
                }`}>
                  <p className="whitespace-pre-wrap">
                    {document.content}
                  </p>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className={`px-5 py-3 border-t ${
              isDarkMode ? 'border-gray-700/50' : 'border-gray-200/50'
            }`}>
              <p className={`text-xs text-center ${
                isDarkMode ? 'text-gray-500' : 'text-gray-400'
              }`}>
                Press ESC or click outside to close
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default SourceDocumentModal; 