import React, { useState, useEffect, useRef } from "react";
import { useTheme } from "../../../contexts/ThemeContext";
import { useSidebar } from "../../../contexts/SidebarContext";
import { useAuth } from "../../../contexts/AuthContext";
import { useSettings } from "../../../contexts/SettingsContext";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "react-hot-toast";
import SkeletonLoader from '../../SkeletonLoader/SkeletonLoader';
import SourceDocumentModal from '../../SourceDocumentModal/SourceDocumentModal';
import ChatInput from '../../ChatInput/ChatInput';
import { chatApi, ChatSubThread } from "../../../services/api";
import { getCurrentDateTime } from "../../../lib/utils";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  id: string;
  content: string;
  timestamp: string | Date;
  isUser: boolean;
  execution_time?: number;
  sourceObjects?: any[];
  aiResponseData?: {
    summary?: string;
    answer?: string;
    sources?: any[];
    related_links?: string[];
  };
}

interface Thread {
  id: string;
  title: string;
  content: string;
  timestamp: string;
  messages?: Message[];
}

// Component for rendering AI responses with proper structure - Moved outside to prevent re-creation
const AIResponseComponent: React.FC<{ 
  aiData: {
    summary?: string;
    answer?: string;
    sources?: any[];
    related_links?: string[];
  };
  sourceObjects?: any[];
  isDarkMode: boolean;
  onSourceClick?: (source: any) => void;
}> = React.memo(({ aiData, sourceObjects, isDarkMode, onSourceClick }) => {
  const sources = sourceObjects || aiData.sources || [];
  const [localExpandedSources, setLocalExpandedSources] = React.useState(false);
  const [localExpandedSummary, setLocalExpandedSummary] = React.useState(false);

  return (
    <div className="space-y-4">
      {/* Summary Section - Minimalistic Collapsible */}
      {aiData.summary && aiData.summary !== "string" && (
        <motion.div 
          className={`relative rounded-lg border ${
            isDarkMode 
              ? 'bg-blue-900/5 border-blue-500/10 text-blue-100' 
              : 'bg-blue-50/30 border-blue-200/30 text-blue-900'
          } transition-all duration-300`}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          onMouseEnter={() => setLocalExpandedSummary(true)}
          onMouseLeave={() => setLocalExpandedSummary(false)}
        >
          {/* Compact Header */}
          <div className="p-2 px-3">
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${
                isDarkMode ? 'bg-blue-400' : 'bg-blue-500'
              }`} />
              <span className="text-xs font-medium opacity-70">
                Summary
              </span>
            </div>
          </div>

          {/* Collapsible Content */}
          <AnimatePresence>
            {localExpandedSummary && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className={`px-3 pb-3 border-t ${
                  isDarkMode ? 'border-blue-700/10' : 'border-blue-200/20'
                }`}>
                  <div className="pt-3">
                    <div className="prose prose-sm max-w-none dark:prose-invert text-sm leading-relaxed">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {aiData.summary}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Answer Section */}
      {aiData.answer && aiData.answer !== "string" && (
        <motion.div 
          className="space-y-3"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <div className={`prose max-w-none ${
            isDarkMode ? 'prose-invert' : ''
          } prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-p:leading-relaxed prose-p:mb-3`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {aiData.answer}
            </ReactMarkdown>
          </div>
        </motion.div>
      )}

              {/* Source Documents Section - Minimalistic */}
      {sources.length > 0 && sources[0]?.document_title !== "string" && (
        <motion.div 
          className={`relative rounded-lg border ${
            isDarkMode 
              ? 'bg-emerald-900/5 border-emerald-500/10 text-emerald-100' 
              : 'bg-emerald-50/30 border-emerald-200/30 text-emerald-900'
          } transition-all duration-300`}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          onMouseEnter={() => setLocalExpandedSources(true)}
          onMouseLeave={() => setLocalExpandedSources(false)}
        >
          {/* Compact Header */}
          <div className="p-2 px-3">
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${
                isDarkMode ? 'bg-emerald-400' : 'bg-emerald-500'
              }`} />
              <span className="text-xs font-medium opacity-70">
                {sources.length} source{sources.length > 1 ? 's' : ''}
              </span>
            </div>
          </div>

          {/* Collapsible Content */}
          <AnimatePresence>
            {localExpandedSources && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className={`px-3 pb-2 border-t ${
                  isDarkMode ? 'border-emerald-700/10' : 'border-emerald-200/20'
                }`}>
                  <div className="pt-2 flex flex-wrap gap-1.5">
                    {sources.map((source: any, index: number) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.03 }}
                        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs cursor-pointer transition-all ${
                          isDarkMode
                            ? 'bg-emerald-800/20 hover:bg-emerald-700/30 text-emerald-200 border border-emerald-700/20'
                            : 'bg-white/70 hover:bg-white text-emerald-700 border border-emerald-200/50 hover:border-emerald-300'
                        }`}
                        whileHover={{ scale: 1.02 }}
                                                  onClick={() => onSourceClick?.(source)}
                      >
                        <div className={`w-1 h-1 rounded-full ${
                          source.relevance >= 0.8 ? 'bg-green-500' :
                          source.relevance >= 0.6 ? 'bg-yellow-500' : 'bg-orange-500'
                        }`} />
                        <span className="font-medium truncate max-w-[120px]">
                          {source.document_title}
                        </span>
                        <span className="opacity-50">
                          p{source.page}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Related Links Section */}
      {aiData.related_links && aiData.related_links.length > 0 && aiData.related_links[0] !== "string" && (
        <motion.div 
          className={`p-4 rounded-lg ${
            isDarkMode ? 'bg-purple-900/20 border border-purple-500/20' : 'bg-purple-50 border border-purple-200/50'
          }`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
            </svg>
            <h4 className={`font-semibold text-sm ${
              isDarkMode ? 'text-purple-200' : 'text-purple-800'
            }`}>Related Links</h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {aiData.related_links.map((link: string, index: number) => (
              <a
                key={index}
                href={link}
                target="_blank"
                rel="noopener noreferrer"
                className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all hover:scale-105 ${
                  isDarkMode 
                    ? 'bg-purple-600 hover:bg-purple-500 text-white' 
                    : 'bg-purple-100 hover:bg-purple-200 text-purple-800'
                }`}
              >
                <span className="truncate max-w-[200px]">{link}</span>
                <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison to prevent unnecessary re-renders
  return (
    prevProps.isDarkMode === nextProps.isDarkMode &&
    prevProps.onSourceClick === nextProps.onSourceClick &&
    JSON.stringify(prevProps.aiData) === JSON.stringify(nextProps.aiData) &&
    JSON.stringify(prevProps.sourceObjects) === JSON.stringify(nextProps.sourceObjects)
  );
});

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [currentThread, setCurrentThread] = useState<Thread | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const processedPromptsRef = useRef<Set<string>>(new Set()); // Track processed prompts
  const autoSubmitInProgressRef = useRef<Set<string>>(new Set()); // Track in-progress submissions

  const { isDarkMode } = useTheme();
  const { isOpen: isSidebarOpen } = useSidebar();
  const { user } = useAuth();
  const { showExecutionTime } = useSettings();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);

  // Memoized callback to prevent re-renders
  const handleSourceClick = React.useCallback((source: any) => {
    setSelectedDocument(source);
    setIsModalOpen(true);
  }, []);
  const streamEventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => {
      if (streamEventSourceRef.current) {
        streamEventSourceRef.current.close();
      }
    };
  }, []);

  const startTokenStream = (
    taskId: string,
    aiResponseId: string,
    threadToUpdate: Thread,
    onComplete?: () => void
  ) => {
    if (streamEventSourceRef.current) {
      streamEventSourceRef.current.close();
    }

    const token = localStorage.getItem("auth_token");
    // event-source URL format matching django gateway mapping
    const streamUrl = `/api/chat/stream/${taskId}${token ? `?token=${encodeURIComponent(token)}` : ""}`;
    const eventSource = new EventSource(streamUrl);
    streamEventSourceRef.current = eventSource;

    console.log("Started EventSource stream for task:", taskId);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received stream data:", data);

        if (data.token) {
          setMessages((prevMessages) => {
            const updated = prevMessages.map((msg) => {
              if (msg.id === aiResponseId) {
                const currentAnswer = msg.aiResponseData?.answer || "";
                return {
                  ...msg,
                  aiResponseData: {
                    ...msg.aiResponseData,
                    answer: currentAnswer + data.token,
                  },
                };
              }
              return msg;
            });
            return updated;
          });
        } else if (data.status === "done") {
          eventSource.close();
          streamEventSourceRef.current = null;
          setIsGenerating(false);
          console.log("SSE Stream finished successfully");

          // Save final messages to thread and localStorage
          setMessages((prevMessages) => {
            if (threadToUpdate) {
              const threads = JSON.parse(localStorage.getItem("threads") || "[]");
              const threadIndex = threads.findIndex((t: Thread) => t.id === threadToUpdate.id);
              if (threadIndex !== -1) {
                const updatedThread = {
                  ...threadToUpdate,
                  messages: prevMessages,
                };
                threads[threadIndex] = updatedThread;
                setCurrentThread(updatedThread);
                localStorage.setItem("threads", JSON.stringify(threads));
              }
            }
            return prevMessages;
          });

          if (onComplete) onComplete();
        } else if (data.error) {
          console.error("SSE stream error message:", data.error);
          toast.error(data.error);
          eventSource.close();
          streamEventSourceRef.current = null;
          setIsGenerating(false);
          if (onComplete) onComplete();
        } else if (data.sources || data.thinking_steps || data.used_tools) {
          // Update sources and metadata
          setMessages((prevMessages) => {
            return prevMessages.map((msg) => {
              if (msg.id === aiResponseId) {
                return {
                  ...msg,
                  sourceObjects: data.sources || [],
                  aiResponseData: {
                    ...msg.aiResponseData,
                    sources: data.sources || [],
                  },
                };
              }
              return msg;
            });
          });
        }
      } catch (err) {
        console.error("Error parsing SSE message:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource error:", err);
      eventSource.close();
      streamEventSourceRef.current = null;
      setIsGenerating(false);
      toast.error("Stream connection failed. Falling back.");
      if (onComplete) onComplete();
    };
  };
  // Format relative time function with proper timezone handling

  const formatRelativeTime = (timestamp: string | Date) => {
    if (!timestamp) return 'Unknown';
    
    // Parse the ISO string properly (handles timezone offset)
    const date = new Date(timestamp);
    const now = new Date();
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }
    
    const diffInMilliseconds = now.getTime() - date.getTime();
    const diffInSeconds = Math.floor(diffInMilliseconds / 1000);
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);
    
    // Handle future dates (in case of clock skew)
    if (diffInSeconds < 0) {
      return 'just now';
    }
    
    if (diffInSeconds < 60) {
      return 'just now';
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes} minute${diffInMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffInHours < 24) {
      return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`;
    } else if (diffInDays < 7) {
      return `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`;
    } else {
      // For older dates, show full date and time in user's local timezone
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    }
  };

  // Transform ChatSubThread array to Messages format
  const transformSubThreadsToMessages = (subThreads: ChatSubThread[]): Message[] => {
    const messages: Message[] = [];
    
    // Sort sub-threads by creation date in ascending order (oldest first)
    // to ensure messages are displayed chronologically
    const sortedSubThreads = [...subThreads].sort((a, b) => {
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    });
    
    sortedSubThreads.forEach((subThread, index) => {
      // Add user query message
      messages.push({
        id: `${subThread.chat_id}-${index}-query`,
        content: subThread.query,
        timestamp: subThread.created_at,
        isUser: true,
      });
      
      // Add AI response message with structured data
      messages.push({
        id: `${subThread.chat_id}-${index}-answer`,
        content: "", // Not used for structured responses
        timestamp: subThread.updated_at,
        isUser: false,
        execution_time: subThread.execution_time || 0,
        sourceObjects: subThread.sources || [],
        aiResponseData: {
          summary: subThread.summary,
          answer: subThread.answer,
          sources: subThread.sources,
          related_links: subThread.related_links
        }
      });
    });
    
    return messages;
  };

  // Fetch thread data from API
  const fetchThreadData = async (chatId: string) => {
    try {
      setIsLoading(true);
      
      // Fetch both thread details and sub-threads in parallel
      const [threadResponse, subThreadsResponse] = await Promise.all([
        chatApi.getThreadById(chatId),
        chatApi.getSubThreads(chatId)
      ]);
      
      if (threadResponse.data && threadResponse.status === 200 && 
          subThreadsResponse.data && subThreadsResponse.status === 200) {
        const threadData = threadResponse.data;
        const subThreads = subThreadsResponse.data;
        
        // Create thread object for current state using API data
        const thread: Thread = {
          id: chatId,
          title: threadData.title || 'Chat Thread',
          content: '', // Not needed for existing threads
          timestamp: threadData.created_at,
          messages: transformSubThreadsToMessages(subThreads)
        };
        
        setCurrentThread(thread);
        setMessages(thread.messages || []);
      } else {
        console.error('Failed to fetch thread data:', threadResponse.error || subThreadsResponse.error);
        // Fallback to localStorage for old threads
        loadFromLocalStorage(chatId);
      }
    } catch (error) {
      console.error('Error fetching thread data:', error);
      // Fallback to localStorage for old threads
      loadFromLocalStorage(chatId);
    } finally {
      setIsLoading(false);
    }
  };

  // Fallback function to load from localStorage (for old threads)
  const loadFromLocalStorage = (threadId: string) => {
    const threads = JSON.parse(localStorage.getItem('threads') || '[]');
    const thread = threads.find((t: Thread) => t.id === threadId);
    if (thread) {
      setCurrentThread(thread);
      if (thread.messages) {
        setMessages(thread.messages.map((msg: Message) => ({
          ...msg,
          timestamp: msg.timestamp
        })));
      } else {
        const initialMessage = {
          id: thread.id,
          content: thread.content,
          timestamp: thread.timestamp,
          isUser: true,
        };
        setMessages([initialMessage]);
        setIsGenerating(true);

        // Generate AI response for the initial message
        setTimeout(() => {
          const aiResponse: Message = {
            id: Date.now().toString(),
            content: generateAIResponse(thread.content),
            timestamp: getCurrentDateTime(),
            isUser: false,
          };
          const updatedMessages = [initialMessage, aiResponse];
          setMessages(updatedMessages);
          setIsGenerating(false);

          // Update thread in localStorage
          thread.messages = updatedMessages;
          const updatedThreads = threads.map((t: Thread) => 
            t.id === threadId ? thread : t
          );
          localStorage.setItem('threads', JSON.stringify(updatedThreads));
        }, 2000);
      }
    }
  };

  const generateAIResponse = (userQuery: string) => {
    const query = userQuery.toLowerCase();

    if (query.includes('what') && query.includes('ai agent')) {
      return `Summary:
AI agents are autonomous systems that perceive their environment and take actions to achieve specific goals without constant human guidance.

Answer:
# What Are AI Agents?

AI agents are autonomous entities designed to perceive their environment, process information, and take actions to achieve specific goals. They are a core concept in artificial intelligence (AI), representing systems that can operate independently, make decisions, and interact with their surroundings without needing constant human instructions.

## Purpose of AI Agents

The main purpose of AI agents is to automate tasks, solve problems, and make decisions in situations where human oversight is impractical or inefficient. They are essential in advancing AI technology because they enable the creation of systems that can:

• Work independently: Function without continuous human guidance
• Adapt to new situations: Learn from data and experiences to improve over time
• Interact effectively: Communicate or collaborate with humans and other systems

## Key Characteristics

AI agents are defined by several important traits:

• **Autonomy**: They make decisions and act on their own
• **Reactivity**: They respond to changes in their environment
• **Proactivity**: They take initiative to achieve their goals
• **Social ability**: They can interact with other agents or humans

Source Documents:
- Russell, S. & Norvig, P. "Artificial Intelligence: A Modern Approach" - Chapter 2: Intelligent Agents
- Wooldridge, M. "An Introduction to MultiAgent Systems" - Agent Architecture Overview
- MIT OpenCourseWare: 6.034 Artificial Intelligence - Agent Design Principles

Related Links:
- Stanford AI Course - https://cs.stanford.edu/people/eroberts/courses/soco/projects/neural-networks/
- MIT AI Lab Research - https://www.csail.mit.edu/research/artificial-intelligence
- AI Agent Frameworks - https://github.com/microsoft/autogen`;
    }

    if (query.includes('machine learning') || query.includes('ml')) {
      return `Summary:
Machine Learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.

Answer:
Machine Learning (ML) is a powerful subset of artificial intelligence that focuses on developing algorithms and statistical models that enable computers to improve their performance on a specific task through experience, without being explicitly programmed for every scenario.

### Types of Machine Learning

1. **Supervised Learning**: Uses labeled training data to learn patterns
2. **Unsupervised Learning**: Finds hidden patterns in unlabeled data  
3. **Reinforcement Learning**: Learns through interaction and feedback

### Applications

Machine learning is widely used in recommendation systems, image recognition, natural language processing, and predictive analytics.

Source Documents:
- Tom Mitchell "Machine Learning" - Foundational Concepts
- Andrew Ng Stanford CS229 - Machine Learning Course Materials
- scikit-learn Documentation - Practical ML Implementation

Related Links:
- Coursera ML Course - https://www.coursera.org/learn/machine-learning
- Kaggle Learn - https://www.kaggle.com/learn
- Google AI Education - https://ai.google/education/`;
    }
    
    return `Answer:
I apologize, but I don't have specific information about that topic. Could you please ask something else or rephrase your question?

Related Links:
- Search Documentation - https://www.example.com/search
- Help Center - https://www.example.com/help`;
  };

  // Separate component for source documents in formatMessage with isolated state
  const SourceDocumentsSection: React.FC<{ documents: any[] }> = React.memo(({ documents }) => {
    const [localExpanded, setLocalExpanded] = React.useState(false);
    
    if (!documents || documents.length === 0) return null;

    return (
      <motion.div 
        className={`relative rounded-lg border ${
          isDarkMode 
            ? 'bg-emerald-900/5 border-emerald-500/10 text-emerald-100' 
            : 'bg-emerald-50/30 border-emerald-200/30 text-emerald-900'
        } transition-all duration-300`}
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
        onMouseEnter={() => setLocalExpanded(true)}
        onMouseLeave={() => setLocalExpanded(false)}
      >
        {/* Compact Header */}
        <div className="p-2 px-3">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${
              isDarkMode ? 'bg-emerald-400' : 'bg-emerald-500'
            }`} />
            <span className="text-xs font-medium opacity-70">
              {documents.length} source{documents.length > 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Collapsible Content */}
        <AnimatePresence>
          {localExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className={`px-3 pb-2 border-t ${
                isDarkMode ? 'border-emerald-700/10' : 'border-emerald-200/20'
              }`}>
                <div className="pt-2 flex flex-wrap gap-1.5">
                  {documents.map((doc, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.03 }}
                      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs cursor-pointer transition-all ${
                        isDarkMode
                          ? 'bg-emerald-800/20 hover:bg-emerald-700/30 text-emerald-200 border border-emerald-700/20'
                          : 'bg-white/70 hover:bg-white text-emerald-700 border border-emerald-200/50 hover:border-emerald-300'
                      }`}
                      whileHover={{ scale: 1.02 }}
                      onClick={() => {
                        setSelectedDocument(doc);
                        setIsModalOpen(true);
                      }}
                    >
                      <div className={`w-1 h-1 rounded-full ${
                        isDarkMode ? 'bg-emerald-400' : 'bg-emerald-500'
                      }`} />
                      <span className="font-medium truncate max-w-[120px]">
                        Doc {index + 1}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
              </motion.div>
      );
  });

  const formatMessage = (content: string, sourceObjects?: any[]) => {
    // Parse structured response sections
    const sections = {
      summary: '',
      answer: '',
      sourceDocuments: sourceObjects || [] as any[],
      relatedLinks: [] as { title: string; url: string }[]
    };

    // Split content by common section markers
    const lines = content.split('\n').filter(line => line.trim());
    let currentSection = 'answer'; // default section
    let currentContent: string[] = [];

    const processSectionContent = (sectionType: string, content: string[]) => {
      const contentText = content.join('\n').trim();
      if (!contentText) return;

      switch (sectionType) {
        case 'summary':
          sections.summary = contentText;
          break;
        case 'answer':
          sections.answer = contentText;
          break;
        case 'sourceDocuments':
        case 'sources':
          // Skip parsing since we get source objects directly
          break;
        case 'relatedLinks':
        case 'links':
          // Parse links in format "Title - URL" or "[Title](URL)" or just URLs
          content.forEach(line => {
            const trimmed = line.replace(/^[-•*]\s*/, '').trim();
            if (trimmed.includes(' - ') && trimmed.includes('http')) {
              const [title, url] = trimmed.split(' - ', 2);
              sections.relatedLinks.push({ title: title.trim(), url: url.trim() });
            } else if (trimmed.match(/\[([^\]]+)\]\(([^)]+)\)/)) {
              const match = trimmed.match(/\[([^\]]+)\]\(([^)]+)\)/);
              if (match) {
                sections.relatedLinks.push({ title: match[1], url: match[2] });
              }
            } else if (trimmed.startsWith('http')) {
              sections.relatedLinks.push({ title: trimmed, url: trimmed });
            }
          });
          break;
        default:
          sections.answer += (sections.answer ? '\n\n' : '') + contentText;
      }
    };

    // Process each line to identify sections
    for (const line of lines) {
      const lowerLine = line.toLowerCase().trim();
      
      if (lowerLine.startsWith('summary:') || lowerLine === 'summary') {
        processSectionContent(currentSection, currentContent);
        currentSection = 'summary';
        currentContent = lowerLine.includes(':') ? [line.substring(line.indexOf(':') + 1).trim()] : [];
      } else if (lowerLine.startsWith('answer:') || lowerLine === 'answer') {
        processSectionContent(currentSection, currentContent);
        currentSection = 'answer';
        currentContent = lowerLine.includes(':') ? [line.substring(line.indexOf(':') + 1).trim()] : [];
      } else if (lowerLine.includes('source') && (lowerLine.includes('document') || lowerLine.includes('doc'))) {
        processSectionContent(currentSection, currentContent);
        currentSection = 'sourceDocuments';
        currentContent = [];
      } else if (lowerLine.includes('related') && lowerLine.includes('link')) {
        processSectionContent(currentSection, currentContent);
        currentSection = 'relatedLinks';
        currentContent = [];
      } else if (lowerLine === 'sources:' || lowerLine === 'sources') {
        processSectionContent(currentSection, currentContent);
        currentSection = 'sources';
        currentContent = [];
      } else if (lowerLine === 'links:' || lowerLine === 'links') {
        processSectionContent(currentSection, currentContent);
        currentSection = 'links';
        currentContent = [];
      } else {
        currentContent.push(line);
      }
    }

    // Process remaining content
    processSectionContent(currentSection, currentContent);

    // If no structured sections found, treat as regular answer
    if (!sections.summary && !sections.sourceDocuments.length && !sections.relatedLinks.length && !sections.answer) {
      sections.answer = content;
    }

    return (
      <div className="space-y-4">
        {/* Summary Section - Modern Minimalistic */}
        {sections.summary && (
          <motion.div 
            className={`relative p-4 rounded-xl border ${
              isDarkMode 
                ? 'bg-gradient-to-r from-blue-900/10 to-purple-900/10 border-blue-500/20 text-blue-100' 
                : 'bg-gradient-to-r from-blue-50/80 to-purple-50/80 border-blue-200/50 text-blue-900'
            } backdrop-blur-sm`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            {/* Floating icon */}
            <motion.div 
              className={`absolute -top-2 -left-2 p-2 rounded-lg ${
                isDarkMode ? 'bg-blue-600' : 'bg-blue-500'
              } shadow-lg`}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 300, delay: 0.2 }}
            >
              <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
            </motion.div>
            
            <div className="pl-4">
              <motion.h4 
                className="font-medium text-xs uppercase tracking-wide mb-2 opacity-70"
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.7 }}
                transition={{ delay: 0.3 }}
              >
                Summary
              </motion.h4>
              <motion.p 
                className="text-sm leading-relaxed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                {sections.summary}
              </motion.p>
            </div>
          </motion.div>
        )}

        {/* Answer Section */}
        {sections.answer && (
          <div className="space-y-3">
            {sections.answer.split('\n\n').map((paragraph, index) => {
              if (paragraph.startsWith('# ')) {
                return (
                  <h1 key={index} className="text-2xl font-bold mb-4 mt-6">
                    {paragraph.replace('# ', '')}
                  </h1>
                );
              }
              if (paragraph.startsWith('## ')) {
                return (
                  <h2 key={index} className="text-xl font-bold mt-6 mb-3">
                    {paragraph.replace('## ', '')}
                  </h2>
                );
              }
              if (paragraph.startsWith('### ')) {
                return (
                  <h3 key={index} className="text-lg font-semibold mt-4 mb-2">
                    {paragraph.replace('### ', '')}
                  </h3>
                );
              }
              if (paragraph.trim() === '') {
                return <div key={index} className="h-2" />;
              }
              return (
                <p key={index} className="mb-3 leading-relaxed">
                  {paragraph}
                </p>
              );
            })}
          </div>
        )}

        {/* Source Documents Section - Using separate component */}
        <SourceDocumentsSection documents={sections.sourceDocuments} />

        {/* Related Links Section */}
        {sections.relatedLinks.length > 0 && (
          <div className={`p-4 rounded-lg ${
            isDarkMode ? 'bg-purple-900/20' : 'bg-purple-50'
          }`}>
            <div className="flex items-center gap-2 mb-3">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
              </svg>
              <h4 className={`font-semibold text-sm ${
                isDarkMode ? 'text-purple-200' : 'text-purple-800'
              }`}>Related Links</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {sections.relatedLinks.map((link, index) => (
                <a
                  key={index}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all hover:scale-105 ${
                    isDarkMode 
                      ? 'bg-purple-600 hover:bg-purple-500 text-white' 
                      : 'bg-purple-100 hover:bg-purple-200 text-purple-800'
                  }`}
                >
                  <span>{link.title}</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const navigate = useNavigate();
  
  useEffect(() => {
    const chatId = searchParams.get('chatId');
    const threadId = searchParams.get('threadId'); // For backwards compatibility
    const prompt = searchParams.get('prompt');
    const responseMode = searchParams.get('responseMode') || 'general'; // Extract response mode from URL

    console.log('useEffect triggered with params:', { chatId, threadId, prompt, responseMode });

    // Redirect to home if no chat ID is provided (reload without params)
    if (!chatId && !threadId) {
      console.log('No chat ID found, redirecting to home...');
      navigate('/home');
      return;
    }

    if (chatId) {
      // New API-based thread loading
      fetchThreadData(chatId);
      
      // Handle automatic prompt submission for new threads
      if (prompt && prompt.trim()) {
        const promptKey = `${chatId}-${prompt}`;
        console.log('Processing prompt:', promptKey, 'Already processed:', processedPromptsRef.current.has(promptKey), 'In progress:', autoSubmitInProgressRef.current.has(promptKey));
        
        // Prevent duplicate processing of the same prompt
        if (!processedPromptsRef.current.has(promptKey) && !autoSubmitInProgressRef.current.has(promptKey)) {
          processedPromptsRef.current.add(promptKey);
          autoSubmitInProgressRef.current.add(promptKey);
          console.log('Adding prompt to processed list:', promptKey);
          
          setTimeout(async () => {
            // Show user message and AI response placeholder immediately
            const userMessage: Message = {
              id: Date.now().toString(),
              content: prompt,
              timestamp: getCurrentDateTime(),
              isUser: true,
            };

            const aiResponsePlaceholderId = (Date.now() + 1).toString();
            const aiResponsePlaceholder: Message = {
              id: aiResponsePlaceholderId,
              content: "",
              timestamp: getCurrentDateTime(),
              isUser: false,
              aiResponseData: {
                answer: "",
                summary: "",
                sources: [],
                related_links: []
              }
            };

            setMessages([userMessage, aiResponsePlaceholder]);
            setInputValue("");
            setIsGenerating(true);
            try {

              const response = await chatApi.submitChatQuery(
                chatId,
                prompt.trim(),
                5,
                responseMode // Use response mode from URL
              );
              if (response.data && (response.status === 200 || response.status === 201 || response.status === 202)) {
                const { task_id } = response.data;
                const threadToUpdate: Thread = {
                  id: chatId,
                  title: "New Chat Thread",
                  content: prompt,
                  timestamp: getCurrentDateTime(),
                  messages: [userMessage, aiResponsePlaceholder]
                };
                startTokenStream(task_id, aiResponsePlaceholderId, threadToUpdate, () => {
                  autoSubmitInProgressRef.current.delete(promptKey);
                });
                console.log('Auto-submitted prompt and initiated token stream. Task ID:', task_id);
              } else {
                throw new Error(response.error || 'Failed to get AI response');
              }
            } catch (error) {
              console.error('Failed to auto-submit prompt:', error);
              setIsGenerating(false);
              autoSubmitInProgressRef.current.delete(promptKey);
              toast.error('Failed to get AI response for your query.');
            }
          }, 500); // Small delay to ensure thread is loaded
        }
      }
    } else if (threadId) {
      // Legacy localStorage-based thread loading
      loadFromLocalStorage(threadId);
      
      // Handle prompt for new threads
      if (prompt) {
        const threads = JSON.parse(localStorage.getItem('threads') || '[]');
        const thread = threads.find((t: Thread) => t.id === threadId);
        if (thread && thread.messages && thread.messages.length === 1) {
          setIsGenerating(true);
          setTimeout(() => {
            const aiResponse: Message = {
              id: Date.now().toString(),
              content: generateAIResponse(prompt),
              timestamp: getCurrentDateTime(),
              isUser: false,
            };
            const updatedMessages = [...thread.messages, aiResponse];
            setMessages(updatedMessages.map(msg => ({
              ...msg,
              timestamp: msg.timestamp
            })));
            setIsGenerating(false);

            // Update thread in localStorage
            thread.messages = updatedMessages;
            const updatedThreads = threads.map((t: Thread) => 
              t.id === threadId ? thread : t
            );
            localStorage.setItem('threads', JSON.stringify(updatedThreads));
          }, 2000);
        }
      }
    }
  }, [searchParams]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isModalOpen) {
        setIsModalOpen(false);
        setSelectedDocument(null);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isModalOpen]);

  const handleSubmit = async (message: string, responseMode: string) => {
    if (!message.trim() || isGenerating) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: message,
      timestamp: getCurrentDateTime(),
      isUser: true,
    };

    let activeThread = currentThread;

    // If no currentThread exists, create a new one using the API
    if (!activeThread) {
      if (!user?.id) {
        toast.error('Please log in to create a new chat');
        return;
      }

      try {
        const threadTitle = message.substring(0, 50) + (message.length > 50 ? '...' : '');
        const response = await chatApi.createNewThread(threadTitle, user.id);
        
        if (response.data && response.status === 201) {
          const apiThread = response.data;
          
          // Create thread object with the API response data
          const newThread: Thread = {
            id: apiThread.chat_id, // Use the chat_id returned from API
            title: apiThread.title,
            content: message,
            timestamp: apiThread.created_at,
            messages: [newMessage]
          };
          
          activeThread = newThread;
          setCurrentThread(newThread);
          setMessages([newMessage]);
          
          console.log('New thread created via API:', apiThread, 'Mode:', responseMode);
          toast.success('New chat created!');
          
          // Save to localStorage for backward compatibility
          const threads = JSON.parse(localStorage.getItem('threads') || '[]');
          threads.unshift(newThread);
          localStorage.setItem('threads', JSON.stringify(threads));
        } else {
          throw new Error(response.error || 'Failed to create thread');
        }
      } catch (error) {
        console.error('Failed to create thread via API:', error);
        toast.error('Failed to create new chat. Please try again.');
        return;
      }
    } else {
      // Add message to existing thread
      const updatedMessages = [...messages, newMessage];
      activeThread = {
        ...activeThread,
        messages: updatedMessages
      };
      setMessages(updatedMessages);
    }

    setInputValue("");
    setIsGenerating(true);

    // Scroll to bottom immediately
    setTimeout(() => scrollToBottom(), 100);

    // Submit query to AI API
    try {
      if (!activeThread) {
        throw new Error('No current thread available');
      }

      // Add a placeholder AI response message that will be populated via SSE stream
      const aiResponsePlaceholderId = (Date.now() + 1).toString();
      const aiResponsePlaceholder: Message = {
        id: aiResponsePlaceholderId,
        content: "",
        timestamp: getCurrentDateTime(),
        isUser: false,
        aiResponseData: {
          answer: "",
          summary: "",
          sources: [],
          related_links: []
        }
      };

      const finalMessagesWithPlaceholder = [...(activeThread.messages || []), aiResponsePlaceholder];
      setMessages(finalMessagesWithPlaceholder);

      const threadToUpdate: Thread = {
        ...activeThread,
        messages: finalMessagesWithPlaceholder
      };

      const response = await chatApi.submitChatQuery(
        activeThread.id,
        newMessage.content,
        5, // Number of results
        responseMode // Pass response mode directly for routing
      );

      if (response.data && (response.status === 200 || response.status === 201 || response.status === 202)) {
        const { task_id } = response.data;
        startTokenStream(task_id, aiResponsePlaceholderId, threadToUpdate);
        console.log('AI response generation task initiated:', task_id);
      } else {
        throw new Error(response.error || 'Failed to trigger AI generation task');
      }
    } catch (error) {
      console.error('Failed to get AI response:', error);
      
      // Fallback to mock response on error
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: generateAIResponse(newMessage.content),
        timestamp: getCurrentDateTime(),
        isUser: false,
      };
      
      const finalMessages = [...(activeThread ? activeThread.messages || [] : []), aiResponse];
      setMessages(finalMessages);
      setIsGenerating(false);

      // Update thread in localStorage
      if (activeThread) {
        const threads = JSON.parse(localStorage.getItem('threads') || '[]');
        const threadIndex = threads.findIndex((t: Thread) => t.id === activeThread.id);
        if (threadIndex !== -1) {
          const updatedThread = {
            ...activeThread,
            messages: finalMessages
          };
          threads[threadIndex] = updatedThread;
          setCurrentThread(updatedThread);
          localStorage.setItem('threads', JSON.stringify(threads));
        }
      }

      toast.error('Failed to get AI response. Using fallback.');
    }

    // Scroll to bottom after response
    setTimeout(() => scrollToBottom(), 100);
  };

  return (
    <div className={`fixed inset-0 ${isDarkMode ? 'bg-[#282a36]' : 'bg-white'} overflow-hidden flex flex-col`}>
      {/* Thread Title Header - Modern Aesthetic - Always Show */}
      <motion.div 
        className={`border-b backdrop-blur-sm ${
          isDarkMode 
            ? 'border-gray-700/30 bg-[#282a36]/80' 
            : 'border-gray-200/50 bg-white/80'
        }`}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        <motion.div 
          className="px-4 md:px-6 py-5"
          animate={{
            marginLeft: isSidebarOpen ? "16rem" : "4rem",
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
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2, duration: 0.4 }}
                className="flex items-center gap-3 mb-2"
              >
                {/* Chat indicator */}
                <motion.div 
                  className={`p-2 rounded-lg ${
                    isDarkMode ? 'bg-purple-600/20' : 'bg-purple-100'
                  } shadow-sm`}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", delay: 0.3, stiffness: 300 }}
                >
                  <svg className={`w-4 h-4 ${
                    isDarkMode ? 'text-purple-400' : 'text-purple-600'
                  }`} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                  </svg>
                </motion.div>
                
                <div className="flex-1 min-w-0">
                  <motion.h1 
                    className={`text-lg font-semibold truncate ${
                      isDarkMode ? 'text-gray-100' : 'text-gray-900'
                    }`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4, duration: 0.3 }}
                  >
                    {currentThread ? currentThread.title : 'New Chat'}
                  </motion.h1>
                  
                  <motion.div
                    className="flex items-center gap-3 mt-1"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5, duration: 0.3 }}
                  >
                    {currentThread ? (
                      <>
                        <div className="flex items-center gap-1.5">
                          <svg className={`w-3 h-3 ${
                            isDarkMode ? 'text-gray-500' : 'text-gray-400'
                          }`} fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                          </svg>
                          <span className={`text-xs ${
                            isDarkMode ? 'text-gray-400' : 'text-gray-500'
                          }`}>
                            Created {formatRelativeTime(currentThread.timestamp)}
                          </span>
                        </div>
                        
                        {messages.length > 0 && (
                          <>
                            <div className={`w-1 h-1 rounded-full ${
                              isDarkMode ? 'bg-gray-600' : 'bg-gray-300'
                            }`} />
                            <div className="flex items-center gap-1.5">
                              <svg className={`w-3 h-3 ${
                                isDarkMode ? 'text-gray-500' : 'text-gray-400'
                              }`} fill="currentColor" viewBox="0 0 20 20">
                                <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
                                <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
                              </svg>
                              <span className={`text-xs ${
                                isDarkMode ? 'text-gray-400' : 'text-gray-500'
                              }`}>
                                Last activity {formatRelativeTime(messages[messages.length - 1]?.timestamp)}
                              </span>
                            </div>
                          </>
                        )}
                      </>
                    ) : (
                      <div className="flex items-center gap-1.5">
                        <svg className={`w-3 h-3 ${
                          isDarkMode ? 'text-gray-500' : 'text-gray-400'
                        }`} fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clipRule="evenodd" />
                        </svg>
                        <span className={`text-xs ${
                          isDarkMode ? 'text-gray-400' : 'text-gray-500'
                        }`}>
                          Start a conversation below
                        </span>
                      </div>
                    )}
                  </motion.div>
                </div>
              </motion.div>
            </div>
            
            {/* Status indicator */}
            <motion.div
              className="flex items-center gap-2 ml-4"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.6, duration: 0.3 }}
            >
              <motion.div 
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                  isDarkMode 
                    ? 'bg-green-900/30 text-green-400 border border-green-700/30' 
                    : 'bg-green-50 text-green-700 border border-green-200'
                }`}
                animate={{ 
                  scale: [1, 1.02, 1],
                }}
                transition={{ 
                  duration: 3, 
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                <motion.div 
                  className={`w-1.5 h-1.5 rounded-full ${
                    isDarkMode ? 'bg-green-400' : 'bg-green-500'
                  }`}
                  animate={{ 
                    opacity: [0.4, 1, 0.4],
                  }}
                  transition={{ 
                    duration: 2, 
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
                <span>Ready</span>
              </motion.div>
            </motion.div>
          </div>
        </motion.div>
      </motion.div>

      {/* Main Messages Container with Sidebar Margin */}
      <motion.div 
        className="flex-1 overflow-hidden"
        animate={{
          marginLeft: isSidebarOpen ? "16rem" : "4rem",
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
        <div className="h-full overflow-y-auto">
            <div className="px-4 md:px-6 py-4 space-y-4 pb-32">
              {/* Loading state for fetching thread data */}
              {isLoading && (
                <motion.div
                  className="w-full"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className={`flex items-center gap-2 mb-2 ${
                    isDarkMode ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      isDarkMode ? 'bg-gray-400' : 'bg-gray-600'
                    }`} />
                    <span className="text-sm font-medium">Loading conversation...</span>
                  </div>
                  <div className={`pl-4 border-l-2 ${
                    isDarkMode ? 'border-gray-400/30' : 'border-gray-600/30'
                  }`}>
                    <SkeletonLoader variant="message" />
                  </div>
                </motion.div>
              )}
              
              {!isLoading && messages.map((message, index) => (
              <motion.div
                key={message.id}
                className="w-full"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: 0.4,
                  delay: index * 0.1,
                  type: "spring",
                  stiffness: 100
                }}
              >
                {/* Message Header */}
                <div className={`flex items-center gap-2 mb-2 ${
                  message.isUser 
                    ? (isDarkMode ? 'text-blue-400' : 'text-blue-600')
                    : (isDarkMode ? 'text-green-400' : 'text-green-600')
                }`}>
                  <div className={`w-2 h-2 rounded-full ${
                    message.isUser 
                      ? (isDarkMode ? 'bg-blue-400' : 'bg-blue-600')
                      : (isDarkMode ? 'bg-green-400' : 'bg-green-600')
                  }`} />
                  <span className="text-sm font-medium">
                    {message.isUser ? 'You' : 'AI Assistant'}
                  </span>
                  <span className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                  
                                    {/* Execution Time - Only show for AI responses and if enabled in settings */}
                  {!message.isUser && message.execution_time !== undefined && message.execution_time > 0 && showExecutionTime && (
                    <>
                      <div className={`w-1 h-1 rounded-full ${
                        isDarkMode ? 'bg-gray-600' : 'bg-gray-300'
                      }`} />
                      <motion.div
                        className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${
                          isDarkMode 
                            ? 'bg-amber-900/20 text-amber-400 border border-amber-700/30' 
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3, delay: 0.2 }}
                        title={`Query processed in ${message.execution_time.toFixed(3)} seconds`}
                      >
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                        </svg>
                        <span className="font-medium">
                          {message.execution_time < 1 
                            ? `${(message.execution_time * 1000).toFixed(0)}ms`
                            : `${message.execution_time.toFixed(1)}s`
                          }
                        </span>
                      </motion.div>
                    </>
                  )}
                </div>

                {/* Message Content */}
                <div className={`pl-4 border-l-2 ${
                  message.isUser 
                    ? (isDarkMode ? 'border-blue-400/30' : 'border-blue-600/30')
                    : (isDarkMode ? 'border-green-400/30' : 'border-green-600/30')
                }`}>
                  <div className={`leading-relaxed ${
                    isDarkMode ? 'text-gray-100' : 'text-gray-900'
                  }`}>
                    {message.isUser ? (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    ) : message.aiResponseData ? (
                      <AIResponseComponent 
                        aiData={message.aiResponseData} 
                        sourceObjects={message.sourceObjects}
                        isDarkMode={isDarkMode}
                        onSourceClick={handleSourceClick}
                      />
                    ) : (
                      <div className="text-justify">
                        {formatMessage(message.content, message.sourceObjects)}
                      </div>
                    )}
                  </div>
                </div>

                {/* Separator Line */}
                {index < messages.length - 1 && (
                  <div className={`mt-6 border-b ${
                    isDarkMode ? 'border-gray-700/50' : 'border-gray-200/50'
                  }`} />
                )}
              </motion.div>
            ))}

            {/* AI Response Loading Skeleton */}
            <AnimatePresence>
              {isGenerating && (
                <motion.div
                  className="w-full"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* AI Header */}
                  <div className={`flex items-center gap-2 mb-2 ${
                    isDarkMode ? 'text-green-400' : 'text-green-600'
                  }`}>
                    <div className={`w-2 h-2 rounded-full ${
                      isDarkMode ? 'bg-green-400' : 'bg-green-600'
                    }`} />
                    <span className="text-sm font-medium">AI Assistant</span>
                    <div className="flex items-center gap-1 ml-2">
                      <motion.div
                        className={`w-1 h-1 rounded-full ${
                          isDarkMode ? 'bg-green-400' : 'bg-green-600'
                        }`}
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 0.8, repeat: Infinity, delay: 0 }}
                      />
                      <motion.div
                        className={`w-1 h-1 rounded-full ${
                          isDarkMode ? 'bg-green-400' : 'bg-green-600'
                        }`}
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 0.8, repeat: Infinity, delay: 0.2 }}
                      />
                      <motion.div
                        className={`w-1 h-1 rounded-full ${
                          isDarkMode ? 'bg-green-400' : 'bg-green-600'
                        }`}
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 0.8, repeat: Infinity, delay: 0.4 }}
                      />
                    </div>
                  </div>

                  {/* Skeleton Content */}
                  <div className={`pl-4 border-l-2 ${
                    isDarkMode ? 'border-green-400/30' : 'border-green-600/30'
                  }`}>
                    <SkeletonLoader variant="message" />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

              <div ref={messagesEndRef} />
            </div>
          </div>
        </motion.div>

      {/* Input Area - Outside sidebar margin so border extends full width */}
      <motion.div 
        className={`${
          isDarkMode ? 'bg-[#282a36]' : 'bg-white'
        } border-t ${
          isDarkMode ? 'border-gray-700/50' : 'border-gray-200'
        }`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
      >
        <motion.div 
          className="w-full"
          animate={{
            paddingLeft: isSidebarOpen ? "16rem" : "4rem",
          }}
          transition={{
            type: "spring",
            stiffness: 300,
            damping: 30,
          }}
          style={{
            paddingLeft: typeof window !== 'undefined' && window.innerWidth < 768 ? '0rem' : undefined
          }}
        >
          <div className="max-w-4xl mx-auto">
            <ChatInput
                value={inputValue}
              onChange={setInputValue}
              onSubmit={handleSubmit}
                placeholder={currentThread ? "Continue the conversation..." : "Start a new conversation..."}
                disabled={isGenerating}
              isGenerating={isGenerating}
              variant="default"
              showModeSelector={true}
              className=""
            />
            </div>
        </motion.div>
      </motion.div>

      {/* Source Document Modal */}
      <SourceDocumentModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedDocument(null);
        }}
        document={selectedDocument}
      />


    </div>
  );
};

export default Chat; 