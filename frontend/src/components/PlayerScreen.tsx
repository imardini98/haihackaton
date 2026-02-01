import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Hand, Shuffle, Repeat, ArrowLeft, MoreVertical, Loader2 } from 'lucide-react';
import { QuestionModal } from './QuestionModal';
import { AnswerModal } from './AnswerModal';
import { HandRaiseAnimation } from './HandRaiseAnimation';
import { getPodcast, type Podcast } from '../api/podcasts';
import {
  startSession,
  updateSession,
  askTextQuestion,
  askVoiceQuestion,
  continueSession,
  type AskResponse,
  type ProcessVoiceResponse
} from '../api/interaction';
import { getApiBaseUrl } from '../api/http';

interface PlayerScreenProps {
  topic: string;
  podcastId?: string | null;
  token?: string;
  onBackToLanding: () => void;
}

// Audio buffer for seamless playback
interface AudioBuffer {
  audio: HTMLAudioElement;
  segmentIndex: number;
  blobUrl: string | null;
  isLoaded: boolean;
}

// Ref to hold the onSegmentEnd callback (avoids stale closure issues)
let onSegmentEndCallback: ((segmentIndex: number) => void) | null = null;

export function PlayerScreen({ topic, podcastId, token, onBackToLanding }: PlayerScreenProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [showHandAnimation, setShowHandAnimation] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [showAnswerModal, setShowAnswerModal] = useState(false);

  // Podcast state
  const [podcast, setPodcast] = useState<Podcast | null>(null);
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAudioReady, setIsAudioReady] = useState(false);

  // Session state (for Q&A)
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSubmittingQuestion, setIsSubmittingQuestion] = useState(false);
  const [currentAnswer, setCurrentAnswer] = useState<AskResponse | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [isLoadingResume, setIsLoadingResume] = useState(false);

  // Dual audio buffer refs for seamless playback
  const currentAudioRef = useRef<AudioBuffer | null>(null);
  const nextAudioRef = useRef<AudioBuffer | null>(null);
  const segmentStartTimeRef = useRef(0);
  const preloadedSegmentsRef = useRef<Map<number, string>>(new Map());

  // Track actual audio durations (from loaded audio files)
  const actualDurationsRef = useRef<Map<number, number>>(new Map());
  const [durationsLoaded, setDurationsLoaded] = useState(0);

  // Resume audio ref
  const resumeAudioRef = useRef<HTMLAudioElement | null>(null);

  // Get actual duration for a segment (prefer actual, fallback to API, then 60s)
  const getSegmentDuration = useCallback((segmentIndex: number): number => {
    const actual = actualDurationsRef.current.get(segmentIndex);
    if (actual && actual > 0) return actual;
    return podcast?.segments?.[segmentIndex]?.duration_seconds || 60;
  }, [podcast?.segments]);

  // Calculate total duration using actual durations when available
  const totalDuration = React.useMemo(() => {
    if (!podcast?.segments?.length) return 240;
    return podcast.segments.reduce((sum, _, idx) => sum + getSegmentDuration(idx), 0);
  }, [podcast?.segments, getSegmentDuration, durationsLoaded]);

  // Load podcast data
  useEffect(() => {
    if (!podcastId || !token) return;

    const loadPodcast = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await getPodcast(podcastId, token);
        setPodcast(data);

        // Sort segments by sequence
        if (data.segments) {
          data.segments.sort((a, b) => a.sequence - b.sequence);
        }
      } catch (err) {
        console.error('Failed to load podcast:', err);
        setError(err instanceof Error ? err.message : 'Failed to load podcast');
      } finally {
        setIsLoading(false);
      }
    };

    loadPodcast();
  }, [podcastId, token]);

  // Start listening session when podcast loads
  useEffect(() => {
    if (!podcast?.segments?.length || !podcastId || !token || sessionId) return;

    const initSession = async () => {
      try {
        const firstSegment = podcast.segments[0];
        const session = await startSession(podcastId, firstSegment.id, token);
        setSessionId(session.session_id);
      } catch (err) {
        console.error('Failed to start session:', err);
        // Non-fatal - Q&A won't work but playback continues
      }
    };

    initSession();
  }, [podcast?.segments, podcastId, token, sessionId]);

  // Update session when segment changes
  useEffect(() => {
    if (!sessionId || !token || !podcast?.segments) return;

    const currentSeg = podcast.segments[currentSegmentIndex];
    if (!currentSeg) return;

    updateSession(sessionId, currentSeg.id, token).catch(console.error);
  }, [sessionId, currentSegmentIndex, token, podcast?.segments]);

  // Get current segment
  const currentSegment = podcast?.segments?.[currentSegmentIndex];

  // Calculate cumulative time at segment start (using actual durations)
  const getSegmentStartTime = useCallback((segmentIndex: number) => {
    if (!podcast?.segments) return 0;
    let time = 0;
    for (let i = 0; i < segmentIndex; i++) {
      time += getSegmentDuration(i);
    }
    return time;
  }, [podcast?.segments, getSegmentDuration]);

  // Fetch and cache audio blob for a segment
  const fetchSegmentAudio = useCallback(async (segmentIndex: number): Promise<string | null> => {
    if (!podcastId || !token || !podcast?.segments) return null;

    // Check if already cached
    const cached = preloadedSegmentsRef.current.get(segmentIndex);
    if (cached) return cached;

    const segment = podcast.segments[segmentIndex];
    if (!segment) return null;

    const baseUrl = getApiBaseUrl();
    const audioUrl = `${baseUrl}/api/v1/podcasts/${podcastId}/audio/${segment.sequence}`;

    try {
      const response = await fetch(audioUrl, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Failed to load audio');
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);

      // Cache it
      preloadedSegmentsRef.current.set(segmentIndex, blobUrl);
      return blobUrl;
    } catch (err) {
      console.error(`Failed to load segment ${segmentIndex}:`, err);
      return null;
    }
  }, [podcastId, token, podcast?.segments]);

  // Create audio buffer for a segment (captures actual duration on load)
  const createAudioBuffer = useCallback((segmentIndex: number, blobUrl: string): AudioBuffer => {
    const audio = new Audio();
    audio.src = blobUrl;
    audio.preload = 'auto';

    // Capture actual duration when metadata loads
    audio.addEventListener('loadedmetadata', () => {
      if (audio.duration && audio.duration > 0 && isFinite(audio.duration)) {
        actualDurationsRef.current.set(segmentIndex, audio.duration);
        setDurationsLoaded(prev => prev + 1);
      }
    });

    // Attach ended listener immediately (uses callback ref to avoid stale closures)
    audio.addEventListener('ended', () => {
      if (onSegmentEndCallback) {
        onSegmentEndCallback(segmentIndex);
      }
    });

    return {
      audio,
      segmentIndex,
      blobUrl,
      isLoaded: true,
    };
  }, []);

  // Initialize and load first segment
  useEffect(() => {
    if (!podcast?.segments?.length || !podcastId || !token) return;

    const initializeAudio = async () => {
      setIsAudioReady(false);

      // Load first segment
      const firstBlobUrl = await fetchSegmentAudio(0);
      if (!firstBlobUrl) {
        setError('Failed to load audio');
        return;
      }

      const buffer = createAudioBuffer(0, firstBlobUrl);
      currentAudioRef.current = buffer;
      segmentStartTimeRef.current = 0;
      setIsAudioReady(true);

      // Preload second segment if exists
      if (podcast.segments.length > 1) {
        const secondBlobUrl = await fetchSegmentAudio(1);
        if (secondBlobUrl) {
          nextAudioRef.current = createAudioBuffer(1, secondBlobUrl);
        }
      }
    };

    initializeAudio();

    // Cleanup
    return () => {
      preloadedSegmentsRef.current.forEach((url) => URL.revokeObjectURL(url));
      preloadedSegmentsRef.current.clear();
    };
  }, [podcast?.segments, podcastId, token, fetchSegmentAudio, createAudioBuffer]);

  // Handle segment end callback
  const handleSegmentEnd = useCallback(async (endedSegmentIndex: number) => {
    if (!podcast?.segments) return;

    // Only handle if this is the current segment that ended
    if (endedSegmentIndex !== currentSegmentIndex) return;

    const nextIndex = currentSegmentIndex + 1;

    if (nextIndex >= podcast.segments.length) {
      // Podcast finished
      setIsPlaying(false);
      return;
    }

    // Seamlessly switch to preloaded next segment
    if (nextAudioRef.current && nextAudioRef.current.segmentIndex === nextIndex) {
      currentAudioRef.current = nextAudioRef.current;
      nextAudioRef.current = null;
      segmentStartTimeRef.current = getSegmentStartTime(nextIndex);
      setCurrentSegmentIndex(nextIndex);

      currentAudioRef.current.audio.play().catch(console.error);

      // Preload the following segment
      const followingIndex = nextIndex + 1;
      if (followingIndex < podcast.segments.length) {
        const blobUrl = await fetchSegmentAudio(followingIndex);
        if (blobUrl) {
          nextAudioRef.current = createAudioBuffer(followingIndex, blobUrl);
        }
      }
    } else {
      // Fallback: next not preloaded, load it now
      const blobUrl = await fetchSegmentAudio(nextIndex);
      if (blobUrl) {
        currentAudioRef.current = createAudioBuffer(nextIndex, blobUrl);
        segmentStartTimeRef.current = getSegmentStartTime(nextIndex);
        setCurrentSegmentIndex(nextIndex);
        currentAudioRef.current.audio.play().catch(console.error);
      }
    }
  }, [currentSegmentIndex, podcast?.segments, getSegmentStartTime, fetchSegmentAudio, createAudioBuffer]);

  // Update the callback ref whenever handleSegmentEnd changes
  useEffect(() => {
    onSegmentEndCallback = handleSegmentEnd;
    return () => {
      onSegmentEndCallback = null;
    };
  }, [handleSegmentEnd]);

  // Handle timeupdate for progress tracking
  useEffect(() => {
    const currentBuffer = currentAudioRef.current;
    if (!currentBuffer || !podcast?.segments) return;

    const audio = currentBuffer.audio;

    const handleTimeUpdate = () => {
      const segmentTime = audio.currentTime;
      const absoluteTime = segmentStartTimeRef.current + segmentTime;
      setCurrentTime(Math.floor(absoluteTime));
    };

    const handleError = (e: Event) => {
      console.error('Audio error:', e);
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('error', handleError);
    };
  }, [currentSegmentIndex, podcast?.segments, isAudioReady]);

  // Play/pause audio
  useEffect(() => {
    const currentBuffer = currentAudioRef.current;
    if (!currentBuffer || !isAudioReady) return;

    const audio = currentBuffer.audio;

    if (isPlaying) {
      audio.play().catch((err) => {
        console.error('Failed to play audio:', err);
        setIsPlaying(false);
      });
    } else {
      audio.pause();
    }
  }, [isPlaying, isAudioReady]);

  // Update progress bar
  useEffect(() => {
    setProgress((currentTime / totalDuration) * 100);
  }, [currentTime, totalDuration]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        currentAudioRef.current.audio.pause();
        currentAudioRef.current.audio.src = '';
      }
      if (nextAudioRef.current) {
        nextAudioRef.current.audio.pause();
        nextAudioRef.current.audio.src = '';
      }
      if (resumeAudioRef.current) {
        resumeAudioRef.current.pause();
        resumeAudioRef.current.src = '';
      }
      preloadedSegmentsRef.current.forEach((url) => URL.revokeObjectURL(url));
      preloadedSegmentsRef.current.clear();
    };
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayPause = () => {
    if (!podcast && !podcastId) {
      setIsPlaying(!isPlaying);
      return;
    }
    setIsPlaying(!isPlaying);
  };

  const handleSkipBack = () => {
    const currentAudio = currentAudioRef.current?.audio;
    if (currentAudio && currentAudio.currentTime > 3) {
      currentAudio.currentTime = 0;
    } else if (currentSegmentIndex > 0) {
      skipToSegment(currentSegmentIndex - 1);
    }
  };

  const handleSkipForward = () => {
    if (podcast?.segments && currentSegmentIndex < podcast.segments.length - 1) {
      skipToSegment(currentSegmentIndex + 1);
    }
  };

  // Skip to a specific segment with preloading
  const skipToSegment = async (targetIndex: number) => {
    if (!podcast?.segments || targetIndex < 0 || targetIndex >= podcast.segments.length) return;

    const wasPlaying = isPlaying;

    if (currentAudioRef.current) {
      currentAudioRef.current.audio.pause();
    }

    if (nextAudioRef.current && nextAudioRef.current.segmentIndex === targetIndex) {
      currentAudioRef.current = nextAudioRef.current;
      nextAudioRef.current = null;
    } else {
      const blobUrl = await fetchSegmentAudio(targetIndex);
      if (blobUrl) {
        currentAudioRef.current = createAudioBuffer(targetIndex, blobUrl);
      }
    }

    segmentStartTimeRef.current = getSegmentStartTime(targetIndex);
    setCurrentSegmentIndex(targetIndex);

    if (wasPlaying && currentAudioRef.current) {
      currentAudioRef.current.audio.play().catch(console.error);
    }

    const nextIndex = targetIndex + 1;
    if (nextIndex < podcast.segments.length) {
      const nextBlobUrl = await fetchSegmentAudio(nextIndex);
      if (nextBlobUrl) {
        nextAudioRef.current = createAudioBuffer(nextIndex, nextBlobUrl);
      }
    }
  };

  const handleProgressClick = async (e: React.MouseEvent<HTMLDivElement>) => {
    if (!podcast?.segments) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const clickPosition = (e.clientX - rect.left) / rect.width;
    const targetTime = clickPosition * totalDuration;

    let cumulativeTime = 0;
    for (let i = 0; i < podcast.segments.length; i++) {
      const segmentDuration = getSegmentDuration(i);
      if (cumulativeTime + segmentDuration > targetTime) {
        const positionInSegment = targetTime - cumulativeTime;

        if (i === currentSegmentIndex) {
          const currentAudio = currentAudioRef.current?.audio;
          if (currentAudio) {
            currentAudio.currentTime = positionInSegment;
          }
        } else {
          await skipToSegment(i);
          setTimeout(() => {
            const currentAudio = currentAudioRef.current?.audio;
            if (currentAudio) {
              currentAudio.currentTime = positionInSegment;
            }
          }, 100);
        }
        break;
      }
      cumulativeTime += segmentDuration;
    }
  };

  // --- Q&A Flow ---

  const handleRaiseHand = () => {
    setIsPlaying(false);
    setShowHandAnimation(true);
  };

  const handleAnimationComplete = () => {
    setShowHandAnimation(false);
    setShowQuestionModal(true);
  };

  const handleAskQuestion = async (question: string, audioBlob?: Blob) => {
    if (!sessionId || !token) {
      console.error('No session or token available');
      setShowQuestionModal(false);
      setIsPlaying(true);
      return;
    }

    setIsSubmittingQuestion(true);

    try {
      let response: AskResponse;

      if (audioBlob) {
        // Voice question
        const voiceResponse: ProcessVoiceResponse = await askVoiceQuestion(sessionId, audioBlob, token);

        if (voiceResponse.is_continue_signal && voiceResponse.resume) {
          // User said "continue" or similar - resume podcast
          setShowQuestionModal(false);
          await handleResumeAfterQA(voiceResponse.resume.resume_audio_url);
          return;
        }

        if (voiceResponse.exchange) {
          response = voiceResponse.exchange;
          setCurrentQuestion(voiceResponse.transcription || 'Voice question');
        } else {
          throw new Error('No answer received');
        }
      } else {
        // Text question
        response = await askTextQuestion(sessionId, question, token);
        setCurrentQuestion(question);
      }

      setCurrentAnswer(response);
      setShowQuestionModal(false);
      setShowAnswerModal(true);

    } catch (err) {
      console.error('Failed to submit question:', err);
      setShowQuestionModal(false);
      setIsPlaying(true);
    } finally {
      setIsSubmittingQuestion(false);
    }
  };

  const handleResumeFromQuestion = () => {
    setShowQuestionModal(false);
    setIsPlaying(true);
  };

  const handleResumeFromAnswer = async () => {
    if (!sessionId || !token) {
      setShowAnswerModal(false);
      setIsPlaying(true);
      return;
    }

    setIsLoadingResume(true);

    try {
      const resumeResponse = await continueSession(sessionId, token);
      setShowAnswerModal(false);
      setCurrentAnswer(null);

      // Play resume audio if available, then resume podcast
      await handleResumeAfterQA(resumeResponse.resume_audio_url);

    } catch (err) {
      console.error('Failed to get resume line:', err);
      setShowAnswerModal(false);
      setIsPlaying(true);
    } finally {
      setIsLoadingResume(false);
    }
  };

  const handleResumeAfterQA = async (resumeAudioUrl?: string | null) => {
    if (resumeAudioUrl && token) {
      try {
        // Fetch resume audio with auth
        const baseUrl = getApiBaseUrl();
        const fullUrl = resumeAudioUrl.startsWith('http') ? resumeAudioUrl : `${baseUrl}${resumeAudioUrl}`;

        const response = await fetch(fullUrl, {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.ok) {
          const blob = await response.blob();
          const blobUrl = URL.createObjectURL(blob);

          resumeAudioRef.current = new Audio(blobUrl);
          resumeAudioRef.current.onended = () => {
            URL.revokeObjectURL(blobUrl);
            setIsPlaying(true);
          };
          resumeAudioRef.current.onerror = () => {
            URL.revokeObjectURL(blobUrl);
            setIsPlaying(true);
          };
          resumeAudioRef.current.play().catch(() => {
            setIsPlaying(true);
          });
          return;
        }
      } catch (err) {
        console.error('Failed to play resume audio:', err);
      }
    }

    // No resume audio or failed to play - just resume
    setIsPlaying(true);
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 flex items-center justify-center px-6 py-8">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-white">Loading podcast...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 flex items-center justify-center px-6 py-8">
        <div className="text-center max-w-md">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={onBackToLanding}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Go back
          </button>
        </div>
      </div>
    );
  }

  // Get display info
  const displayTitle = podcast?.title || topic;
  const displayTopic = currentSegment?.topic_label || podcast?.topic || 'Science Explained';
  const segmentCount = podcast?.segments?.length || 0;

  return (
    <>
      <div className="min-h-screen bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 flex items-center justify-center px-6 py-8 relative">
        <div className="w-full max-w-[480px] mx-auto">
          {/* Album Art with overlaid buttons */}
          <div className="mb-8 relative">
            <div className="aspect-[3/4] w-full max-w-[400px] mx-auto bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900 rounded-xl shadow-2xl flex items-center justify-center border border-blue-500/20">
              <div className="text-white text-center p-8">
                <div className="text-5xl font-bold mb-3">PodAsk</div>
                <div className="text-lg opacity-90">{displayTopic}</div>
              </div>
            </div>

            {/* Back Button */}
            <button
              onClick={onBackToLanding}
              className="absolute top-4 left-4 p-3 rounded-full bg-black/30 hover:bg-black/50 backdrop-blur-sm transition-all group"
              aria-label="Back to home"
            >
              <ArrowLeft className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
            </button>

            {/* More Options Button */}
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
              {displayTitle}
            </h2>
            <p className="text-sm text-gray-400">
              PodAsk • {displayTopic}
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
              {segmentCount > 0 && (
                <span className="text-gray-300 font-medium">
                  Segment {currentSegmentIndex + 1} of {segmentCount}
                </span>
              )}
              <span>{formatTime(Math.round(totalDuration))}</span>
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
              disabled={!sessionId}
              className="w-full text-white py-4 px-6 rounded-full font-bold text-base shadow-lg transition-all hover:scale-105 flex items-center justify-center gap-2 disabled:opacity-50 disabled:hover:scale-100"
              style={{ backgroundColor: '#F59E0B' }}
              onMouseEnter={(e) => sessionId && (e.currentTarget.style.backgroundColor = '#D97706')}
              onMouseLeave={(e) => sessionId && (e.currentTarget.style.backgroundColor = '#F59E0B')}
            >
              <Hand className="w-5 h-5" />
              Raise Hand
            </button>
            <p className="text-center text-xs text-gray-400 mt-2">
              {sessionId ? 'Ask questions anytime while listening' : 'Loading Q&A session...'}
            </p>
          </div>
        </div>
      </div>

      {/* Hand Raise Animation */}
      {showHandAnimation && (
        <HandRaiseAnimation onComplete={handleAnimationComplete} />
      )}

      {/* Question Modal */}
      {showQuestionModal && (
        <QuestionModal
          onAsk={handleAskQuestion}
          onCancel={handleResumeFromQuestion}
          autoStartRecording={true}
          isSubmitting={isSubmittingQuestion}
        />
      )}

      {/* Answer Modal */}
      {showAnswerModal && currentAnswer && token && (
        <AnswerModal
          question={currentQuestion}
          answer={currentAnswer}
          token={token}
          onResume={handleResumeFromAnswer}
          isLoadingResume={isLoadingResume}
        />
      )}
    </>
  );
}
