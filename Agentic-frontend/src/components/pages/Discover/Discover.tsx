import React, { useState } from "react";
import { motion } from "framer-motion";
import { useTheme } from "../../../contexts/ThemeContext";
import { useSidebar } from "../../../contexts/SidebarContext";
import { FiTrendingUp, FiMonitor, FiDollarSign, FiMusic, FiActivity, FiClock, FiUser, FiHeart, FiShare2, FiBookmark } from "react-icons/fi";

const Discover: React.FC = () => {
  const { isDarkMode } = useTheme();
  const { isOpen: sidebarOpen } = useSidebar();
  const [activeCategory, setActiveCategory] = useState("for-you");

  const categories = [
    { id: "for-you", icon: <FiTrendingUp />, label: "For You", count: 24 },
    { id: "tech", icon: <FiMonitor />, label: "Tech & Science", count: 18 },
    { id: "finance", icon: <FiDollarSign />, label: "Finance", count: 12 },
    { id: "culture", icon: <FiMusic />, label: "Arts & Culture", count: 15 },
    { id: "sports", icon: <FiActivity />, label: "Sports", count: 9 },
  ];

  const blogPosts = [
    {
      id: 1,
      title: "The Future of AI in Everyday Applications",
      excerpt: "Exploring how artificial intelligence is transforming our daily routines and work processes...",
      author: "Dr. Sarah Chen",
      readTime: "5 min read",
      category: "Tech & Science",
      likes: 142,
      published: "2 hours ago",
      imageColor: "from-blue-500 to-purple-600"
    },
    {
      id: 2,
      title: "Understanding Cryptocurrency Market Trends",
      excerpt: "A comprehensive analysis of current crypto markets and what investors should watch for...",
      author: "Michael Torres",
      readTime: "8 min read",
      category: "Finance",
      likes: 89,
      published: "4 hours ago",
      imageColor: "from-green-500 to-emerald-600"
    },
    {
      id: 3,
      title: "Digital Art Revolution: NFTs and Beyond",
      excerpt: "How blockchain technology is reshaping the art world and creating new opportunities...",
      author: "Elena Rodriguez",
      readTime: "6 min read",
      category: "Arts & Culture",
      likes: 203,
      published: "6 hours ago",
      imageColor: "from-purple-500 to-pink-600"
    },
    {
      id: 4,
      title: "Machine Learning in Sports Analytics",
      excerpt: "Professional teams are using AI to gain competitive advantages through data analysis...",
      author: "James Wilson",
      readTime: "7 min read",
      category: "Sports",
      likes: 156,
      published: "1 day ago",
      imageColor: "from-orange-500 to-red-600"
    },
    {
      id: 5,
      title: "Sustainable Technology Solutions",
      excerpt: "Green tech innovations that are helping combat climate change and environmental issues...",
      author: "Dr. Lisa Park",
      readTime: "9 min read",
      category: "Tech & Science",
      likes: 178,
      published: "1 day ago",
      imageColor: "from-teal-500 to-cyan-600"
    },
    {
      id: 6,
      title: "The Psychology of User Experience Design",
      excerpt: "Understanding how cognitive science principles can improve digital product design...",
      author: "Amanda Foster",
      readTime: "4 min read",
      category: "Tech & Science",
      likes: 134,
      published: "2 days ago",
      imageColor: "from-indigo-500 to-blue-600"
    }
  ];

  const filteredPosts = activeCategory === "for-you" 
    ? blogPosts 
    : blogPosts.filter(post => 
        post.category.toLowerCase().includes(activeCategory.toLowerCase()) ||
        activeCategory === "tech" && post.category === "Tech & Science" ||
        activeCategory === "culture" && post.category === "Arts & Culture"
      );

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
          <div className="flex items-center justify-between">
            <div>
              <h1 className={`text-xl font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                Discover
              </h1>
              <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Explore trending topics and articles
              </p>
            </div>
          </div>

          {/* Categories */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-4 overflow-x-auto"
          >
            <div className="flex gap-2 pb-2">
              {categories.map((category) => (
                <motion.button
                  key={category.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setActiveCategory(category.id)}
                  className={`flex items-center px-3 py-2 rounded-lg transition-colors whitespace-nowrap ${
                    activeCategory === category.id
                      ? isDarkMode 
                        ? 'bg-[#44475a] text-purple-400 border border-purple-500/30'
                        : 'bg-purple-100 text-purple-700 border border-purple-200'
                      : isDarkMode
                        ? 'text-gray-400 hover:bg-[#44475a]/50 border border-transparent'
                        : 'text-gray-600 hover:bg-gray-100 border border-transparent'
                  }`}
                >
                  <span className="mr-2">{category.icon}</span>
                  <span className="text-sm">{category.label}</span>
                  <span className={`ml-2 px-1.5 py-0.5 text-xs rounded ${
                    activeCategory === category.id
                      ? isDarkMode
                        ? 'bg-purple-500/20 text-purple-300'
                        : 'bg-purple-200 text-purple-600'
                      : isDarkMode
                        ? 'bg-gray-700 text-gray-400'
                        : 'bg-gray-200 text-gray-500'
                  }`}>
                    {category.count}
                  </span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        </motion.div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {/* Content Grid - Optimized for space usage */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 max-w-none"
          >
            {filteredPosts.map((post, index) => (
              <motion.div
                key={post.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ scale: 1.02, y: -4 }}
                className={`group rounded-lg overflow-hidden cursor-pointer transition-all duration-300 ${
                  isDarkMode 
                    ? 'bg-[#44475a] hover:bg-[#44475a]/80 border border-gray-700/50 hover:border-gray-600/70'
                    : 'bg-white hover:bg-gray-50 border border-gray-200 hover:border-gray-300'
                } hover:shadow-lg`}
              >
                {/* Image Placeholder */}
                <div className={`aspect-video bg-gradient-to-br ${post.imageColor} relative overflow-hidden`}>
                  <div className="absolute inset-0 bg-black/20" />
                  <div className="absolute top-3 right-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      isDarkMode ? 'bg-black/40 text-white' : 'bg-white/90 text-gray-700'
                    }`}>
                      {post.category}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-2 text-xs">
                    <FiClock className="w-3 h-3 text-gray-500" />
                    <span className="text-gray-500">{post.published}</span>
                    <span className="text-gray-400">•</span>
                    <span className="text-gray-500">{post.readTime}</span>
                  </div>

                  <h3 className={`font-semibold mb-2 line-clamp-2 group-hover:text-purple-600 transition-colors ${
                    isDarkMode ? 'text-gray-100' : 'text-gray-900'
                  }`}>
                    {post.title}
                  </h3>

                  <p className={`text-sm line-clamp-3 mb-3 ${
                    isDarkMode ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    {post.excerpt}
                  </p>

                  {/* Author and Actions */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                        isDarkMode ? 'bg-[#282a36]' : 'bg-gray-100'
                      }`}>
                        <FiUser className="w-3 h-3 text-gray-500" />
                      </div>
                      <span className={`text-xs ${
                        isDarkMode ? 'text-gray-400' : 'text-gray-600'
                      }`}>
                        {post.author}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className={`p-1 rounded transition-colors ${
                        isDarkMode 
                          ? 'text-gray-500 hover:text-red-400'
                          : 'text-gray-400 hover:text-red-500'
                      }`}>
                        <FiHeart className="w-3 h-3" />
                      </button>
                      <button className={`p-1 rounded transition-colors ${
                        isDarkMode 
                          ? 'text-gray-500 hover:text-blue-400'
                          : 'text-gray-400 hover:text-blue-500'
                      }`}>
                        <FiShare2 className="w-3 h-3" />
                      </button>
                      <button className={`p-1 rounded transition-colors ${
                        isDarkMode 
                          ? 'text-gray-500 hover:text-yellow-400'
                          : 'text-gray-400 hover:text-yellow-500'
                      }`}>
                        <FiBookmark className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Engagement */}
                  <div className="mt-3 pt-3 border-t border-gray-200/10">
                    <div className="flex items-center gap-1">
                      <FiHeart className="w-3 h-3 text-gray-500" />
                      <span className={`text-xs ${
                        isDarkMode ? 'text-gray-500' : 'text-gray-400'
                      }`}>
                        {post.likes} likes
                      </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* No Results */}
          {filteredPosts.length === 0 && (
            <div className="text-center py-12">
              <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
                isDarkMode ? 'bg-[#44475a]' : 'bg-gray-100'
              }`}>
                <FiTrendingUp className={`w-8 h-8 ${
                  isDarkMode ? 'text-gray-600' : 'text-gray-400'
                }`} />
              </div>
              <p className={`text-base font-medium mb-2 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-600'
              }`}>
                No articles found
              </p>
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-600' : 'text-gray-500'
              }`}>
                Try selecting a different category
              </p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default Discover;
