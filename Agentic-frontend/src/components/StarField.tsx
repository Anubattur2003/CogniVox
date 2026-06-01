import React, { useMemo } from 'react';

interface StarFieldProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  starCount?: number;
  speed?: number;
}

const StarField: React.FC<StarFieldProps> = ({
  className = '',
  width = '100%',
  height = '100%',
  starCount = 150,
  speed = 0.5
}) => {
  // Generate random stars
  const stars = useMemo(() => {
    return Array.from({ length: starCount }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      opacity: Math.random() * 0.8 + 0.2,
      twinkleDelay: Math.random() * 4,
    }));
  }, [starCount]);

  return (
    <div 
      className={`absolute inset-0 overflow-hidden ${className}`}
      style={{ width, height }}
    >
      <div className="relative w-full h-full">
        {stars.map((star) => (
          <div
            key={star.id}
            className="absolute bg-white rounded-full animate-pulse"
            style={{
              left: `${star.x}%`,
              top: `${star.y}%`,
              width: `${star.size}px`,
              height: `${star.size}px`,
              opacity: star.opacity,
              animationDelay: `${star.twinkleDelay}s`,
              animationDuration: '2s',
            }}
          />
        ))}
        
        {/* Additional animated shooting stars */}
        <div className="absolute inset-0">
          {Array.from({ length: 3 }, (_, i) => (
            <div
              key={`shooting-${i}`}
              className="absolute w-1 h-1 bg-white rounded-full animate-shooting-star"
              style={{
                left: '0%',
                top: `${20 + i * 30}%`,
                animationDuration: `${8 + i * 2}s`,
                animationDelay: `${i * 3}s`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default StarField; 