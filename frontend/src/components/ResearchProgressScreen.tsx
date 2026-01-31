import { useEffect, useState } from 'react';
import { 
  FileText,
  Sparkles,
  List,
  BarChart3,
  Mic,
  CheckCircle,
  Headphones
} from 'lucide-react';

interface ResearchProgressScreenProps {
  topic: string;
  onComplete: () => void;
}

interface PipelineStep {
  id: string;
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  duration: number; // in milliseconds
}

const pipelineSteps: PipelineStep[] = [
  {
    id: 'scanning',
    title: 'Scanning the papers',
    icon: FileText,
    duration: 3000,
  },
  {
    id: 'summarizing',
    title: 'Summarizing the articles',
    icon: Sparkles,
    duration: 3000,
  },
  {
    id: 'collecting',
    title: 'Collecting the main points',
    icon: List,
    duration: 3000,
  },
  {
    id: 'structuring',
    title: 'Structuring the episode',
    icon: BarChart3,
    duration: 3000,
  },
  {
    id: 'preparing',
    title: 'Preparing the narration',
    icon: Mic,
    duration: 3000,
  },
  {
    id: 'checking',
    title: 'Checking for clarity',
    icon: CheckCircle,
    duration: 2500,
  },
  {
    id: 'finalizing',
    title: 'Finalizing your podcast',
    icon: Headphones,
    duration: 2500,
  },
];

