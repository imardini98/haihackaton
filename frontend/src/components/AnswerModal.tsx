import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, Loader2, Volume2 } from 'lucide-react';
import { type AskResponse } from '../api/interaction';
import { getApiBaseUrl } from '../api/http';

interface AnswerModalProps {
  question: string;
  answer: AskResponse;
  token: string;
  onResume: () => void;
  isLoadingResume?: boolean;
}

type PlaybackPhase = 'idle' | 'host' | 'expert' | 'complete';

export function AnswerModal({
  question,
  answer,
  token,
  onResume,
  isLoadingResume = false
}: AnswerModalProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackPhase, setPlaybackPhase] = useState<PlaybackPhase>('idle');
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  const hostAudioRef = useRef<HTMLAudioElement | null>(null);
  const expertAudioRef = useRef<HTMLAudioElement | null>(null);
  const hostBlobUrlRef = useRef<string | null>(null);
  const expertBlobUrlRef = useRef<string | null>(null);

  // Fetch audio with auth header
  const fetchAudioBlob = useCallback(async (url: string): Promise<string> => {
    const baseUrl = getApiBaseUrl();
    const fullUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;

    const response = await fetch(fullUrl, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!response.ok) {
      throw new Error('Failed to load audio');
    }

    const blob = await response.blob();
    return URL.createObjectURL(blob);
  }, [token]);

  // Preload audio files
  useEffect(() => {
    const loadAudio = async () => {
      setIsLoadingAudio(true);
      setAudioError(null);

      try {
        // Load host audio
        if (answer.host_audio_url) {
          const hostBlobUrl = await fetchAudioBlob(answer.host_audio_url);
          hostBlobUrlRef.current = hostBlobUrl;
          hostAudioRef.current = new Audio(hostBlobUrl);
        }

        // Load expert audio
        if (answer.expert_audio_url) {
          const expertBlobUrl = await fetchAudioBlob(answer.expert_audio_url);
          expertBlobUrlRef.current = expertBlobUrl;
          expertAudioRef.current = new Audio(expertBlobUrl);
        }

        // Auto-play when loaded
        if (hostAudioRef.current || expertAudioRef.current) {
          handlePlay();
        }
      } catch (error) {
        console.error('Failed to load answer audio:', error);
        setAudioError('Failed to load audio. You can still read the answer below.');
      } finally {
        setIsLoadingAudio(false);
      }
    };

    loadAudio();

    // Cleanup
    return () => {
      if (hostBlobUrlRef.current) URL.revokeObjectURL(hostBlobUrlRef.current);
      if (expertBlobUrlRef.current) URL.revokeObjectURL(expertBlobUrlRef.current);
      if (hostAudioRef.current) {
        hostAudioRef.current.pause();
        hostAudioRef.current = null;
      }
      if (expertAudioRef.current) {
        expertAudioRef.current.pause();
        expertAudioRef.current = null;
      }
    };
  }, [answer.host_audio_url, answer.expert_audio_url, fetchAudioBlob]);

  // Handle playback
  const handlePlay = useCallback(() => {
    setIsPlaying(true);

    if (hostAudioRef.current) {
      setPlaybackPhase('host');
      hostAudioRef.current.play().catch(console.error);

      hostAudioRef.current.onended = () => {
        if (expertAudioRef.current) {
          setPlaybackPhase('expert');
          expertAudioRef.current.play().catch(console.error);

          expertAudioRef.current.onended = () => {
            setPlaybackPhase('complete');
            setIsPlaying(false);
          };
        } else {
          setPlaybackPhase('complete');
          setIsPlaying(false);
        }
      };
    } else if (expertAudioRef.current) {
      setPlaybackPhase('expert');
      expertAudioRef.current.play().catch(console.error);

      expertAudioRef.current.onended = () => {
        setPlaybackPhase('complete');
        setIsPlaying(false);
      };
    }
  }, []);

  const handlePause = useCallback(() => {
    setIsPlaying(false);
    hostAudioRef.current?.pause();
    expertAudioRef.current?.pause();
  }, []);

  const handlePlayPause = () => {
    if (isPlaying) {
      handlePause();
    } else {
      if (playbackPhase === 'complete') {
        // Restart from beginning
        if (hostAudioRef.current) hostAudioRef.current.currentTime = 0;
        if (expertAudioRef.current) expertAudioRef.current.currentTime = 0;
        setPlaybackPhase('idle');
      }
      handlePlay();
    }
  };

  // Update progress based on current playback
  useEffect(() => {
    const updateProgress = () => {
      let current = 0;
      let total = 0;

      if (hostAudioRef.current) {
        total += hostAudioRef.current.duration || 0;
        if (playbackPhase === 'host') {
          current = hostAudioRef.current.currentTime;
        } else if (playbackPhase === 'expert' || playbackPhase === 'complete') {
          current = hostAudioRef.current.duration || 0;
        }
      }

      if (expertAudioRef.current) {
        total += expertAudioRef.current.duration || 0;
        if (playbackPhase === 'expert') {
          current += expertAudioRef.current.currentTime;
        } else if (playbackPhase === 'complete') {
          current += expertAudioRef.current.duration || 0;
        }
      }

      setDuration(total);
      setCurrentTime(current);
      if (total > 0) {
        setProgress((current / total) * 100);
      }
    };

    const interval = setInterval(updateProgress, 100);
    return () => clearInterval(interval);
  }, [playbackPhase]);

  const formatTime = (seconds: number) => {
    if (!isFinite(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center px-6 z-50 animate-in fade-in duration-200">
      <div className="bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 rounded-3xl shadow-2xl w-full max-w-[520px] p-8 border border-blue-800/50 animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
        {/* Question */}
        <div className="mb-6">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Your question:</p>
          <p className="text-base text-gray-300 italic">"{question}"</p>
        </div>

        <h3 className="text-xl font-semibold text-white mb-4">
          Answer:
        </h3>

        {/* Audio Player */}
        <div className="bg-blue-900/30 border border-blue-700/50 rounded-2xl p-6 mb-6">
          {isLoadingAudio ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
              <span className="ml-3 text-gray-400">Loading audio...</span>
            </div>
          ) : audioError ? (
            <div className="text-center py-2">
              <p className="text-sm text-amber-400">{audioError}</p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-4 mb-4">
                <button
                  onClick={handlePlayPause}
                  className="p-3 bg-white hover:scale-105 rounded-full transition-transform flex-shrink-0"
                  aria-label={isPlaying ? 'Pause answer' : 'Play answer'}
                >
                  {isPlaying ? (
                    <Pause className="w-5 h-5 text-black fill-black" />
                  ) : (
                    <Play className="w-5 h-5 text-black fill-black ml-0.5" />
                  )}
                </button>

                <div className="flex-1">
                  <div className="h-1 bg-blue-800/50 rounded-full">
                    <div
                      className="h-full bg-white rounded-full transition-all duration-100"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>

                <span className="text-sm text-gray-400 flex-shrink-0">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </span>
              </div>

              {/* Speaker Indicator */}
              <div className="flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-400">
                  {playbackPhase === 'host' && 'Host speaking...'}
                  {playbackPhase === 'expert' && 'Expert answering...'}
                  {playbackPhase === 'complete' && 'Answer complete'}
                  {playbackPhase === 'idle' && 'Ready to play'}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Text Answer (always visible) */}
        <div className="mb-8 space-y-4">
          <div className="p-4 bg-blue-900/20 rounded-xl border border-blue-800/30">
            <p className="text-xs text-blue-400 uppercase tracking-wider mb-2">Host:</p>
            <p className="text-gray-300 text-sm">{answer.host_acknowledgment}</p>
          </div>

          <div className="p-4 bg-blue-900/20 rounded-xl border border-blue-800/30">
            <p className="text-xs text-orange-400 uppercase tracking-wider mb-2">Expert:</p>
            <p className="text-gray-300 text-sm">{answer.expert_answer}</p>
          </div>

          {answer.topics_discussed.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {answer.topics_discussed.map((topic, i) => (
                <span
                  key={i}
                  className="px-2 py-1 bg-blue-800/30 text-blue-300 text-xs rounded-full"
                >
                  {topic}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Resume Button */}
        <button
          onClick={onResume}
          disabled={isLoadingResume}
          className="w-full text-white py-4 px-6 rounded-full font-bold transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
          style={{ backgroundColor: isLoadingResume ? '#9CA3AF' : '#F59E0B' }}
          onMouseEnter={(e) => !isLoadingResume && (e.currentTarget.style.backgroundColor = '#D97706')}
          onMouseLeave={(e) => !isLoadingResume && (e.currentTarget.style.backgroundColor = '#F59E0B')}
        >
          {isLoadingResume ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Preparing to resume...
            </>
          ) : (
            'Resume Podcast'
          )}
        </button>
      </div>
    </div>
  );
}
