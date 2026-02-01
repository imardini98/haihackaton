import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Mic, Keyboard, StopCircle, Loader2 } from 'lucide-react';

interface QuestionModalProps {
  onAsk: (question: string, audioBlob?: Blob) => void;
  onCancel: () => void;
  autoStartRecording?: boolean;
  isSubmitting?: boolean;
}

export function QuestionModal({
  onAsk,
  onCancel,
  autoStartRecording = false,
  isSubmitting = false
}: QuestionModalProps) {
  const [question, setQuestion] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [showTextInput, setShowTextInput] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingError, setRecordingError] = useState<string | null>(null);

  // Recording refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Auto-start recording when modal opens
  useEffect(() => {
    if (autoStartRecording && !showTextInput && !isSubmitting) {
      const timer = setTimeout(() => {
        handleStartRecording();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [autoStartRecording, showTextInput, isSubmitting]);

  const handleStartRecording = useCallback(async () => {
    setRecordingError(null);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        }
      });
      streamRef.current = stream;

      // Determine supported MIME type
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
        mimeType = 'audio/ogg';
      }

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        setAudioBlob(blob);

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = window.setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Failed to start recording:', error);
      setRecordingError('Could not access microphone. Please check permissions.');
    }
  }, []);

  const handleStopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [isRecording]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isSubmitting) {
      onAsk(question.trim());
    }
  };

  const handleVoiceSubmit = () => {
    if (audioBlob && !isSubmitting) {
      onAsk('', audioBlob);
    }
  };

  const handleRetryRecording = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    handleStartRecording();
  };

  const formatRecordingTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center z-50 animate-in fade-in duration-200">
      <div
        className="bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900 rounded-t-3xl sm:rounded-3xl shadow-2xl w-full max-w-[520px] border-t border-blue-800/50 sm:border animate-in slide-in-from-bottom sm:zoom-in-95 duration-300"
        style={{ maxHeight: '90vh' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 pb-4 border-b border-blue-800/50">
          <h3 className="text-xl font-semibold text-white">
            Ask a question
          </h3>
          <button
            onClick={onCancel}
            disabled={isSubmitting}
            className="p-2 hover:bg-blue-800/30 rounded-full transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="p-6">
          {!showTextInput ? (
            <>
              {/* Voice Input Section */}
              <div className="text-center mb-8">
                <p className="text-sm text-gray-400 mb-8">
                  {isRecording ? 'Listening...' : audioBlob ? 'Recording complete' : 'Tap to speak your question'}
                </p>

                {/* Error Message */}
                {recordingError && (
                  <div className="mb-6 p-3 bg-red-500/20 border border-red-500/50 rounded-xl">
                    <p className="text-sm text-red-300">{recordingError}</p>
                  </div>
                )}

                {/* Microphone Button */}
                <div className="flex justify-center mb-6">
                  {!isRecording && !audioBlob ? (
                    <button
                      onClick={handleStartRecording}
                      disabled={isSubmitting}
                      className="w-24 h-24 rounded-full flex items-center justify-center transition-all hover:scale-105 shadow-lg text-white disabled:opacity-50"
                      style={{
                        backgroundColor: '#F59E0B',
                        boxShadow: '0 10px 25px -5px rgba(245, 158, 11, 0.5)'
                      }}
                      onMouseEnter={(e) => !isSubmitting && (e.currentTarget.style.backgroundColor = '#D97706')}
                      onMouseLeave={(e) => !isSubmitting && (e.currentTarget.style.backgroundColor = '#F59E0B')}
                      aria-label="Start recording"
                    >
                      <Mic className="w-10 h-10" />
                    </button>
                  ) : isRecording ? (
                    <button
                      onClick={handleStopRecording}
                      className="w-24 h-24 rounded-full flex items-center justify-center animate-pulse shadow-lg"
                      style={{
                        backgroundColor: '#EF4444',
                        boxShadow: '0 10px 25px -5px rgba(239, 68, 68, 0.5)'
                      }}
                      aria-label="Stop recording"
                    >
                      <StopCircle className="w-10 h-10 text-white" />
                    </button>
                  ) : (
                    <div className="w-24 h-24 rounded-full flex items-center justify-center bg-green-600 shadow-lg">
                      <Mic className="w-10 h-10 text-white" />
                    </div>
                  )}
                </div>

                {/* Recording Time */}
                {(isRecording || audioBlob) && (
                  <div className="mb-6">
                    <div className="inline-flex items-center gap-2 bg-neutral-800/50 px-4 py-2 rounded-full border border-neutral-700">
                      {isRecording && (
                        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                      )}
                      <span className="text-sm text-white font-mono">
                        {formatRecordingTime(recordingTime)}
                      </span>
                    </div>
                  </div>
                )}

                {/* Waveform Animation */}
                {isRecording && (
                  <div className="flex items-center justify-center gap-1 mb-8 h-16">
                    {[...Array(20)].map((_, i) => (
                      <div
                        key={i}
                        className="w-1 rounded-full animate-pulse"
                        style={{
                          backgroundColor: '#F59E0B',
                          height: `${Math.random() * 60 + 10}%`,
                          animationDelay: `${i * 0.05}s`,
                          animationDuration: `${0.5 + Math.random() * 0.5}s`
                        }}
                      />
                    ))}
                  </div>
                )}

                {/* Recording Complete Message */}
                {audioBlob && !isRecording && (
                  <div className="bg-blue-900/30 border border-blue-700/50 rounded-2xl p-4 mb-6">
                    <p className="text-sm text-gray-400 mb-2">Voice recorded</p>
                    <p className="text-white">Your question is ready to send</p>
                  </div>
                )}

                {/* Type Instead Link */}
                {!isRecording && !audioBlob && (
                  <button
                    onClick={() => setShowTextInput(true)}
                    disabled={isSubmitting}
                    className="text-gray-400 hover:text-white text-sm flex items-center gap-2 mx-auto transition-colors disabled:opacity-50"
                  >
                    <Keyboard className="w-4 h-4" />
                    Or type your question
                  </button>
                )}
              </div>

              {/* Action Buttons for Voice */}
              {audioBlob && !isRecording && (
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={handleRetryRecording}
                    disabled={isSubmitting}
                    className="flex-1 bg-white/10 text-white py-4 px-6 rounded-full font-semibold hover:bg-white/20 transition-colors disabled:opacity-50"
                  >
                    Re-record
                  </button>

                  <button
                    onClick={handleVoiceSubmit}
                    disabled={isSubmitting}
                    className="flex-1 text-white py-4 px-6 rounded-full font-bold transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
                    style={{ backgroundColor: isSubmitting ? '#9CA3AF' : '#F59E0B' }}
                    onMouseEnter={(e) => !isSubmitting && (e.currentTarget.style.backgroundColor = '#D97706')}
                    onMouseLeave={(e) => !isSubmitting && (e.currentTarget.style.backgroundColor = '#F59E0B')}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      'Ask Question'
                    )}
                  </button>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Text Input Section */}
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="text-sm text-gray-400 mb-3 block">
                    Type your question
                  </label>
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., Can you explain that concept in simpler terms?"
                    rows={4}
                    disabled={isSubmitting}
                    className="w-full px-5 py-4 bg-blue-900/30 border border-blue-700/50 rounded-2xl focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-500/20 resize-none text-base text-white placeholder:text-gray-500 transition-all disabled:opacity-50"
                    autoFocus
                  />
                </div>

                {/* Voice Input Link */}
                <button
                  type="button"
                  onClick={() => {
                    setShowTextInput(false);
                    setQuestion('');
                  }}
                  disabled={isSubmitting}
                  className="text-gray-400 hover:text-white text-sm flex items-center gap-2 transition-colors disabled:opacity-50"
                >
                  <Mic className="w-4 h-4" />
                  Use voice instead
                </button>

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onCancel}
                    disabled={isSubmitting}
                    className="flex-1 bg-white/10 text-white py-4 px-6 rounded-full font-semibold hover:bg-white/20 transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={!question.trim() || isSubmitting}
                    className="flex-1 text-white py-4 px-6 rounded-full font-bold transition-all hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
                    style={{ backgroundColor: !question.trim() || isSubmitting ? '#9CA3AF' : '#F59E0B' }}
                    onMouseEnter={(e) => {
                      if (question.trim() && !isSubmitting) e.currentTarget.style.backgroundColor = '#D97706';
                    }}
                    onMouseLeave={(e) => {
                      if (question.trim() && !isSubmitting) e.currentTarget.style.backgroundColor = '#F59E0B';
                    }}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      'Ask Question'
                    )}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
