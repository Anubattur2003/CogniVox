import React from 'react';
import { motion } from 'framer-motion';

interface AnimatedAvatarProps {
  name?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  gradientColors?: [string, string];
}

const AnimatedAvatar: React.FC<AnimatedAvatarProps> = ({ 
  name = 'User', 
  size = 'md', 
  className = '',
  gradientColors 
}) => {
  // Get first character of first name, fallback to 'U' for User
  const initial = name?.charAt(0)?.toUpperCase() || 'U';
  
  // Size configurations
  const sizeClasses = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
    xl: 'w-16 h-16 text-xl'
  };

  // Generate consistent gradient colors based on the initial
  const getGradientColors = (): [string, string] => {
    if (gradientColors) return gradientColors;
    
    const colorPairs: Record<string, [string, string]> = {
      'A': ['#FF6B6B', '#4ECDC4'],
      'B': ['#45B7D1', '#96CEB4'],
      'C': ['#FECA57', '#FF9FF3'],
      'D': ['#48CAE4', '#F72585'],
      'E': ['#06FFA5', '#3D5AFE'],
      'F': ['#FFD93D', '#6BCF7F'],
      'G': ['#A8E6CF', '#FF8B94'],
      'H': ['#B4A7D6', '#D4A5A5'],
      'I': ['#95E1D3', '#F3D250'],
      'J': ['#C7CEEA', '#FFB6C1'],
      'K': ['#FFDAB9', '#E6E6FA'],
      'L': ['#87CEEB', '#DDA0DD'],
      'M': ['#F0E68C', '#98FB98'],
      'N': ['#FFB347', '#77DD77'],
      'O': ['#AEC6CF', '#FFCCCB'],
      'P': ['#CFCFC4', '#F49AC2'],
      'Q': ['#FDFD96', '#C1E1C1'],
      'R': ['#FFA07A', '#20B2AA'],
      'S': ['#DEB887', '#5F9EA0'],
      'T': ['#F5DEB3', '#48D1CC'],
      'U': ['#E0E0E0', '#9370DB'],
      'V': ['#FFFACD', '#32CD32'],
      'W': ['#F0F8FF', '#FF69B4'],
      'X': ['#FAEBD7', '#8A2BE2'],
      'Y': ['#F5F5DC', '#FF1493'],
      'Z': ['#FFE4E1', '#00CED1']
    };

    return colorPairs[initial] || ['#667eea', '#764ba2'];
  };

  const [color1, color2] = getGradientColors();

  return (
    <motion.div
      initial={{ scale: 0, rotate: -180 }}
      animate={{ scale: 1, rotate: 0 }}
      whileHover={{ 
        scale: 1.1,
        rotate: [0, -10, 10, 0],
        transition: { 
          duration: 0.3,
          rotate: { duration: 0.5, ease: "easeInOut" }
        }
      }}
      whileTap={{ scale: 0.9 }}
      className={`
        ${sizeClasses[size]} 
        rounded-full 
        flex 
        items-center 
        justify-center 
        font-bold 
        text-white 
        shadow-lg 
        cursor-pointer 
        relative 
        overflow-hidden
        ${className}
      `}
      style={{
        background: `linear-gradient(135deg, ${color1}, ${color2})`,
      }}
    >
      {/* Animated background particles */}
      <motion.div
        className="absolute inset-0 opacity-30"
        animate={{
          background: [
            `radial-gradient(circle at 20% 80%, rgba(255,255,255,0.2) 0%, transparent 70%)`,
            `radial-gradient(circle at 80% 20%, rgba(255,255,255,0.2) 0%, transparent 70%)`,
            `radial-gradient(circle at 40% 40%, rgba(255,255,255,0.2) 0%, transparent 70%)`
          ]
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "easeInOut"
        }}
      />
      
      {/* Shimmer effect */}
      <motion.div
        className="absolute inset-0 opacity-0"
        whileHover={{
          opacity: [0, 0.3, 0],
          background: `linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.5) 50%, transparent 70%)`
        }}
        transition={{ duration: 0.6, ease: "easeInOut" }}
      />
      
      {/* Character */}
      <motion.span
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.3 }}
        className="relative z-10 select-none"
      >
        {initial}
      </motion.span>
      
      {/* Floating ring effect */}
      <motion.div
        className="absolute inset-0 rounded-full border-2 border-white opacity-0"
        whileHover={{
          opacity: [0, 0.6, 0],
          scale: [1, 1.2, 1.4],
        }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </motion.div>
  );
};

export default AnimatedAvatar; 