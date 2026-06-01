import React, { useEffect, useRef, useState } from "react";
import { FaTimes } from "react-icons/fa";
import { FiTarget, FiZap, FiCpu, FiClock } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "react-hot-toast";
import { useTheme } from "../../contexts/ThemeContext";
import { useAuth } from "../../contexts/AuthContext";
import { useSpace } from "../../contexts/SpaceContext";
import { useNavigate } from "react-router-dom";
import { chatApi } from "../../services/api";
import ChatInput from "../ChatInput/ChatInput";

interface QuickInputProps {
  isOpen: boolean;
  onClose: () => void;
}

type ResponseMode = {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  placeholder: string;
  comingSoon?: boolean;
};

const QuickInput: React.FC<QuickInputProps> = ({ isOpen, onClose }) => {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { isDarkMode } = useTheme();
  const { user } = useAuth();
  const { selectedSpace, fetchSpaces } = useSpace();
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState("");
  const [selectedMode, setSelectedMode] = useState<string>("general");
  const [showModes, setShowModes] = useState(false);


  const responseModes: ResponseMode[] = [
    {
      id: "general",
      label: "General",
      icon: <FiTarget className="w-3 h-3" />,
      color: "purple",
      placeholder: "Ask me anything..."
    },
    {
      id: "thinking",
      label: "Thinking",
      icon: <FiCpu className="w-3 h-3" />,
      color: "blue",
      placeholder: "Thinking about..."
    },
    {
      id: "agentic",
      label: "Agentic",
      icon: <FiZap className="w-3 h-3" />,
      color: "green",
      placeholder: "Help me with..."
    },
    {
      id: "research",
      label: "Research",
      icon: <FiClock className="w-3 h-3" />,
      color: "orange",
      placeholder: "Researching...",
      comingSoon: true
    }
  ];

  const currentMode = responseModes.find(mode => mode.id === selectedMode) || responseModes[0];

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
        adjustTextareaHeight();
      }, 100);
    }
    if (isOpen) {
      setInputValue("");
      setSelectedMode("general");
      setShowModes(false);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  const adjustTextareaHeight = () => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      const scrollHeight = inputRef.current.scrollHeight;
      const minHeight = 28; // Minimum single line height
      const maxHeight = 100; // Dynamic maximum height for longer content
      const newHeight = Math.max(minHeight, Math.min(scrollHeight, maxHeight));
      inputRef.current.style.height = `${newHeight}px`;
    }
  };

  const handleSubmit = async (message: string, responseMode: string) => {
    if (!message.trim()) return;

    if (!user?.id) {
      toast.error('Please log in to create a new chat');
      onClose();
      return;
    }

    try {
      const threadTitle = message.substring(0, 50) + (message.length > 50 ? '...' : '');
      const response = await chatApi.createNewThread(threadTitle, user.id, selectedSpace?.id);
      
      if (response.data && (response.status === 200 || response.status === 201)) {
        const apiThread = response.data;
        
        // Create thread for local storage (backward compatibility)
        const threads = JSON.parse(localStorage.getItem('threads') || '[]');
        const newThread = {
          id: apiThread.chat_id,
          title: apiThread.title,
          content: message,
          timestamp: apiThread.created_at,
          action: "general", // No longer using quick actions
          responseMode: responseMode,
          messages: [{
            id: Date.now().toString(),
            content: message,
            timestamp: apiThread.created_at,
            isUser: true,
            action: "general", // No longer using quick actions
            responseMode: responseMode
          }]
        };
        
        threads.unshift(newThread);
        localStorage.setItem('threads', JSON.stringify(threads));

        console.log('New thread created via API from QuickInput:', apiThread, 'Mode:', responseMode);
        toast.success('New chat created!');

        // Refresh spaces to update thread counts (async, don't block navigation)
        fetchSpaces().catch(err => console.error('Failed to refresh spaces:', err));

        // Close modal first, then navigate
        onClose();
        setInputValue("");
        
        // Navigate to chat and submit the query immediately with response mode
        navigate(`/chat?chatId=${apiThread.chat_id}&prompt=${encodeURIComponent(message.trim())}&responseMode=${responseMode}`);
      } else {
        throw new Error(response.error || 'Failed to create thread');
      }
    } catch (error) {
      console.error('Failed to create thread via API from QuickInput:', error);
      toast.error('Failed to create new chat. Please try again.');
      // Close modal on error too
      onClose();
      setInputValue("");
      navigate('/chat');
    }
  };

  const getActionColor = (color: string) => {
    const colors = {
      purple: isDarkMode ? 'text-purple-400' : 'text-purple-600',
      blue: isDarkMode ? 'text-blue-400' : 'text-blue-600',
      yellow: isDarkMode ? 'text-yellow-400' : 'text-yellow-600',
      green: isDarkMode ? 'text-green-400' : 'text-green-600',
      orange: isDarkMode ? 'text-orange-400' : 'text-orange-600'
    };
    return colors[color as keyof typeof colors] || colors.purple;
  };

  if (!isOpen) return null;

  return (
    <>
      <motion.div 
        className={`fixed inset-0 ${
          isDarkMode ? 'bg-gray-950/60' : 'bg-white/60'
        } backdrop-blur-sm flex items-center justify-center z-50 p-4`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.15 }}
      >
        <motion.div 
          ref={containerRef}
          className={`${
            isDarkMode ? 'bg-gray-900/95 border border-gray-800/40' : 'bg-white/95 border border-gray-200/40'
          } backdrop-blur-sm rounded-lg shadow-xl w-full max-w-md relative overflow-hidden`}
          initial={{ scale: 0.95, y: 10 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.95, y: 10 }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
        >
          {/* Compact Header */}
          <div className={`flex items-center justify-between px-2 py-1.5 border-b ${
            isDarkMode ? 'border-gray-800/40' : 'border-gray-200/40'
          }`}>
            <div className="flex items-center space-x-1.5">
              <div className={`p-0.5 rounded ${getActionColor(currentMode.color)}`}>
                {currentMode.icon}
              </div>
              <span className={`text-xs font-medium ${
                isDarkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                {currentMode.label}
              </span>
            </div>
            
            <div className="flex items-center space-x-0.5">
              <motion.button
                onClick={() => setShowModes(!showModes)}
                className={`p-1 rounded transition-colors ${
                  isDarkMode 
                    ? 'hover:bg-gray-800/50 text-gray-400 hover:text-gray-300' 
                    : 'hover:bg-gray-100/50 text-gray-500 hover:text-gray-600'
                } ${getActionColor(currentMode.color)}`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title="Change response mode"
              >
                <FiZap className="w-3 h-3" />
              </motion.button>
              
              <motion.button
                onClick={onClose}
                className={`p-1 rounded transition-colors ${
                  isDarkMode 
                    ? 'hover:bg-gray-800/50 text-gray-400 hover:text-gray-300' 
                    : 'hover:bg-gray-100/50 text-gray-500 hover:text-gray-600'
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <FaTimes className="w-3 h-3" />
              </motion.button>
            </div>
          </div>

          {/* Response Mode Selector */}
          <AnimatePresence>
            {showModes && (
              <motion.div
                className={`px-2 py-1.5 border-b ${
                  isDarkMode ? 'border-gray-800/40' : 'border-gray-200/40'
                }`}
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.15 }}
              >
                <div className="grid grid-cols-2 gap-1">
                  {responseModes.map((mode) => (
                    <motion.button
                      key={mode.id}
                      onClick={() => {
                        if (!mode.comingSoon) {
                          setSelectedMode(mode.id);
                        }
                        setShowModes(false);
                      }}
                      disabled={mode.comingSoon}
                      className={`flex items-center px-1.5 py-1 rounded text-xs transition-all ${
                        selectedMode === mode.id
                          ? isDarkMode 
                            ? 'bg-gray-800/60 text-gray-200' 
                            : 'bg-gray-100 text-gray-900'
                          : isDarkMode 
                            ? 'hover:bg-gray-800/40 text-gray-400 hover:text-gray-300' 
                            : 'hover:bg-gray-100/60 text-gray-600 hover:text-gray-900'
                      } ${mode.comingSoon ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
                      whileHover={!mode.comingSoon ? { scale: 1.02 } : {}}
                      whileTap={!mode.comingSoon ? { scale: 0.98 } : {}}
                    >
                      <div className={`mr-1 ${getActionColor(mode.color)}`}>
                        {mode.icon}
                      </div>
                      <span className="flex-1 truncate">{mode.label}</span>
                      {mode.comingSoon && (
                        <span className={`text-xs px-1 py-0.5 rounded ml-1 ${
                          isDarkMode ? 'bg-yellow-600/20 text-yellow-400' : 'bg-yellow-100 text-yellow-600'
                        }`}>
                          Soon
                        </span>
                      )}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input Section */}
          <div className="p-2">
            <ChatInput
              value={inputValue}
              onChange={setInputValue}
              onSubmit={handleSubmit}
              placeholder={currentMode.placeholder}
              variant="modal"
              showModeSelector={false}
              mode={selectedMode}
              className="border-none p-0"
            />
          </div>
        </motion.div>
      </motion.div>


    </>
  );
};

export default QuickInput;
