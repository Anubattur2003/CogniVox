import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import data from "../../../data.json";
import PromptInput from "./PromptInput";
import { useTheme } from "../../../contexts/ThemeContext";
import { useSidebar } from "../../../contexts/SidebarContext";
import { FiPlus, FiBookOpen, FiExternalLink, FiClock, FiMessageSquare } from "react-icons/fi";

interface ThreadData {
  title: string;
  resource: string;
  response: string;
  relatedLinks: string[];
  subThreads?: ThreadData[];
  questions?: { question: string; answer: string }[];
  sources?: { name: string; link?: string }[];
}

const Thread: React.FC = () => {
  const { threadId } = useParams<{ threadId: string }>();
  const [threadData, setThreadData] = useState<ThreadData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isDarkMode } = useTheme();
  const { isOpen: sidebarOpen } = useSidebar();

  useEffect(() => {
    const fetchThreadData = () => {
      if (threadId) {
        const index = parseInt(threadId) - 1;
        if (index >= 0 && index < data.length) {
          setThreadData(data[index]);
          setError(null);
        } else {
          setError("Thread not found");
        }
      }
      setLoading(false);
    };
    fetchThreadData();
  }, [threadId]);

  if (loading) {
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
        <div className="p-4">
          <div className="animate-pulse space-y-4">
            <div className={`h-6 rounded w-1/3 ${isDarkMode ? 'bg-[#44475a]' : 'bg-gray-200'}`}></div>
            <div className={`h-4 rounded w-3/4 ${isDarkMode ? 'bg-[#44475a]' : 'bg-gray-200'}`}></div>
            <div className={`h-4 rounded w-1/2 ${isDarkMode ? 'bg-[#44475a]' : 'bg-gray-200'}`}></div>
            <div className={`h-32 rounded ${isDarkMode ? 'bg-[#44475a]' : 'bg-gray-200'}`}></div>
          </div>
        </div>
      </motion.div>
    );
  }

  if (error) {
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
        <div className="flex items-center justify-center h-full px-4">
          <div className="text-center">
            <h1 className="text-xl font-bold text-red-500 mb-2">Error</h1>
            <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>{error}</p>
          </div>
        </div>
      </motion.div>
    );
  }

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
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isDarkMode ? 'bg-[#44475a]' : 'bg-gray-100'
            }`}>
              <FiBookOpen className={`w-5 h-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`} />
            </div>
            <div className="flex-1">
              <h1 className={`text-lg font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                {threadData?.title}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <FiClock className="w-3 h-3 text-gray-500" />
                <span className="text-xs text-gray-500">Thread #{threadId}</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 max-w-6xl mx-auto">
            
            {/* Questions Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className={`rounded-lg border ${
                isDarkMode 
                  ? 'bg-[#44475a] border-gray-700/50' 
                  : 'bg-white border-gray-200'
              } hover:shadow-lg transition-shadow duration-300`}
            >
              <div className="p-4 border-b border-gray-200/10">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <FiMessageSquare className="w-3 h-3 text-white" />
                  </div>
                  <h2 className={`text-base font-semibold ${
                    isDarkMode ? 'text-gray-100' : 'text-gray-900'
                  }`}>
                    Q&A Discussion
                  </h2>
                </div>
              </div>
              
              <div className="p-4">
                <div className="space-y-4">
                  {threadData?.questions?.map((item, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                      className="space-y-2"
                    >
                      <div className={`p-3 rounded-lg ${
                        isDarkMode ? 'bg-[#282a36]' : 'bg-gray-50'
                      }`}>
                        <h3 className={`text-sm font-medium mb-2 ${
                          isDarkMode ? 'text-blue-400' : 'text-blue-600'
                        }`}>
                          Q: {item.question}
                        </h3>
                        <p className={`text-sm leading-relaxed ${
                          isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                          {item.answer}
                        </p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Sources Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className={`rounded-lg border ${
                isDarkMode 
                  ? 'bg-[#44475a] border-gray-700/50' 
                  : 'bg-white border-gray-200'
              } hover:shadow-lg transition-shadow duration-300`}
            >
              <div className="p-4 border-b border-gray-200/10">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center">
                    <FiExternalLink className="w-3 h-3 text-white" />
                  </div>
                  <h2 className={`text-base font-semibold ${
                    isDarkMode ? 'text-gray-100' : 'text-gray-900'
                  }`}>
                    Sources & References
                  </h2>
                </div>
              </div>

              <div className="p-4">
                <div className="space-y-2">
                  {threadData?.sources?.map((source, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                      className={`p-3 rounded-lg border transition-all duration-200 hover:shadow-sm ${
                        isDarkMode 
                          ? 'bg-[#282a36] border-gray-700/30 hover:border-gray-600/50' 
                          : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`text-sm font-medium ${
                          isDarkMode ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                          {source.name}
                        </span>
                        {source.link && (
                          <a 
                            href={source.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors ${
                              isDarkMode 
                                ? 'text-blue-400 hover:bg-blue-500/10'
                                : 'text-blue-600 hover:bg-blue-50'
                            }`}
                          >
                            <FiExternalLink className="w-3 h-3" />
                            View
                          </a>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>

          {/* CogniVox Response Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className={`mt-4 max-w-6xl mx-auto rounded-lg border ${
              isDarkMode 
                ? 'bg-[#44475a] border-gray-700/50' 
                : 'bg-white border-gray-200'
            } hover:shadow-lg transition-shadow duration-300`}
          >
            <div className="p-4 border-b border-gray-200/10">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 rounded bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                  <span className="text-xs font-bold text-white">AI</span>
                </div>
                <h2 className={`text-base font-semibold ${
                  isDarkMode ? 'text-gray-100' : 'text-gray-900'
                }`}>
                  CogniVox Analysis
                </h2>
              </div>
            </div>
            
            <div className="p-4">
              <div className={`prose max-w-none ${
                isDarkMode ? 'prose-invert' : ''
              }`}>
                <p className={`text-sm leading-relaxed ${
                  isDarkMode ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  {threadData?.response}
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Prompt Input */}
      <PromptInput />
    </motion.div>
  );
};

export default Thread;
