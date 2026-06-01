import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useTheme } from "../../contexts/ThemeContext";

interface SkeletonLoaderProps {
  variant?: "message" | "simple";
}

const THINKING_MESSAGES = [
  "Thinking...",
  "Processing your request...",
  "Wait a moment...",
  "Analyzing context...",
  "Gathering information...",
  "Formulating response...",
  "Almost there...",
];

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  variant = "message",
}) => {
  const { isDarkMode } = useTheme();
  const [thinkingMessage, setThinkingMessage] = useState(THINKING_MESSAGES[0]);

  // Rotate through thinking messages
  useEffect(() => {
    const interval = setInterval(() => {
      setThinkingMessage((prev) => {
        const currentIndex = THINKING_MESSAGES.indexOf(prev);
        const nextIndex = (currentIndex + 1) % THINKING_MESSAGES.length;
        return THINKING_MESSAGES[nextIndex];
      });
    }, 2000); // Change message every 2 seconds

    return () => clearInterval(interval);
  }, []);

  const shimmerVariants = {
    initial: { x: "-100%" },
    animate: { x: "100%" },
  };

  const shimmerTransition = {
    duration: 1,
    repeat: Infinity,
    ease: "easeInOut" as const,
  };

  const SkeletonLine = ({
    width = "100%",
    height = "12px",
    className = "",
  }) => (
    <div
      className={`relative overflow-hidden rounded ${className} ${
        isDarkMode ? "bg-gray-800/30" : "bg-gray-200/50"
      }`}
      style={{ width, height }}
    >
      <motion.div
        className={`absolute inset-0 ${
          isDarkMode
            ? "bg-gradient-to-r from-transparent via-gray-700/30 to-transparent"
            : "bg-gradient-to-r from-transparent via-white/60 to-transparent"
        }`}
        variants={shimmerVariants}
        initial="initial"
        animate="animate"
        transition={shimmerTransition}
      />
    </div>
  );

  const SkeletonPulse = ({
    children,
    delay = 0,
  }: {
    children: React.ReactNode;
    delay?: number;
  }) => (
    <motion.div
      initial={{ opacity: 0.6 }}
      animate={{ opacity: [0.6, 1, 0.6] }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        delay,
        ease: "easeInOut",
      }}
    >
      {children}
    </motion.div>
  );

  const MessageSkeleton = () => (
    <div className="space-y-3">
      {/* Thinking message with animated dots */}
      <motion.div
        className={`flex items-center gap-2 ${
          isDarkMode ? "text-purple-400" : "text-purple-600"
        }`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <motion.span
          className="text-sm font-medium"
          key={thinkingMessage}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 5 }}
          transition={{ duration: 0.3 }}
        >
          {thinkingMessage}
        </motion.span>
        <div className="flex gap-1">
          <motion.div
            className={`w-1 h-1 rounded-full ${
              isDarkMode ? "bg-purple-400" : "bg-purple-600"
            }`}
            animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0 }}
          />
          <motion.div
            className={`w-1 h-1 rounded-full ${
              isDarkMode ? "bg-purple-400" : "bg-purple-600"
            }`}
            animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
          />
          <motion.div
            className={`w-1 h-1 rounded-full ${
              isDarkMode ? "bg-purple-400" : "bg-purple-600"
            }`}
            animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
          />
        </div>
      </motion.div>

      {/* Content lines */}
      <div className="space-y-1.5">
        <SkeletonPulse delay={0}>
          <SkeletonLine width="88%" height="12px" />
        </SkeletonPulse>
        <SkeletonPulse delay={0.1}>
          <SkeletonLine width="82%" height="12px" />
        </SkeletonPulse>
        <SkeletonPulse delay={0.2}>
          <SkeletonLine width="75%" height="12px" />
        </SkeletonPulse>
        <SkeletonPulse delay={0.3}>
          <SkeletonLine width="68%" height="12px" />
        </SkeletonPulse>
      </div>
    </div>
  );

  const SimpleSkeleton = () => (
    <div className="space-y-2">
      <SkeletonPulse delay={0}>
        <SkeletonLine width="90%" height="14px" />
      </SkeletonPulse>
      <SkeletonPulse delay={0.3}>
        <SkeletonLine width="85%" height="14px" />
      </SkeletonPulse>
      <SkeletonPulse delay={0.6}>
        <SkeletonLine width="80%" height="14px" />
      </SkeletonPulse>
    </div>
  );

  const renderSkeleton = () => {
    switch (variant) {
      case "simple":
        return <SimpleSkeleton />;
      default:
        return <MessageSkeleton />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      className="w-full"
    >
      {renderSkeleton()}
    </motion.div>
  );
};

export default SkeletonLoader;
