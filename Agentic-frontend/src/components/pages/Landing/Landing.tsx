import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { useTheme } from '../../../contexts/ThemeContext';
import { useSidebar } from '../../../contexts/SidebarContext';
import { useAuth } from '../../../contexts/AuthContext';
import { FaArrowRight } from "react-icons/fa";
import { FiTarget } from "react-icons/fi";
import { chatApi } from '../../../services/api';
import { getCurrentDateTime, formatToLocalTimezone } from '../../../lib/utils';

const Landing: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const navigate = useNavigate();
  const { theme, isDarkMode } = useTheme();
  const { isOpen: sidebarOpen } = useSidebar();
  const { user } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    if (!user?.id) {
      toast.error('Please log in to create a new chat');
      return;
    }

    try {
      const threadTitle = prompt.substring(0, 50) + (prompt.length > 50 ? '...' : '');
      const response = await chatApi.createNewThread(threadTitle, user.id);
      
      if (response.data && (response.status === 200 || response.status === 201)) {
        const apiThread = response.data;
        
        // Save the thread to localStorage with initial AI greeting (backward compatibility)
        const threads = JSON.parse(localStorage.getItem('threads') || '[]');
        const newThread = {
          id: apiThread.chat_id,
          title: apiThread.title,
          content: prompt,
          timestamp: apiThread.created_at,
          messages: [
            {
              id: Date.now().toString(),
              content: prompt,
              timestamp: apiThread.created_at,
              isUser: true
            },
            {
              id: 'greeting',
              content: "Hi there! This is AI Chatbot. How can I help you?",
              timestamp: formatToLocalTimezone(new Date(Date.now() + 1000)), // Add 1 second to ensure it appears after
              isUser: false
            }
          ]
        };
        
        threads.unshift(newThread);
        localStorage.setItem('threads', JSON.stringify(threads));

        console.log('New thread created via API from Landing:', apiThread);
        toast.success('New chat created!');

        // Navigate to chat page with the API-generated thread ID and prompt
        navigate(`/chat?chatId=${apiThread.chat_id}&prompt=${encodeURIComponent(prompt.trim())}`);
      } else {
        throw new Error(response.error || 'Failed to create thread');
      }
    } catch (error) {
      console.error('Failed to create thread via API from Landing:', error);
      toast.error('Failed to create new chat. Please try again.');
    }
  };

  return (
    <motion.div 
      className={`fixed inset-0 flex flex-col items-center justify-center px-4 overflow-y-auto`}
      animate={{
        marginLeft: sidebarOpen ? "16rem" : "4rem",
      }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 30,
      }}
      style={{
        backgroundColor: isDarkMode ? '#282a36' : '#ffffff',
        marginLeft: typeof window !== 'undefined' && window.innerWidth < 768 ? '0rem' : undefined
      }}
    >
      <h1 
        className="text-4xl font-bold mb-8"
        style={{ color: isDarkMode ? '#f8f8f2' : '#44475a' }}
      >
        What do you want to know?
      </h1>
      
      <div className="w-full max-w-2xl">
        <form onSubmit={handleSubmit} className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask anything..."
            className="w-full rounded-lg pl-12 pr-12 py-4 text-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-colors"
            style={{ 
              backgroundColor: isDarkMode ? '#44475a' : '#f8f8f2',
              color: isDarkMode ? '#f8f8f2' : '#282a36',
              borderColor: isDarkMode ? '#6272a4' : '#8be9fd'
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <div 
            className="absolute left-4 top-1/2 -translate-y-1/2"
            style={{ color: isDarkMode ? '#6272a4' : '#8be9fd' }}
          >
            <FiTarget size={20} />
          </div>
          <button
            type="submit"
            disabled={!prompt.trim()}
            className={`absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded-full transition-colors
              ${!prompt.trim() && 'opacity-50 cursor-not-allowed'}`}
            style={{ 
              color: prompt.trim() 
                ? (isDarkMode ? '#ff79c6' : '#bd93f9')
                : (isDarkMode ? '#6272a4' : '#8be9fd')
            }}
            aria-label="Submit prompt"
          >
            <FaArrowRight size={20} />
          </button>
        </form>
      </div>
    </motion.div>
  );
};

export default Landing;
