import { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Hand, Shuffle, Repeat, ArrowLeft, MoreVertical } from 'lucide-react';
import { QuestionModal } from './QuestionModal';
import { AnswerModal } from './AnswerModal';
import { HandRaiseAnimation } from './HandRaiseAnimation';

interface PlayerScreenProps {
  topic: string;
  onBackToLanding: () => void;
}

export function PlayerScreen({ topic, onBackToLanding }: PlayerScreenProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [showHandAnimation, setShowHandAnimation] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [showAnswerModal, setShowAnswerModal] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const intervalRef = useRef<number | null>(null);

  const totalDuration = 240; // 4 minutes in seconds

  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = window.setInterval(() => {
        setCurrentTime((prev) => {
          const newTime = prev + 1;
          if (newTime >= totalDuration) {
            setIsPlaying(false);
            return totalDuration;
          }
          return newTime;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, totalDuration]);

  useEffect(() => {
    setProgress((currentTime / totalDuration) * 100);
  }, [currentTime, totalDuration]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSkipBack = () => {
    setCurrentTime((prev) => Math.max(0, prev - 15));
  };

  const handleSkipForward = () => {
    setCurrentTime((prev) => Math.min(totalDuration, prev + 15));
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickPosition = (e.clientX - rect.left) / rect.width;
    const newTime = Math.floor(clickPosition * totalDuration);
    setCurrentTime(newTime);
  };

  const handleRaiseHand = () => {
    setIsPlaying(false);
    setShowHandAnimation(true);
  };

  const handleAnimationComplete = () => {
    setShowHandAnimation(false);
    setShowQuestionModal(true);
  };

  const handleAskQuestion = (question: string) => {
    setCurrentQuestion(question);
    setShowQuestionModal(false);
    setShowAnswerModal(true);
  };

  const handleResumeFromQuestion = () => {
    setShowQuestionModal(false);
    setIsPlaying(true);
  };

  const handleResumeFromAnswer = () => {
    setShowAnswerModal(false);
    setIsPlaying(true);
  };

  return (
    <>
      <div className="min-h-screen bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 flex items-center justify-center px-6 py-8 relative">
        <div className="w-full max-w-[480px] mx-auto">
          {/* Album Art with overlaid buttons */}
          <div className="mb-8 relative">
            <div className="aspect-[3/4] w-full max-w-[400px] mx-auto bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900 rounded-xl shadow-2xl flex items-center justify-center border border-blue-500/20">
              <div className="text-white text-center p-8">
                <div className="text-5xl font-bold mb-3">PodAsk</div>
                <div className="text-lg opacity-90">Science Explained</div>
              </div>
            </div>
            
            {/* Back Button - Top Left over album art */}
            <button
              onClick={onBackToLanding}
              className="absolute top-4 left-4 p-3 rounded-full bg-black/30 hover:bg-black/50 backdrop-blur-sm transition-all group"
              aria-label="Back to home"
            >
              <ArrowLeft className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
            </button>

            {/* More Options Button - Top Right over album art */}
            <button
              className="absolute top-4 right-4 p-3 rounded-full bg-black/30 hover:bg-black/50 backdrop-blur-sm transition-all group"
              aria-label="More options"
            >
              <MoreVertical className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
            </button>
          </div>

          {/* Episode Info */}
          <div className="text-center mb-8 px-4">
            <h2 className="text-2xl font-semibold text-white mb-2">
              {topic}
            </h2>
            <p className="text-sm text-gray-400">
              PodAsk • Science Explained
            </p>
          </div>

          {/* Progress Bar */}
          <div className="mb-6 px-4">
            <div 
              onClick={handleProgressClick}
              className="h-1 bg-gray-600 rounded-full cursor-pointer mb-2 group"
            >
              <div
                className="h-full bg-white rounded-full transition-all duration-300 relative"
                style={{ width: `${progress}%` }}
              >
                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
            <div className="flex justify-between text-xs text-gray-400">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(totalDuration)}</span>
            </div>
          </div>

          {/* Playback Controls */}
          <div className="flex items-center justify-center gap-4 mb-20 px-4">
            <button
              className="p-2 hover:opacity-70 transition-opacity"
              aria-label="Shuffle"
            >
              <Shuffle className="w-5 h-5 text-gray-400" />
            </button>

            <button
              onClick={handleSkipBack}
              className="p-2 hover:opacity-70 transition-opacity"
              aria-label="Previous track"
            >
              <SkipBack className="w-7 h-7 text-white fill-white" />
            </button>

            <button
              onClick={handlePlayPause}
              className="p-4 bg-white hover:scale-105 rounded-full transition-transform"
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <Pause className="w-7 h-7 text-black fill-black" />
              ) : (
                <Play className="w-7 h-7 text-black fill-black ml-1" />
              )}
            </button>

            <button
              onClick={handleSkipForward}
              className="p-2 hover:opacity-70 transition-opacity"
              aria-label="Next track"
            >
              <SkipForward className="w-7 h-7 text-white fill-white" />
            </button>

            <button
              className="p-2 hover:opacity-70 transition-opacity"
              aria-label="Repeat"
            >
              <Repeat className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Raise Hand Button */}
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-full max-w-[480px] px-6">
            <button
              onClick={handleRaiseHand}
              className="w-full text-white py-4 px-6 rounded-full font-bold text-base shadow-lg transition-all hover:scale-105 flex items-center justify-center gap-2"
              style={{ backgroundColor: '#F59E0B' }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#D97706'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#F59E0B'}
            >
              <Hand className="w-5 h-5" />
              Raise Hand
            </button>
            <p className="text-center text-xs text-gray-400 mt-2">
              Ask questions anytime while listening
            </p>
          </div>
        </div>
      </div>

      {/* Hand Raise Animation */}
      {showHandAnimation && (
        <HandRaiseAnimation onComplete={handleAnimationComplete} />
      )}

      {/* Modals */}
      {showQuestionModal && (
        <QuestionModal
          onAsk={handleAskQuestion}
          onCancel={handleResumeFromQuestion}
          autoStartRecording={true}
        />
      )}
      {showAnswerModal && (
        <AnswerModal
          question={currentQuestion}
          onResume={handleResumeFromAnswer}
        />
      )}
    </>
  );
}