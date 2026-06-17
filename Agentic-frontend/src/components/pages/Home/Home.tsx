import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FiMessageSquare, FiBook, FiSettings, FiHelpCircle, FiSend, FiCommand, FiLogOut, FiUser, FiPaperclip, FiFileText } from "react-icons/fi";
import { toast } from "react-hot-toast";
import AnimatedAvatar from '../../AnimatedAvatar/AnimatedAvatar';
import { useTheme } from "../../../contexts/ThemeContext";
import { useSidebar } from "../../../contexts/SidebarContext";
import { useAuth } from "../../../contexts/AuthContext";
import { useSpace } from "../../../contexts/SpaceContext";
import { chatApi } from "../../../services/api";
import FileUploadModal from "../../FileUploadModal/FileUploadModal";
import ChatInput from "../../ChatInput/ChatInput";

const Home: React.FC = () => {
  const navigate = useNavigate();
  const { isDarkMode } = useTheme();
  const { isOpen: sidebarOpen } = useSidebar();
  const { logout, user } = useAuth();
  const { selectedSpace, fetchSpaces } = useSpace();
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);
  const [promptInput, setPromptInput] = useState("");


  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };



  const handlePromptSubmit = async (message: string, responseMode: string) => {
    if (!message.trim()) return;

    if (!user?.id) {
      toast.error('Please log in to create a new chat');
      return;
    }

    try {
      const threadTitle = message.substring(0, 50) + (message.length > 50 ? '...' : '');
      const response = await chatApi.createNewThread(threadTitle, user.id, selectedSpace?.id);

      if (response.data && (response.status === 200 || response.status === 201)) {
        const apiThread = response.data;

        // Create a new thread for local storage (backward compatibility)
        const threads = JSON.parse(localStorage.getItem('threads') || '[]');
        const newThread = {
          id: apiThread.chat_id,
          title: apiThread.title,
          content: message,
          timestamp: apiThread.created_at,
          responseMode: responseMode,
          messages: [{
            id: Date.now().toString(),
            content: message,
            timestamp: apiThread.created_at,
            isUser: true,
            responseMode: responseMode
          }]
        };

        threads.unshift(newThread);
        localStorage.setItem('threads', JSON.stringify(threads));

        console.log('New thread created via API from Home:', apiThread, 'Mode:', responseMode);
        toast.success('New chat created!');

        // Refresh spaces to update thread counts (async, don't block navigation)
        fetchSpaces().catch(err => console.error('Failed to refresh spaces:', err));

        // Navigate to chat with the API-generated thread ID, prompt, and response mode
        navigate(`/chat?chatId=${apiThread.chat_id}&prompt=${encodeURIComponent(message.trim())}&responseMode=${responseMode}`);
        setPromptInput("");
      } else {
        throw new Error(response.error || 'Failed to create thread');
      }
    } catch (error) {
      console.error('Failed to create thread via API from Home:', error);
      toast.error('Failed to create new chat. Please try again.');
    }
  };

  interface Card {
    id: string;
    title: string;
    description: string;
    icon: React.ReactNode;
    path: string;
    color: string;
    onClick?: () => void;
  }

  const cards: Card[] = [
    {
      id: "chat",
      title: "Start a Chat",
      description: "Begin a new conversation with CogniVox AI",
      icon: <FiMessageSquare className="w-5 h-5" />,
      path: "/chat",
      color: "from-purple-500 to-pink-500",
      onClick: () => navigate("/chat")
    },
    {
      id: "library",
      title: "Library",
      description: "Access your saved conversations and history",
      icon: <FiBook className="w-5 h-5" />,
      path: "/library",
      color: "from-blue-500 to-cyan-500"
    },
    {
      id: "settings",
      title: "Settings",
      description: "Customize your CogniVox experience",
      icon: <FiSettings className="w-5 h-5" />,
      path: "/settings",
      color: "from-green-500 to-emerald-500"
    },
    {
      id: "help",
      title: "Help & Support",
      description: "Learn more about using CogniVox",
      icon: <FiHelpCircle className="w-5 h-5" />,
      path: "/help",
      color: "from-yellow-500 to-orange-500"
    }
  ];

  return (
    <>
      <motion.div
        className={`fixed inset-0 overflow-y-auto ${isDarkMode ? 'bg-[#282a36]' : ''
          }`}
        animate={{
          marginLeft: sidebarOpen ? "16rem" : "4rem",
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
        }}
        style={{
          ...(!isDarkMode
            ? {
              background:
                "linear-gradient(135deg,#f8f3ef 0%,#f3eef9 55%,#eef2ff 100%)",
            }
            : {}),
          marginLeft: typeof window !== 'undefined' && window.innerWidth < 768 ? '0rem' : undefined
        }}
      >
        <div className="relative z-10 h-full flex flex-col">
          {!isDarkMode && (
            <>
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  background:
                    "radial-gradient(circle at 20% 30%, rgba(139,92,246,0.12), transparent 40%), radial-gradient(circle at 80% 20%, rgba(59,130,246,0.08), transparent 35%)",
                }}
              />
            </>
          )}
          {/* Main Content */}
          <div className="flex-1 px-4 py-6 overflow-y-auto">
            {/* Welcome Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center mb-8"
            >
              <h1 className={`text-3xl md:text-4xl font-bold mb-3 ${isDarkMode
                ? 'text-gray-100'
                : 'bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent'
                }`}>
                Welcome to CogniVox
              </h1>
              <p className={`text-base ${isDarkMode ? 'text-gray-400' : 'text-[#4a4f7a]'
                }`}>
                Your intelligent conversation companion
              </p>
            </motion.div>

            {/* Cards Grid - Optimized for space usage */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 max-w-6xl mx-auto mb-6">
              {cards.map((card) => (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{
                    scale: 1.02,
                    y: -2
                  }}
                  whileTap={{ scale: 0.98 }}
                  onHoverStart={() => setHoveredCard(card.id)}
                  onHoverEnd={() => setHoveredCard(null)}
                  onClick={() => card.onClick ? card.onClick() : navigate(card.path)}
                  className={`group relative overflow-hidden rounded-xl cursor-pointer transition-all duration-300 ${isDarkMode
                    ? 'bg-[#44475a] hover:bg-[#44475a]/80 border border-gray-700/50 hover:border-gray-600/70'
                    : 'bg-white/80 backdrop-blur-md border border-white/50 hover:border-purple-200'
                    } shadow-lg shadow-purple-100/30 hover:shadow-xl`}
                >
                  <div className="p-4">
                    {/* Icon */}
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center mb-3 shadow-sm`}>
                      {card.icon}
                    </div>

                    {/* Content */}
                    <h3 className={`text-base font-semibold mb-2 ${isDarkMode
                      ? 'text-gray-100'
                      : 'bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent'
                      }`}>
                      {card.title}
                    </h3>
                    <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-[#4a4f7a]'
                      }`}>
                      {card.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Compact Prompt Input */}
          <motion.div
            className={`${isDarkMode
              ? 'bg-[#282a36]'
              : 'bg-white/50 backdrop-blur-md'
              } border-t ${isDarkMode ? 'border-gray-800/50' : 'border-gray-100'
              }`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <div className="max-w-4xl mx-auto">
              <ChatInput
                value={promptInput}
                onChange={setPromptInput}
                onSubmit={handlePromptSubmit}
                placeholder="What would you like to explore today?"
                variant="compact"
                showModeSelector={true}
                className="border-none"
              />
            </div>
          </motion.div>
        </div>
      </motion.div>


    </>
  );
};

export default Home;