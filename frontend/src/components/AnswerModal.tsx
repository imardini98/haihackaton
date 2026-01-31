import React, { useState, useEffect } from 'react';
import { Play, Pause } from 'lucide-react';

interface AnswerModalProps {
  question: string;
  onResume: () => void;
}

export function AnswerModal({ question, onResume }: AnswerModalProps) {
  const [isPlayingAnswer, setIsPlayingAnswer] = useState(false);
  const [answerProgress, setAnswerProgress] = useState(0);

  const answerDuration = 30; // 30 seconds

  useEffect(() => {
    let interval: number | null = null;
    
    if (isPlayingAnswer) {
      interval = window.setInterval(() => {
        setAnswerProgress((prev) => {
          const newProgress = prev + (100 / answerDuration);
          if (newProgress >= 100) {
            setIsPlayingAnswer(false);
            return 100;
          }
          return newProgress;
        });
      }, 1000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isPlayingAnswer, answerDuration]);

  const handlePlayPause = () => {
    setIsPlayingAnswer(!isPlayingAnswer);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center px-6 z-50 animate-in fade-in duration-200">
      <div className="bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 rounded-3xl shadow-2xl w-full max-w-[520px] p-8 border border-blue-800/50 animate-in zoom-in-95 duration-200">
        <div className="mb-6">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Your question:</p>
          <p className="text-base text-gray-300 italic">"{question}"</p>
        </div>

        <h3 className="text-xl font-semibold text-white mb-6">
          Quick explanation:
        </h3>
        
        {/* Mini Audio Player */}
        <div className="bg-blue-900/30 border border-blue-700/50 rounded-2xl p-6 mb-8">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={handlePlayPause}
              className="p-3 bg-white hover:scale-105 rounded-full transition-transform flex-shrink-0"
              aria-label={isPlayingAnswer ? 'Pause answer' : 'Play answer'}
            >
              {isPlayingAnswer ? (
                <Pause className="w-5 h-5 text-black fill-black" />
              ) : (
                <Play className="w-5 h-5 text-black fill-black ml-0.5" />
              )}
            </button>

            <div className="flex-1">
              <div className="h-1 bg-blue-800/50 rounded-full">
                <div
                  className="h-full bg-white rounded-full transition-all duration-300"
                  style={{ width: `${answerProgress}%` }}
                />
              </div>
            </div>

            <span className="text-sm text-gray-400 flex-shrink-0">0:{answerDuration}</span>
          </div>

          <p className="text-sm text-gray-400">
            A personalized answer to help clarify this topic
          </p>
        </div>
        
        <button
          onClick={onResume}
          className="w-full text-white py-4 px-6 rounded-full font-bold transition-all hover:scale-105"
          style={{ backgroundColor: '#F59E0B' }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#D97706'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#F59E0B'}
        >
          Resume Podcast
        </button>
      </div>
    </div>
  );
}