import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { 
  FaRocket, 
  FaBrain, 
  FaSearch, 
  FaShieldAlt, 
  FaBolt, 
  FaUsers, 
  FaChartLine, 
  FaCode, 
  FaStar, 
  FaArrowRight,
  FaPlay,
  FaCheckCircle,
  FaMicrochip,
  FaNetworkWired,
  FaEye,
  FaHandshake,
  FaDatabase,
  FaLinkedin,
  FaGithub,
  FaTwitter,
  FaPaperPlane
} from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import { Meteors } from '../../components/magicui/meteors';
import { MagicCard } from '../../components/magicui/magic-card';
import { EarthGlobe } from '../../components/3d-globe/index';
import StarField from '../../components/StarField';

const LandingPage: React.FC = () => {
  const { isDarkMode } = useTheme();
  const navigate = useNavigate();
  const [currentFeature, setCurrentFeature] = useState(0);
  const [inputValue, setInputValue] = useState('');
  const [isInputFocused, setIsInputFocused] = useState(false);

  const handleAuth = (type: 'signin' | 'signup') => {
    if (type === 'signin') {
      navigate('/login');
    } else {
      navigate('/signup');
    }
  };

  const handleInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      // For demo purposes, navigate to signup with the query
      navigate('/signup', { state: { query: inputValue } });
    }
  };

  const dropdownCategories = [
    {
      title: "Document Processing",
      icon: <FaRocket className="w-4 h-4" />,
      suggestions: [
        "Analyze PDF documents",
        "Extract text from images", 
        "Process legal contracts",
        "Summarize research papers"
      ]
    },
    {
      title: "Knowledge Graphs",
      icon: <FaNetworkWired className="w-4 h-4" />,
      suggestions: [
        "Create knowledge network",
        "Find document relationships",
        "Explore entity connections",
        "Build concept maps"
      ]
    },
    {
      title: "AI Chat",
      icon: <FaBrain className="w-4 h-4" />,
      suggestions: [
        "Ask questions about data",
        "Get intelligent insights",
        "Chat with documents",
        "Query knowledge base"
      ]
    },
    {
      title: "Search & Memory", 
      icon: <FaSearch className="w-4 h-4" />,
      suggestions: [
        "Semantic search documents",
        "Find similar content",
        "Remember past conversations",
        "Contextual information retrieval"
      ]
    }
  ];

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
    setIsInputFocused(false);
  };

  // Auto-rotate features every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % 4);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Core features data
  const coreFeatures = [
    {
      icon: <FaBrain className="w-8 h-8 text-white" />,
      title: "Intelligent Memory",
      description: "Multi-level memory system with persistent conversation context",
      color: "from-purple-500 to-purple-600",
      details: "Advanced L0/L1/L2 memory hierarchy for optimal performance"
    },
    {
      icon: <FaNetworkWired className="w-8 h-8 text-white" />,
      title: "Knowledge Graphs",
      description: "Transform documents into searchable knowledge networks",
      color: "from-blue-500 to-blue-600",
      details: "Neo4j-powered semantic relationships and graph traversal"
    },
    {
      icon: <FaSearch className="w-8 h-8 text-white" />,
      title: "Hybrid Search",
      description: "Semantic and keyword search with intelligent fusion",
      color: "from-green-500 to-green-600",
      details: "Vector embeddings combined with traditional search methods"
    },
    {
      icon: <FaMicrochip className="w-8 h-8 text-white" />,
      title: "Multi-Agent AI",
      description: "Specialized agents for query processing and response generation",
      color: "from-orange-500 to-orange-600",
      details: "Query validation, intent classification, and context awareness"
    }
  ];

  // Services data
  const services = [
    {
      icon: <FaRocket className="w-6 h-6" />,
      title: "Document Processing",
      description: "Intelligent PDF processing with adaptive chunking and OCR capabilities"
    },
    {
      icon: <FaBrain className="w-6 h-6" />,
      title: "Conversational AI",
      description: "Multi-agent chat system with persistent memory and context awareness"
    },
    {
      icon: <FaDatabase className="w-6 h-6" />,
      title: "Knowledge Management",
      description: "Graph-based knowledge storage with semantic relationships"
    },
    {
      icon: <FaShieldAlt className="w-6 h-6" />,
      title: "Enterprise Security",
      description: "JWT authentication, user isolation, and secure data handling"
    },
    {
      icon: <FaBolt className="w-6 h-6" />,
      title: "Real-time Processing",
      description: "Streaming responses with GPU acceleration and async processing"
    },
    {
      icon: <FaUsers className="w-6 h-6" />,
      title: "Multi-tenant Support",
      description: "User-specific workspaces with isolated data and conversations"
    }
  ];

  // Business benefits data
  const businessBenefits = [
    {
      metric: "10x",
      label: "Faster Knowledge Retrieval",
      description: "Semantic search with vector embeddings"
    },
    {
      metric: "99.9%",
      label: "Response Accuracy",
      description: "Context-aware AI with persistent memory"
    },
    {
      metric: "24/7",
      label: "Available Operations",
      description: "Scalable containerized deployment"
    },
    {
      metric: "50+",
      label: "Document Types Supported",
      description: "PDF, text, and multi-modal processing"
    }
  ];

  // Technology stack
  const techStack = [
    { name: "React", category: "Frontend" },
    { name: "FastAPI", category: "Backend" },
    { name: "Neo4j", category: "Database" },
    { name: "MongoDB", category: "Database" },
    { name: "PostgreSQL", category: "Database" },
    { name: "Ollama", category: "AI/ML" },
    { name: "Docker", category: "DevOps" },
    { name: "ChromaDB", category: "Vector DB" }
  ];

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-gray-100' : 'bg-gradient-to-br from-gray-50 via-white to-gray-50 text-gray-900'}`}>
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 ${isDarkMode ? 'bg-gray-900/80' : 'bg-white/80'} backdrop-blur-lg border-b ${isDarkMode ? 'border-gray-800' : 'border-gray-200'}`}>
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-4 flex justify-between items-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center space-x-2"
          >
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
              <FaBrain className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              CogniVox
            </h1>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="flex items-center gap-4"
          >
            <button
              onClick={() => handleAuth('signin')}
              className={`px-6 py-2 rounded-lg transition-all duration-200 ${
                isDarkMode 
                  ? 'hover:bg-gray-800 text-gray-100 border border-gray-700 hover:border-gray-600' 
                  : 'hover:bg-gray-100 text-gray-900 border border-gray-200 hover:border-gray-300'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => handleAuth('signup')}
              className="px-6 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              Get Started
            </button>
          </motion.div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-4 md:px-6 pt-24 pb-16 overflow-hidden">
        {/* Beautiful Star Field Background covering complete hero section */}
        <StarField 
          className="w-full h-full"
          width="100%"
          height="100%"
        />
        
        {/* Interactive Earth Globe - Bottom Right */}
        <div className="absolute bottom-10 right-10 w-[300px] h-[300px] md:w-[400px] md:h-[400px] lg:w-[500px] lg:h-[500px] z-10">
          <EarthGlobe 
            className="opacity-80 hover:opacity-100 transition-all duration-1000"
            width="100%"
            height="100%"
            showBackground={false}
            showStars={false}
            showSun={true}
            showMoon={true}
            showSatellites={false}
            showInfo={false}
            showGlobe={true}
            autoRotate={true}
            autoRotateSpeed={0.1}
            enableZoom={true}
            enablePan={true}
            lockPosition={false}
            maxDistance={15}
            minDistance={5}
            cameraPosition={[4, 2, 8]}
          />
        </div>

        {/* Subtle Gradient Overlay for Content Readability */}
        <div className="absolute inset-0 w-full h-full z-10 bg-gradient-to-b from-transparent via-transparent to-black/20" />

        {/* Hero Content */}
        <div className="relative z-20 max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-16"
          >
            <h1 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">
              <span className="bg-gradient-to-r from-purple-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
                CogniVox
              </span>
            </h1>
            
            <p className="text-2xl md:text-3xl mb-16 font-light tracking-wide text-white">
              AI-powered knowledge intelligence
            </p>
          </motion.div>

          {/* Modern Search Interface */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="max-w-4xl mx-auto mb-8"
          >
            {/* Main Search Bar */}
            <MagicCard
              className={`${isDarkMode ? 'bg-gray-900/80 border-gray-700/50' : 'bg-white/80 border-gray-200/50'} backdrop-blur-xl mb-6`}
              gradientColor={isDarkMode ? '#1f2937' : '#f3f4f6'}
              gradientOpacity={0.4}
              gradientFrom="#8b5cf6"
              gradientTo="#3b82f6"
            >
              <form onSubmit={handleInputSubmit} className="p-1">
                <div className="flex items-center gap-4 px-6 py-3">
                  <FaSearch className="w-5 h-5 text-white/70" />
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onFocus={() => setIsInputFocused(true)}
                    onBlur={() => setIsInputFocused(false)}
                    placeholder="Ask anything about your documents..."
                    className="flex-1 text-lg bg-transparent text-white placeholder-white/60 focus:outline-none"
                  />
                  <motion.button
                    type="submit"
                    disabled={!inputValue.trim()}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                      inputValue.trim()
                        ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white shadow-lg'
                        : isDarkMode
                          ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                          : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <FaArrowRight className="w-4 h-4" />
                  </motion.button>
                </div>
              </form>
            </MagicCard>

            {/* Floating Suggestion Pills */}
          <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="flex flex-wrap gap-3 justify-center"
            >
              {[
                { text: 'Analyze PDF documents', icon: <FaRocket className="w-3 h-3" /> },
                { text: 'Create knowledge graphs', icon: <FaNetworkWired className="w-3 h-3" /> },
                { text: 'Chat with documents', icon: <FaBrain className="w-3 h-3" /> },
                { text: 'Find relationships', icon: <FaSearch className="w-3 h-3" /> },
                { text: 'Extract insights', icon: <FaEye className="w-3 h-3" /> },
                { text: 'Process contracts', icon: <FaShieldAlt className="w-3 h-3" /> }
              ].map((suggestion, index) => (
                <motion.button
                  key={suggestion.text}
                  initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + index * 0.05 }}
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleSuggestionClick(suggestion.text)}
                  className="px-4 py-2 rounded-full text-sm transition-all duration-200 flex items-center gap-2 bg-white/10 text-white hover:bg-white/20 hover:text-white border border-white/20 backdrop-blur-sm shadow-lg hover:shadow-xl"
                >
                  <span className="p-1 rounded bg-white/20">
                    {suggestion.icon}
                  </span>
                  {suggestion.text}
                </motion.button>
              ))}
            </motion.div>

            {/* Auto-complete Suggestions */}
            <AnimatePresence>
              {isInputFocused && inputValue.length > 2 && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{ duration: 0.2 }}
                  className="mt-3 p-3 rounded-xl backdrop-blur-xl bg-white/10 border border-white/20"
                >
                  <div className="text-xs font-medium mb-2 text-white/70">
                    Suggestions based on "{inputValue}"
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {[
                      `${inputValue} with AI analysis`,
                      `${inputValue} using knowledge graphs`,
                      `${inputValue} for document processing`
                    ].map((suggestion, index) => (
                      <motion.button
                        key={suggestion}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="px-3 py-1.5 rounded-lg text-sm transition-all duration-150 text-white/80 hover:bg-white/10 hover:text-white"
                      >
                        {suggestion}
                      </motion.button>
                    ))}
            </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </section>

      {/* Services Section */}
      <section className="px-4 md:px-6 py-20 relative overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                Enterprise-Ready
              </span>
              <br />
              AI Solutions
            </h2>
            <p className={`text-lg md:text-xl max-w-3xl mx-auto ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              Complete suite of AI-powered services designed for modern businesses
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((service, index) => (
              <motion.div 
                key={service.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ scale: 1.05, y: -5 }}
                className={`p-8 rounded-xl ${isDarkMode ? 'bg-gray-800/50 border-gray-700' : 'bg-white border-gray-200'} border backdrop-blur-sm shadow-lg hover:shadow-xl transition-all duration-300`}
              >
                <div className={`w-12 h-12 rounded-lg ${isDarkMode ? 'bg-purple-500/20' : 'bg-purple-100'} flex items-center justify-center mb-6`}>
                  <span className="text-purple-600">{service.icon}</span>
                </div>
                <h3 className="text-xl font-semibold mb-4">{service.title}</h3>
                <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  {service.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Business Benefits Section */}
      <section className={`px-4 md:px-6 py-20 ${isDarkMode ? 'bg-gray-800/30' : 'bg-gray-50'}`}>
        <div className="max-w-7xl mx-auto">
              <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              Measurable Business Impact
            </h2>
            <p className={`text-lg md:text-xl max-w-3xl mx-auto ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              Real results from organizations using CogniVox
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {businessBenefits.map((benefit, index) => (
              <motion.div 
                key={benefit.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-2">
                  {benefit.metric}
                </div>
                <h3 className="text-lg font-semibold mb-2">{benefit.label}</h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  {benefit.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Stack Section */}
      <section className="px-4 md:px-6 py-20">
        <div className="max-w-7xl mx-auto">
              <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              Built on Modern Technology
            </h2>
            <p className={`text-lg md:text-xl max-w-3xl mx-auto ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              Leveraging the latest in AI, databases, and cloud technologies
            </p>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
            {techStack.map((tech, index) => (
              <motion.div
                key={tech.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.05 }}
                viewport={{ once: true }}
                whileHover={{ scale: 1.05, y: -2 }}
                className={`p-4 rounded-lg ${isDarkMode ? 'bg-gray-800/30 border-gray-700' : 'bg-white border-gray-200'} border text-center`}
              >
                <div className="font-semibold text-sm mb-1">{tech.name}</div>
                <div className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {tech.category}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 md:px-6 py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 via-blue-600/10 to-purple-600/10" />
        <div className="relative z-10 max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              Ready to Transform Your
              <br />
              <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                Knowledge Management?
              </span>
            </h2>
            <p className={`text-lg md:text-xl mb-8 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              Join thousands of organizations already using CogniVox to unlock the power of their data
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => handleAuth('signup')}
                className="group px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg font-semibold text-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Start Free Trial
                <FaArrowRight className="inline ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                className={`px-8 py-4 border-2 rounded-lg font-semibold text-lg transition-all duration-200 ${
                  isDarkMode 
                    ? 'border-gray-600 text-gray-200 hover:border-gray-500 hover:bg-gray-800' 
                    : 'border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50'
                }`}
              >
                Contact Sales
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className={`px-4 md:px-6 py-16 border-t ${isDarkMode ? 'bg-gray-900 border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            {/* Company Info */}
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                  <FaBrain className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                  CogniVox
                </h3>
              </div>
              <p className={`mb-4 max-w-md ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Transforming how organizations interact with their knowledge through intelligent AI and persistent memory.
              </p>
              <div className="flex space-x-4">
                <button className={`p-2 rounded-lg ${isDarkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-200'} transition-colors`}>
                  <FaTwitter className="w-5 h-5" />
                </button>
                <button className={`p-2 rounded-lg ${isDarkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-200'} transition-colors`}>
                  <FaLinkedin className="w-5 h-5" />
                </button>
                <button className={`p-2 rounded-lg ${isDarkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-200'} transition-colors`}>
                  <FaGithub className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Product Links */}
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <div className="space-y-2">
                <button className={`block text-sm ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'} transition-colors`}>
                  Features
                </button>
                <button className={`block text-sm ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'} transition-colors`}>
                  Pricing
                </button>
                <button className={`block text-sm ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'} transition-colors`}>
                  Documentation
                </button>
                <button className={`block text-sm ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'} transition-colors`}>
                  API Reference
                </button>
              </div>
            </div>

            {/* Company Links */}
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <div className="space-y-2">
                <button className={`block text-sm ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'} transition-colors`}>
                  About
                </button>
                <button className={`block text-sm ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'} transition-colors`}>
                  Careers
                </button>
                <button className={`block text-sm ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'} transition-colors`}>
                  Contact
                </button>
                <button className={`block text-sm ${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-600 hover:text-gray-900'} transition-colors`}>
                  Privacy
                </button>
              </div>
            </div>
          </div>

          <div className={`pt-8 border-t ${isDarkMode ? 'border-gray-800' : 'border-gray-200'} text-center`}>
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              © 2025 CogniVox. All rights reserved. Built with ❤️ for the future of AI.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage; 