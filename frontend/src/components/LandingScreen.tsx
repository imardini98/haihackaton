import React, { useState } from 'react';
import logo from '../assets/433dc299e6c56f79156becafd6df63c758f567fc.png';

interface LandingScreenProps {
  onGeneratePodcast: (topic: string) => void;
}

export function LandingScreen({ onGeneratePodcast }: LandingScreenProps) {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onGeneratePodcast(inputValue);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 md:py-16">
      <div className="w-full max-w-[640px] mx-auto text-center">
        {/* Logo */}
        <div className="flex justify-center mb-8 md:mb-10">
          <img 
            src={logo} 
            alt="PodAsk Logo" 
            className="h-20 md:h-24 w-auto object-contain"
          />
        </div>

        {/* Headline & Subline */}
        <div className="mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-semibold leading-tight text-white">
            Don't just listen. Ask the science.
          </h2>
          <p className="text-xl max-w-[540px] mx-auto text-blue-200">
            Get personalized podcast episodes that explain complex topics, with the ability to ask questions as you listen.
          </p>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="What do you want to understand?"
              className="w-full px-6 py-5 text-lg rounded-xl focus:outline-none transition-colors bg-white/10 backdrop-blur-sm text-white placeholder:text-blue-300"
              style={{ 
                border: '2px solid rgba(255, 255, 255, 0.2)'
              }}
              onFocus={(e) => e.target.style.borderColor = '#2188FF'}
              onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.2)'}
            />
          </div>
          
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="w-full py-5 px-8 rounded-xl text-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-white"
            style={{ 
              backgroundColor: inputValue.trim() ? '#2188FF' : '#2188FF'
            }}
            onMouseEnter={(e) => {
              if (inputValue.trim()) {
                e.currentTarget.style.backgroundColor = '#0560D4';
              }
            }}
            onMouseLeave={(e) => {
              if (inputValue.trim()) {
                e.currentTarget.style.backgroundColor = '#2188FF';
              }
            }}
          >
            Generate Podcast
          </button>
        </form>
      </div>
    </div>
  );
}