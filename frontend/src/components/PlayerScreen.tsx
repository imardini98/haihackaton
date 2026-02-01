import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Hand, Shuffle, Repeat, ArrowLeft, MoreVertical, Loader2 } from 'lucide-react';
import { QuestionModal } from './QuestionModal';
import { HandRaiseAnimation } from './HandRaiseAnimation';
import { getPodcast, getSegmentAudioUrl, type Podcast, type Segment } from '../api/podcasts';
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

export function PlayerScreen({ topic, podcastId, token, onBackToLanding }: PlayerScreenProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [showHandAnimation, setShowHandAnimation] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);

  // Podcast state
  const [podcast, setPodcast] = useState<Podcast | null>(null);
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAudioReady, setIsAudioReady] = useState(false);

  // Dual audio buffer refs for seamless playback
  const currentAudioRef = useRef<AudioBuffer | null>(null);
  const nextAudioRef = useRef<AudioBuffer | null>(null);
  const segmentStartTimeRef = useRef(0);
  const preloadedSegmentsRef = useRef<Map<number, string>>(new Map());

  // Calculate total duration from segments or use fallback
  const totalDuration = podcast?.total_duration_seconds ||
    podcast?.segments.reduce((sum, seg) => sum + (seg.duration_seconds || 60), 0) ||
    240;

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

  // Get current segment
  const currentSegment = podcast?.segments?.[currentSegmentIndex];

  // Calculate cumulative time at segment start
  const getSegmentStartTime = useCallback((segmentIndex: number) => {
    if (!podcast?.segments) return 0;
    let time = 0;
    for (let i = 0; i < segmentIndex; i++) {
      time += podcast.segments[i].duration_seconds || 60;
    }
    return time;
  }, [podcast?.segments]);

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

  // Create audio buffer for a segment
  const createAudioBuffer = useCallback((segmentIndex: number, blobUrl: string): AudioBuffer => {
    const audio = new Audio();
    audio.src = blobUrl;
    audio.preload = 'auto';
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

  // Handle segment transitions with seamless playback
  useEffect(() => {
    const currentBuffer = currentAudioRef.current;
    if (!currentBuffer || !podcast?.segments) return;

    const audio = currentBuffer.audio;

    const handleTimeUpdate = () => {
      const segmentTime = audio.currentTime;
      const absoluteTime = segmentStartTimeRef.current + segmentTime;
      setCurrentTime(Math.floor(absoluteTime));
    };

    const handleEnded = async () => {
      const nextIndex = currentSegmentIndex + 1;

      if (nextIndex >= podcast.segments.length) {
        // Podcast finished
        setIsPlaying(false);
        return;
      }

      // Seamlessly switch to preloaded next segment
      if (nextAudioRef.current && nextAudioRef.current.segmentIndex === nextIndex) {
        // Swap buffers - next becomes current
        currentAudioRef.current = nextAudioRef.current;
        nextAudioRef.current = null;

        // Update segment start time
        segmentStartTimeRef.current = getSegmentStartTime(nextIndex);

        // Start playing immediately (no gap)
        currentAudioRef.current.audio.play().catch(console.error);

        // Update state
        setCurrentSegmentIndex(nextIndex);

        // Preload the following segment
        const followingIndex = nextIndex + 1;
        if (followingIndex < podcast.segments.length) {
          const blobUrl = await fetchSegmentAudio(followingIndex);
          if (blobUrl) {
            nextAudioRef.current = createAudioBuffer(followingIndex, blobUrl);
          }
        }
      } else {
        // Fallback: next not preloaded, load it now (will have a small gap)
        const blobUrl = await fetchSegmentAudio(nextIndex);
        if (blobUrl) {
          currentAudioRef.current = createAudioBuffer(nextIndex, blobUrl);
          segmentStartTimeRef.current = getSegmentStartTime(nextIndex);
          currentAudioRef.current.audio.play().catch(console.error);
          setCurrentSegmentIndex(nextIndex);
        }
      }
    };

    const handleError = (e: Event) => {
      console.error('Audio error:', e);
    };

    const handleCanPlayThrough = () => {
      // Audio is buffered enough for continuous playback
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    audio.addEventListener('canplaythrough', handleCanPlayThrough);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('canplaythrough', handleCanPlayThrough);
    };
  }, [currentSegmentIndex, podcast?.segments, getSegmentStartTime, fetchSegmentAudio, createAudioBuffer]);

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
      // Fallback for demo mode without real podcast
      setIsPlaying(!isPlaying);
      return;
    }
    setIsPlaying(!isPlaying);
  };

  const handleSkipBack = () => {
    // Skip to previous segment or rewind within current
    const currentAudio = currentAudioRef.current?.audio;
    if (currentAudio && currentAudio.currentTime > 3) {
      currentAudio.currentTime = 0;
    } else if (currentSegmentIndex > 0) {
      skipToSegment(currentSegmentIndex - 1);
    }
  };

  const handleSkipForward = () => {
    // Skip to next segment
    if (podcast?.segments && currentSegmentIndex < podcast.segments.length - 1) {
      skipToSegment(currentSegmentIndex + 1);
    }
  };

  // Skip to a specific segment with preloading
  const skipToSegment = async (targetIndex: number) => {
    if (!podcast?.segments || targetIndex < 0 || targetIndex >= podcast.segments.length) return;

    // Pause current audio
    if (currentAudioRef.current) {
      currentAudioRef.current.audio.pause();
    }

    // Check if target is the preloaded next segment
    if (nextAudioRef.current && nextAudioRef.current.segmentIndex === targetIndex) {
      currentAudioRef.current = nextAudioRef.current;
      nextAudioRef.current = null;
    } else {
      // Load the target segment
      const blobUrl = await fetchSegmentAudio(targetIndex);
      if (blobUrl) {
        currentAudioRef.current = createAudioBuffer(targetIndex, blobUrl);
      }
    }

    // Update state
    segmentStartTimeRef.current = getSegmentStartTime(targetIndex);
    setCurrentSegmentIndex(targetIndex);

    // Start playing if was playing
    if (isPlaying && currentAudioRef.current) {
      currentAudioRef.current.audio.play().catch(console.error);
    }

    // Preload next segment
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

    // Find which segment this time falls into
    let cumulativeTime = 0;
    for (let i = 0; i < podcast.segments.length; i++) {
      const segmentDuration = podcast.segments[i].duration_seconds || 60;
      if (cumulativeTime + segmentDuration > targetTime) {
        const positionInSegment = targetTime - cumulativeTime;

        if (i === currentSegmentIndex) {
          // Same segment, just seek
          const currentAudio = currentAudioRef.current?.audio;
          if (currentAudio) {
            currentAudio.currentTime = positionInSegment;
          }
        } else {
          // Different segment, skip to it then seek
          await skipToSegment(i);
          // Wait for audio to be ready, then seek
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

  const handleRaiseHand = () => {
    setIsPlaying(false);
    setShowHandAnimation(true);
  };

  const handleAnimationComplete = () => {
    setShowHandAnimation(false);
    setShowQuestionModal(true);
  };

  const handleAskQuestion = (question: string) => {
    setShowQuestionModal(false);
    // The question is answered directly in the playback flow,
    // so we don't show an additional "answer" popup screen.
    setIsPlaying(true);
  };

  const handleResumeFromQuestion = () => {
    setShowQuestionModal(false);
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
                {segmentCount > 0 && (
                  <div className="text-sm opacity-70 mt-2">
                    Segment {currentSegmentIndex + 1} of {segmentCount}
                  </div>
                )}
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
    </>
  );
}