export function ResearchProgressScreen({ topic, onComplete }: ResearchProgressScreenProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  const currentStep = pipelineSteps[currentStepIndex];
  const totalDuration = pipelineSteps.reduce((sum, step) => sum + step.duration, 0);

  useEffect(() => {
    let stepTimer: number;
    let progressInterval: number;
    let elapsedTime = 0;

    // Calculate elapsed time for all previous steps
    for (let i = 0; i < currentStepIndex; i++) {
      elapsedTime += pipelineSteps[i].duration;
    }

    // Move to next step after current step duration
    stepTimer = window.setTimeout(() => {
      if (currentStepIndex < pipelineSteps.length - 1) {
        setCurrentStepIndex((prev) => prev + 1);
      } else {
        // All steps complete
        setTimeout(() => {
          onComplete();
        }, 500);
      }
    }, currentStep.duration);

    // Smooth progress bar
    progressInterval = window.setInterval(() => {
      setProgress((prev) => {
        const increment = (100 / totalDuration) * 50; // Update every 50ms
        const newProgress = prev + increment;
        return Math.min(newProgress, 100);
      });
    }, 50);

    return () => {
      clearTimeout(stepTimer);
      clearInterval(progressInterval);
    };
  }, [currentStepIndex, currentStep.duration, totalDuration, onComplete]);

  const getAnimationClass = () => {
    switch (currentStep.id) {
      case 'scanning':
        return 'animate-scan';
      case 'summarizing':
        return 'animate-shrink-sparkle';
      case 'collecting':
        return 'animate-list-appear';
      case 'structuring':
        return 'animate-slide-segments';
      case 'preparing':
        return 'animate-waveform';
      case 'checking':
        return 'animate-check-pulse';
      case 'finalizing':
        return 'animate-headphone-pulse';
      default:
        return '';
    }
  };

  const Icon = currentStep.icon;

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-16">
      <style>{`
        @keyframes scan-line {
          0%, 100% { transform: translateY(-100%); opacity: 0; }
          10% { opacity: 1; }
          50% { transform: translateY(100%); opacity: 1; }
          60% { opacity: 0; }
        }
        
        @keyframes shrink-sparkle {
          0% { transform: scale(1.5); opacity: 0.5; }
          50% { transform: scale(1); opacity: 1; }
          100% { transform: scale(1) rotate(5deg); }
        }
        
        @keyframes sparkle-burst {
          0%, 100% { transform: scale(0) rotate(0deg); opacity: 0; }
          50% { transform: scale(1.3) rotate(180deg); opacity: 1; }
        }
        
        @keyframes list-item {
          0% { transform: translateX(-20px); opacity: 0; }
          100% { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes segment-slide {
          0% { transform: translateX(-30px); opacity: 0; }
          100% { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes waveform {
          0%, 100% { height: 40%; }
          50% { height: 100%; }
        }
        
        @keyframes check-pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.15); opacity: 0.8; }
        }
        
        @keyframes headphone-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.08); }
        }
        
        .animate-scan .scan-line {
          animation: scan-line 2s ease-in-out infinite;
        }
        
        .animate-shrink-sparkle .main-icon {
          animation: shrink-sparkle 1.5s ease-out forwards;
        }
        
        .animate-shrink-sparkle .sparkle {
          animation: sparkle-burst 1s ease-out infinite;
        }
        
        .animate-list-appear .list-item-1 {
          animation: list-item 0.4s ease-out forwards;
          animation-delay: 0.2s;
          opacity: 0;
        }
        
        .animate-list-appear .list-item-2 {
          animation: list-item 0.4s ease-out forwards;
          animation-delay: 0.6s;
          opacity: 0;
        }
        
        .animate-list-appear .list-item-3 {
          animation: list-item 0.4s ease-out forwards;
          animation-delay: 1s;
          opacity: 0;
        }
        
        .animate-slide-segments .segment {
          animation: segment-slide 0.6s ease-out forwards;
        }
        
        .animate-slide-segments .segment-1 {
          animation-delay: 0.1s;
          opacity: 0;
        }
        
        .animate-slide-segments .segment-2 {
          animation-delay: 0.3s;
          opacity: 0;
        }
        
        .animate-slide-segments .segment-3 {
          animation-delay: 0.5s;
          opacity: 0;
        }
        
        .animate-slide-segments .segment-4 {
          animation-delay: 0.7s;
          opacity: 0;
        }
        
        .animate-waveform .bar {
          animation: waveform 0.8s ease-in-out infinite;
        }
        
        .animate-waveform .bar-1 {
          animation-delay: 0s;
        }
        
        .animate-waveform .bar-2 {
          animation-delay: 0.1s;
        }
        
        .animate-waveform .bar-3 {
          animation-delay: 0.2s;
        }
        
        .animate-waveform .bar-4 {
          animation-delay: 0.3s;
        }
        
        .animate-waveform .bar-5 {
          animation-delay: 0.4s;
        }
        
        .animate-check-pulse .check-icon {
          animation: check-pulse 1.5s ease-in-out infinite;
        }
        
        .animate-headphone-pulse .main-icon {
          animation: headphone-pulse 2s ease-in-out infinite;
        }
      `}</style>

      <div className="w-full max-w-[640px] mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold mb-3 text-white">
            Crafting your podcast on "{topic}"…
          </h1>
          <p className="text-lg text-blue-200">
            We're doing the research so you can just listen.
          </p>
        </div>

        {/* Main Animated Card */}
        <div className="bg-white/5 backdrop-blur-xl rounded-2xl shadow-lg p-16 min-h-[400px] flex flex-col items-center justify-center transition-all duration-500" style={{ border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          {/* Animation Container */}
          <div className={`mb-8 relative ${getAnimationClass()}`}>
            {/* Scanning the papers */}
            {currentStep.id === 'scanning' && (
              <div className="relative w-48 h-48 flex items-center justify-center">
                {/* Stack of papers */}
                <div className="absolute w-32 h-40 rounded-lg transform -rotate-6 bg-white/5" style={{ border: '2px solid rgba(255, 255, 255, 0.1)' }} />
                <div className="absolute w-32 h-40 rounded-lg transform rotate-3 bg-white/10" style={{ border: '2px solid rgba(255, 255, 255, 0.2)' }} />
                <div className="absolute w-32 h-40 bg-white/10 backdrop-blur-sm rounded-lg flex items-center justify-center overflow-hidden" style={{ border: '2px solid #2188FF' }}>
                  <FileText className="w-16 h-16" style={{ color: '#2188FF' }} />
                  {/* Scanner line */}
                  <div className="scan-line absolute inset-x-0 h-1" style={{ backgroundColor: '#2188FF', boxShadow: '0 0 20px #2188FF' }} />
                </div>
              </div>
            )}

            {/* Summarizing the articles */}
            {currentStep.id === 'summarizing' && (
              <div className="relative w-48 h-48 flex items-center justify-center">
                <div className="main-icon relative">
                  <div className="w-24 h-28 bg-white/10 backdrop-blur-sm rounded-lg flex items-center justify-center" style={{ border: '2px solid #2188FF' }}>
                    <FileText className="w-12 h-12" style={{ color: '#2188FF' }} />
                  </div>
                </div>
                {/* Sparkles */}
                <Sparkles className="sparkle absolute top-4 right-4 w-8 h-8" style={{ color: '#F59E0B' }} />
                <Sparkles className="sparkle absolute bottom-8 left-2 w-6 h-6" style={{ color: '#F59E0B', animationDelay: '0.3s' }} />
                <Sparkles className="sparkle absolute top-12 left-0 w-5 h-5" style={{ color: '#F59E0B', animationDelay: '0.6s' }} />
              </div>
            )}

            {/* Collecting the main points */}
            {currentStep.id === 'collecting' && (
              <div className="w-64 space-y-3">
                <div className="list-item-1 flex items-center gap-3 p-3 rounded-lg bg-white/5 backdrop-blur-sm" style={{ border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#2188FF' }} />
                  <div className="h-2 rounded flex-1" style={{ backgroundColor: '#2188FF', opacity: 0.4 }} />
                </div>
                <div className="list-item-2 flex items-center gap-3 p-3 rounded-lg bg-white/5 backdrop-blur-sm" style={{ border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#2188FF' }} />
                  <div className="h-2 rounded flex-1" style={{ backgroundColor: '#2188FF', opacity: 0.4 }} />
                </div>
                <div className="list-item-3 flex items-center gap-3 p-3 rounded-lg bg-white/5 backdrop-blur-sm" style={{ border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#2188FF' }} />
                  <div className="h-2 rounded flex-1" style={{ backgroundColor: '#2188FF', opacity: 0.4 }} />
                </div>
              </div>
            )}

            {/* Structuring the episode */}
            {currentStep.id === 'structuring' && (
              <div className="w-64 flex items-center gap-2">
                <div className="segment segment-1 h-20 flex-1 rounded-lg bg-white/10 backdrop-blur-sm" />
                <div className="segment segment-2 h-16 flex-1 rounded-lg" style={{ backgroundColor: '#2188FF', opacity: 0.6 }} />
                <div className="segment segment-3 h-24 flex-1 rounded-lg" style={{ backgroundColor: '#2188FF', opacity: 0.8 }} />
                <div className="segment segment-4 h-14 flex-1 rounded-lg" style={{ backgroundColor: '#2188FF' }} />
              </div>
            )}

            {/* Preparing the narration */}
            {currentStep.id === 'preparing' && (
              <div className="flex items-end justify-center gap-2 h-32">
                <div className="bar bar-1 w-3 rounded-full" style={{ backgroundColor: '#2188FF', opacity: 0.6 }} />
                <div className="bar bar-2 w-3 rounded-full" style={{ backgroundColor: '#2188FF', opacity: 0.8 }} />
                <div className="bar bar-3 w-3 rounded-full" style={{ backgroundColor: '#2188FF' }} />
                <div className="bar bar-4 w-3 rounded-full" style={{ backgroundColor: '#2188FF', opacity: 0.8 }} />
                <div className="bar bar-5 w-3 rounded-full" style={{ backgroundColor: '#2188FF', opacity: 0.6 }} />
              </div>
            )}

            {/* Checking for clarity */}
            {currentStep.id === 'checking' && (
              <div className="relative w-48 h-48 flex items-center justify-center">
                <div className="w-32 h-32 rounded-full flex items-center justify-center bg-white/5 backdrop-blur-sm">
                  <Sparkles className="w-16 h-16" style={{ color: '#6366F1' }} />
                </div>
                <div className="check-icon absolute">
                  <CheckCircle className="w-20 h-20" style={{ color: '#16A34A' }} />
                </div>
              </div>
            )}

            {/* Finalizing your podcast */}
            {currentStep.id === 'finalizing' && (
              <div className="main-icon">
                <div className="w-40 h-40 rounded-full flex items-center justify-center shadow-xl" style={{ background: 'linear-gradient(135deg, #2188FF 0%, #6366F1 100%)' }}>
                  <Headphones className="w-20 h-20 text-white" />
                </div>
              </div>
            )}
          </div>

          {/* Step Title */}
          <h2 className="text-2xl font-semibold text-center text-white">
            {currentStep.title}
          </h2>
        </div>

        {/* Progress Bar */}
        <div className="mt-8 space-y-2">
          <div className="h-2 rounded-full overflow-hidden bg-white/10">
            <div
              className="h-full rounded-full transition-all duration-300 ease-out"
              style={{ 
                width: `${progress}%`,
                background: 'linear-gradient(to right, #2188FF, #0560D4)'
              }}
            />
          </div>
          <p className="text-sm text-center text-blue-200">
            This usually takes under a minute.
          </p>
        </div>
      </div>
    </div>
  );
}