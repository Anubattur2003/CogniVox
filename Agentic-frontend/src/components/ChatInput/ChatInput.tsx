import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FiSend, FiLoader, FiFileText } from "react-icons/fi";
import { toast } from "react-hot-toast";
import { useTheme } from "../../contexts/ThemeContext";
import FileUploadModal from "../FileUploadModal/FileUploadModal";
import SpeechToText from "../SpeechToText/SpeechToText";

export interface ResponseMode {
  id: string;
  label: string;
  description: string;
  icon?: React.ReactNode;
  color?: string;
  comingSoon?: boolean;
}

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (message: string, mode: string) => void;
  placeholder?: string;
  disabled?: boolean;
  isGenerating?: boolean;
  variant?: "default" | "modal" | "compact";
  showModeSelector?: boolean;
  mode?: string; // External control of response mode
  className?: string;
}

const responseModes: ResponseMode[] = [
  {
    id: "agentic",
    label: "CogniVox Plus",
    description: "Our smartest model & more"
  },
  {
    id: "general",
    label: "CogniVox Standard",
    description: "Great for everyday tasks"
  }
];

const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSubmit,
  placeholder = "Type your message...",
  disabled = false,
  isGenerating = false,
  variant = "default",
  showModeSelector = true,
  mode, // External control of response mode
  className = ""
}) => {
  const { isDarkMode } = useTheme();
  const [selectedMode, setSelectedMode] = useState<string>(mode || "agentic");
  

  const [showModeDropdown, setShowModeDropdown] = useState(false);
  const [isFileModalOpen, setIsFileModalOpen] = useState(false);
  const [uploadedFilesCount, setUploadedFilesCount] = useState(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Use external mode if provided, otherwise use internal selectedMode
  const effectiveMode = mode || selectedMode;
  const currentMode = responseModes.find(m => m.id === effectiveMode) || responseModes[0];
  
  // Update internal state when external mode changes
  useEffect(() => {
    if (mode && mode !== selectedMode) {
      setSelectedMode(mode);
    }
  }, [mode]);



    // Auto-resize textarea
  const adjustTextareaHeight = () => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      const scrollHeight = inputRef.current.scrollHeight;
      const minHeight = variant === "compact" ? 24 : 44; 
      const maxHeight = variant === "modal" ? 120 : variant === "compact" ? 80 : 100;
      
      const newHeight = Math.max(minHeight, Math.min(scrollHeight, maxHeight));
      inputRef.current.style.height = `${newHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [value]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowModeDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleUploadSuccess = (response: any) => {
    if (response && response.metadata) {
      setUploadedFilesCount(response.metadata.file_count);
      toast.success(`${response.metadata.file_count} PDF file${response.metadata.file_count > 1 ? 's' : ''} uploaded to knowledge base!`, {
        style: {
          borderRadius: "10px",
          background: "#10b981",
          color: "#fff",
        },
        duration: 3000,
      });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim() || disabled || isGenerating) return;
    
    onSubmit(value.trim(), effectiveMode);
    setUploadedFilesCount(0);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  return (
    <div className={`w-full ${variant === "modal" ? "p-2" : variant === "compact" ? "px-4 py-3" : "px-4 py-4"} ${className}`}>
      {/* Upload Status Display */}
      <AnimatePresence>
        {uploadedFilesCount > 0 && (
          <motion.div
            className="mb-3"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
              isDarkMode ? 'bg-green-900/20 border-green-700/30 text-green-400' : 'bg-green-50 border-green-200 text-green-700'
            }`}>
              <FiFileText className="w-4 h-4 text-green-500" />
              <span className="text-sm">
                {uploadedFilesCount} PDF file{uploadedFilesCount > 1 ? 's' : ''} uploaded to knowledge base
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area with Integrated Mode Selector */}
      <div className="relative" ref={dropdownRef}>
        <form onSubmit={handleSubmit}>
          <div className={`flex flex-col gap-2 p-2.5 rounded-2xl border transition-all duration-200 ${
            isDarkMode 
              ? 'bg-[#44475a]/50 border-gray-700/30 focus-within:border-purple-500/40 focus-within:bg-[#44475a]/70' 
              : 'bg-gray-50 border-gray-200 focus-within:border-purple-400/40 focus-within:bg-gray-100'
          } ${value.trim() ? (isDarkMode ? 'border-purple-500/40 bg-[#44475a]/70' : 'border-purple-400/40 bg-gray-100') : ''} ${
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          }`}>
            
            {/* Textarea */}
            <textarea
              ref={inputRef}
              value={value}
              onChange={handleInputChange}
              placeholder={placeholder}
              disabled={disabled || isGenerating}
              className={`w-full bg-transparent border-none outline-none resize-none text-sm px-2 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent hover:scrollbar-thumb-gray-500 ${
                isDarkMode ? 'text-gray-100 placeholder-gray-500 scrollbar-thumb-gray-600 hover:scrollbar-thumb-gray-500' : 'text-gray-900 placeholder-gray-500'
              }`}
              style={{ 
                minHeight: variant === "compact" ? '24px' : '44px',
                height: 'auto',
                lineHeight: '1.4',
                paddingTop: '6px',
                paddingBottom: '6px',
                overflow: 'auto',
                wordWrap: 'break-word'
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            
            {/* Footer containing plus upload, model select, audio, and send */}
            <div className="flex items-center justify-between border-t border-gray-700/10 dark:border-gray-700/30 pt-2 px-1">
              <div className="flex items-center gap-1.5">
                {/* Plus (+) Button for files */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setIsFileModalOpen(true)}
                  disabled={disabled}
                  className={`flex items-center justify-center w-8 h-8 rounded-full transition-colors ${
                    isDarkMode
                      ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title="Upload PDF files"
                >
                  <span className="text-xl font-light leading-none">+</span>
                </motion.button>

                {/* Model Selector Pill */}
                {showModeSelector && (
                  <div className="relative">
                    <motion.button
                      type="button"
                      onClick={() => setShowModeDropdown(!showModeDropdown)}
                      className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                        isDarkMode
                          ? selectedMode === 'agentic'
                            ? 'text-purple-400 bg-purple-900/20 border border-purple-800/30 hover:bg-purple-900/30'
                            : 'text-blue-400 bg-blue-900/20 border border-blue-800/30 hover:bg-blue-900/30'
                          : selectedMode === 'agentic'
                            ? 'text-purple-600 bg-purple-50 border border-purple-200 hover:bg-purple-100'
                            : 'text-blue-600 bg-blue-50 border border-blue-200 hover:bg-blue-100'
                      }`}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      title={`Active model: ${currentMode.label}`}
                    >
                      {selectedMode === 'agentic' ? (
                        <svg className="w-3.5 h-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m11.314 11.314l.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
                        </svg>
                      )}
                      <span>{currentMode.label}</span>
                      <svg className={`w-2.5 h-2.5 text-gray-500 transition-transform ${showModeDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 15l7-7 7 7" />
                      </svg>
                    </motion.button>
                  </div>
                )}
              </div>

              {/* Right action group */}
              <div className="flex items-center gap-1.5">
                {/* Speech-to-Text Component */}
                <SpeechToText
                  onTranscribed={(transcribedText) => {
                    const newValue = value ? `${value} ${transcribedText}` : transcribedText;
                    onChange(newValue);
                  }}
                  disabled={disabled}
                  variant={variant}
                  isDarkMode={isDarkMode}
                />

                {/* Submit button */}
                <motion.button
                  whileHover={{ scale: value.trim() && !disabled && !isGenerating ? 1.05 : 1 }}
                  whileTap={{ scale: value.trim() && !disabled && !isGenerating ? 0.95 : 1 }}
                  type="submit"
                  disabled={!value.trim() || disabled || isGenerating}
                  className={`flex items-center justify-center w-8 h-8 rounded-full transition-all duration-200 ${
                    value.trim() && !disabled && !isGenerating
                      ? 'bg-purple-600 hover:bg-purple-700 text-white shadow-sm'
                      : isDarkMode
                        ? 'text-gray-600 bg-gray-800/30'
                        : 'text-gray-400 bg-gray-100'
                  }`}
                >
                  {isGenerating ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    >
                      <FiLoader className="w-3.5 h-3.5" />
                    </motion.div>
                  ) : (
                    <FiSend className="w-3.5 h-3.5" />
                  )}
                </motion.button>
              </div>
            </div>
          </div>
        </form>

        {/* Dropup Selector Menu */}
        {showModeSelector && (
          <AnimatePresence>
            {showModeDropdown && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className={`absolute bottom-full left-0 w-[calc(100vw-2rem)] sm:w-80 mb-2 border rounded-2xl shadow-xl backdrop-blur-sm z-50 p-2 ${
                  isDarkMode 
                    ? 'bg-[#1e1f29]/95 border-gray-700/50 text-gray-100' 
                    : 'bg-white/95 border-gray-200 text-gray-900'
                }`}
              >
                <div className="space-y-1">
                  {responseModes.map((mode) => (
                    <motion.button
                      key={mode.id}
                      type="button"
                      onClick={() => {
                        setSelectedMode(mode.id);
                        setShowModeDropdown(false);
                      }}
                      className={`w-full flex items-center justify-between p-2.5 rounded-xl text-left transition-all duration-200 ${
                        selectedMode === mode.id
                          ? isDarkMode
                            ? 'bg-gray-800/80'
                            : 'bg-gray-100'
                          : isDarkMode
                            ? 'hover:bg-gray-800/40 text-gray-300'
                            : 'hover:bg-gray-50 text-gray-700'
                      }`}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`mt-0.5 ${
                          mode.id === 'agentic' ? 'text-purple-500' : 'text-blue-500'
                        }`}>
                          {mode.id === 'agentic' ? (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m11.314 11.314l.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
                            </svg>
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-sm">{mode.label}</div>
                          <div className={`text-xs mt-0.5 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                            {mode.description}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {selectedMode === mode.id ? (
                          <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : mode.id === 'agentic' ? (
                          <span 
                            onClick={(e) => {
                              e.stopPropagation();
                              toast.success("Upgrade flow triggered!");
                            }}
                            className={`text-[10px] font-semibold px-2 py-1 rounded-full border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-850 transition-all ${
                              isDarkMode ? 'text-gray-200' : 'text-gray-700'
                            }`}
                          >
                            Upgrade
                          </span>
                        ) : null}
                      </div>
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>

      {/* File Upload Modal */}
      <FileUploadModal
        isOpen={isFileModalOpen}
        onClose={() => setIsFileModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
        maxFiles={5}
      />
    </div>
  );
};

export default ChatInput;