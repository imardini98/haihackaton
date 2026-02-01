import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  FileText,
  Sparkles,
  List,
  BarChart3,
  Mic,
  CheckCircle,
  Headphones,
  AlertCircle
} from 'lucide-react';
import { searchPapers, ingestPaper, type PaperSummary, type Paper } from '../api/papers';
import { generatePodcast, pollPodcastStatus, type Podcast } from '../api/podcasts';
import { ApiError } from '../api/http';

interface ResearchProgressScreenProps {
  topic: string;
  token: string;
  onComplete: (podcastId: string) => void;
  onError?: (error: string) => void;
}

interface PipelineStep {
  id: string;
  title: string;
  icon: React.ComponentType<{ className?: string }>;
}

const pipelineSteps: PipelineStep[] = [
  {
    id: 'scanning',
    title: 'Searching for papers',
    icon: FileText,
  },
  {
    id: 'summarizing',
    title: 'Analyzing relevance',
    icon: Sparkles,
  },
  {
    id: 'collecting',
    title: 'Ingesting papers',
    icon: List,
  },
  {
    id: 'structuring',
    title: 'Structuring the episode',
    icon: BarChart3,
  },
  {
    id: 'preparing',
    title: 'Generating audio',
    icon: Mic,
  },
  {
    id: 'checking',
    title: 'Checking for clarity',
    icon: CheckCircle,
  },
  {
    id: 'finalizing',
    title: 'Finalizing your podcast',
    icon: Headphones,
  },
];

export function ResearchProgressScreen({ topic, token, onComplete, onError }: ResearchProgressScreenProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const abortRef = useRef(false);
  const hasStartedRef = useRef(false);

  const currentStep = pipelineSteps[currentStepIndex];

  const setStep = useCallback((index: number, progressValue?: number) => {
    setCurrentStepIndex(index);
    if (progressValue !== undefined) {
      setProgress(progressValue);
    }
  }, []);

  useEffect(() => {
    if (hasStartedRef.current) return;
    hasStartedRef.current = true;

    const runPipeline = async () => {
      try {
        // Step 0: Searching for papers
        setStep(0, 5);
        setStatusMessage('Querying ArXiv...');

        const searchResult = await searchPapers(topic, {
          maxResults: 20,
          topN: 5,
          maxPdfPages: 50,
        });

        if (abortRef.current) return;

        const topPapers = searchResult.top_papers;
        if (!topPapers || topPapers.length === 0) {
          throw new Error('No relevant papers found for this topic. Try a different search query.');
        }

        setStatusMessage(`Found ${searchResult.total_papers_found} papers, selected top ${topPapers.length}`);
        setStep(1, 15);

        // Step 1: Analyzing relevance (brief pause to show the step)
        await new Promise(resolve => setTimeout(resolve, 1000));
        if (abortRef.current) return;

        // Step 2: Ingesting papers
        setStep(2, 25);
        const ingestedPapers: Paper[] = [];

        for (let i = 0; i < topPapers.length; i++) {
          if (abortRef.current) return;

          const paper = topPapers[i];
          setStatusMessage(`Ingesting paper ${i + 1}/${topPapers.length}: ${paper.title.slice(0, 50)}...`);

          try {
            const ingested = await ingestPaper(paper.arxiv_id, token);
            ingestedPapers.push(ingested);
          } catch (err) {
            // Paper might already be ingested, continue with next
            console.warn(`Failed to ingest paper ${paper.arxiv_id}:`, err);
          }

          setProgress(25 + ((i + 1) / topPapers.length) * 15);
        }

        if (abortRef.current) return;

        if (ingestedPapers.length === 0) {
          throw new Error('Failed to ingest any papers. Please try again.');
        }

        setStatusMessage(`Ingested ${ingestedPapers.length} papers`);

        // Step 3: Structuring the episode (start podcast generation)
        setStep(3, 45);
        setStatusMessage('Starting podcast generation...');

        const paperIds = ingestedPapers.map(p => p.id);
        const podcast = await generatePodcast(paperIds, topic, token);

        if (abortRef.current) return;

        setStatusMessage(`Podcast created, generating content...`);

        // Step 4-6: Poll for podcast status
        setStep(4, 55);

        await pollPodcastStatus(podcast.id, token, {
          intervalMs: 3000,
          maxAttempts: 100,
          onStatusChange: (status) => {
            if (abortRef.current) return;

            switch (status.status) {
              case 'pending':
                setStep(4, 55);
                setStatusMessage('Queued for generation...');
                break;
              case 'generating':
                // Progress through steps 4-6 based on time
                const currentProgress = progress;
                if (currentProgress < 70) {
                  setStep(4, Math.min(currentProgress + 5, 70));
                  setStatusMessage('Generating audio narration...');
                } else if (currentProgress < 85) {
                  setStep(5, Math.min(currentProgress + 5, 85));
                  setStatusMessage('Checking quality...');
                } else {
                  setStep(6, Math.min(currentProgress + 3, 95));
                  setStatusMessage('Almost ready...');
                }
                break;
              case 'ready':
                setStep(6, 100);
                setStatusMessage('Podcast ready!');
                break;
              case 'failed':
                throw new Error(status.error_message || 'Podcast generation failed');
            }
          },
        });

        if (abortRef.current) return;

        // Complete
        setProgress(100);
        setStatusMessage('Your podcast is ready!');

        setTimeout(() => {
          if (!abortRef.current) {
            onComplete(podcast.id);
          }
        }, 500);

      } catch (err) {
        if (abortRef.current) return;

        let message = 'An unexpected error occurred';
        if (err instanceof ApiError) {
          message = err.message;
        } else if (err instanceof Error) {
          message = err.message;
        }

        setError(message);
        if (onError) {
          onError(message);
        }
      }
    };

    runPipeline();

    return () => {
      abortRef.current = true;
    };
  }, [topic, token, onComplete, onError, setStep]);

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
            {error ? 'Something went wrong' : currentStep.title}
          </h2>

          {/* Status Message */}
          {statusMessage && !error && (
            <p className="text-sm text-blue-200 mt-3 text-center">
              {statusMessage}
            </p>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-8 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-white text-sm">{error}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="mt-3 text-sm text-blue-300 hover:text-blue-200 underline"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {!error && (
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
              This may take a few minutes while we generate your podcast.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}