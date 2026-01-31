import React, { useEffect, useState } from 'react';
import handIcon from '../assets/bdf35d6b24794cdeb24a98a3abd20c56685812d5.png';

interface HandRaiseAnimationProps {
  onComplete: () => void;
}

export function HandRaiseAnimation({ onComplete }: HandRaiseAnimationProps) {
  const [dots, setDots] = useState('');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Animate dots
    const dotsInterval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);

    // Animate progress from 0 to 100 over 2.5 seconds
    const duration = 2500;
    const intervalTime = 20;
    const increment = (100 / duration) * intervalTime;
    
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + increment;
        if (newProgress >= 100) {
          return 100;
        }
        return newProgress;
      });
    }, intervalTime);

    // Complete animation after 2.5 seconds
    const timer = setTimeout(() => {
      onComplete();
    }, duration);

    return () => {
      clearInterval(dotsInterval);
      clearInterval(progressInterval);
      clearTimeout(timer);
    };
  }, [onComplete]);

  // Calculate the circle SVG dash properties for fill animation
  const radius = 120;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="fixed inset-0 bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 flex flex-col items-center justify-center z-50 px-6">
      <div className="w-full max-w-[480px] mx-auto flex flex-col items-center">
        {/* Top Section - Status Text */}
        <div className="mb-16 text-center">
          <h2 className="text-2xl font-semibold text-white mb-3">
            Raising your hand
          </h2>
          <p className="text-lg text-blue-200">
            Get ready to ask your question
          </p>
        </div>

        {/* Circular Fill Animation */}
        <div className="relative flex items-center justify-center">
          {/* Background Circle */}
          <svg className="absolute" width="280" height="280">
            <circle
              cx="140"
              cy="140"
              r={radius}
              stroke="rgba(245, 158, 11, 0.1)"
              strokeWidth="8"
              fill="none"
            />
          </svg>
          
          {/* Animated Fill Circle */}
          <svg className="absolute -rotate-90" width="280" height="280">
            <circle
              cx="140"
              cy="140"
              r={radius}
              strokeWidth="8"
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              className="transition-all duration-75 ease-linear"
              style={{
                stroke: '#F59E0B',
                filter: 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.5))'
              }}
            />
          </svg>

          {/* Center Content with Bounce */}
          <div className="relative z-10">
            <div className="w-32 h-32 rounded-full flex items-center justify-center shadow-2xl animate-bounce" style={{ backgroundColor: '#F59E0B', boxShadow: '0 25px 50px -12px rgba(245, 158, 11, 0.5)' }}>
              <img src={handIcon} alt="Hand" className="w-16 h-16 text-white" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}