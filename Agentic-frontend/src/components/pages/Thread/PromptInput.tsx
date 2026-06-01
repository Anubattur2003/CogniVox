import React, { useState, useRef, useEffect } from "react";
import { useSidebar } from "../../../contexts/SidebarContext";
import { useTheme } from "../../../contexts/ThemeContext";
import { useAuth } from "../../../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { FiCommand, FiSend, FiPaperclip, FiFileText } from "react-icons/fi";
import { motion } from "framer-motion";
import { toast } from "react-hot-toast";
import { chatApi } from "../../../services/api";
import FileUploadModal from "../../FileUploadModal/FileUploadModal";

const PromptInput: React.FC = () => {
  const [inputValue, setInputValue] = useState("");
  const [isFileModalOpen, setIsFileModalOpen] = useState(false);
  const [uploadedFilesCount, setUploadedFilesCount] = useState(0);
  const { isOpen } = useSidebar();
  const { isDarkMode } = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustTextareaHeight = (element: HTMLTextAreaElement) => {
    element.style.height = 'auto';
    element.style.height = `${element.scrollHeight}px`;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    adjustTextareaHeight(e.target);
  };

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

  useEffect(() => {
    if (textareaRef.current) {
      adjustTextareaHeight(textareaRef.current);
    }
  }, [inputValue]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    if (!user?.id) {
      toast.error('Please log in to create a new chat');
      return;
    }

    try {
      const threadTitle = inputValue.substring(0, 50) + (inputValue.length > 50 ? '...' : '');
      const response = await chatApi.createNewThread(threadTitle, user.id);
      
      if (response.data && (response.status === 200 || response.status === 201)) {
        const apiThread = response.data;
        
        // Save the thread to localStorage (backward compatibility)
        const threads = JSON.parse(localStorage.getItem('threads') || '[]');
        const newThread = {
          id: apiThread.chat_id,
          title: apiThread.title,
          content: inputValue,
          timestamp: apiThread.created_at,
          uploadedFiles: uploadedFilesCount,
        };
        
        threads.unshift(newThread);
        localStorage.setItem('threads', JSON.stringify(threads));

        console.log('New thread created via API from PromptInput:', apiThread);
        toast.success('New chat created!');

        // Navigate to chat page with the API-generated thread ID and prompt
        navigate(`/chat?chatId=${apiThread.chat_id}&prompt=${encodeURIComponent(inputValue.trim())}`, { replace: true });
        setInputValue("");
        setUploadedFilesCount(0);
      } else {
        throw new Error(response.error || 'Failed to create thread');
      }
    } catch (error) {
      console.error('Failed to create thread via API from PromptInput:', error);
      toast.error('Failed to create new chat. Please try again.');
      // Fallback navigation if API fails
      navigate('/chat', { replace: true });
    }
  };

  return (
    <>
      <div className={`fixed bottom-14 md:bottom-0 left-0 right-0 md:left-64 ${
        isDarkMode ? 'bg-[#282a36]/90' : 'bg-white/90'
      } backdrop-blur-sm border-t ${
        isDarkMode ? 'border-gray-700' : 'border-gray-200'
      }`}>
        <div className="mx-auto px-4 py-4">
          {/* Upload Status Display */}
          {uploadedFilesCount > 0 && (
            <div className="max-w-4xl mx-auto mb-3">
              <motion.div
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
                  isDarkMode ? 'bg-green-900/20 border-green-700/30 text-green-400' : 'bg-green-50 border-green-200 text-green-700'
                }`}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
              >
                <FiFileText className="w-4 h-4 text-green-500" />
                <span className="text-sm">
                  {uploadedFilesCount} PDF file{uploadedFilesCount > 1 ? 's' : ''} uploaded to knowledge base
                </span>
              </motion.div>
            </div>
          )}

          <form 
            onSubmit={handleSubmit}
            className="max-w-4xl mx-auto relative"
          >
            <div className={`flex items-center gap-2 p-3 rounded-xl border ${
              isDarkMode ? 'bg-[#44475a]/50 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <FiCommand className={`w-5 h-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={handleInputChange}
                placeholder="Ask anything..."
                rows={1}
                className={`flex-1 bg-transparent border-none outline-none resize-none ${
                  isDarkMode ? 'text-gray-100 placeholder-gray-500' : 'text-gray-900 placeholder-gray-400'
                }`}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                type="button"
                onClick={() => setIsFileModalOpen(true)}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode
                    ? 'text-gray-400 hover:text-gray-300 hover:bg-gray-700'
                    : 'text-gray-500 hover:text-gray-600 hover:bg-gray-100'
                }`}
                title="Upload PDF files"
              >
                <FiPaperclip className="w-5 h-5" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                type="submit"
                disabled={!inputValue.trim()}
                className={`p-2 rounded-lg transition-colors ${
                  inputValue.trim()
                    ? 'bg-purple-500 text-white hover:bg-purple-600'
                    : isDarkMode
                      ? 'bg-gray-700 text-gray-400'
                      : 'bg-gray-100 text-gray-400'
                }`}
              >
                <FiSend className="w-5 h-5" />
              </motion.button>
            </div>
            <div className="absolute -top-6 right-0">
              <span className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                Press Enter to send, Shift + Enter for new line
              </span>
            </div>
          </form>
        </div>
      </div>

      <FileUploadModal
        isOpen={isFileModalOpen}
        onClose={() => setIsFileModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
        maxFiles={5}
      />
    </>
  );
};

export default PromptInput;
