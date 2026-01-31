import { useState, useEffect } from 'react';
import { X, Mic, Keyboard, StopCircle } from 'lucide-react';

interface QuestionModalProps {
  onAsk: (question: string) => void;
  onCancel: () => void;
  autoStartRecording?: boolean;
}

export function QuestionModal({ onAsk, onCancel, autoStartRecording = false }: QuestionModalProps) {
  const [question, setQuestion] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [showTextInput, setShowTextInput] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  // Auto-start recording when modal opens
  useEffect(() => {
    if (autoStartRecording && !showTextInput) {
      // Small delay to let animation complete
      const timer = setTimeout(() => {
        handleStartRecording();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [autoStartRecording, showTextInput]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
      onAsk(question);
    }
  };

  const handleStartRecording = () => {
    setIsRecording(true);
    setRecordingTime(0);
    
    // Simulate recording timer
    const interval = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
    
    // Simulate voice recognition after 3 seconds
    setTimeout(() => {
      clearInterval(interval);
      setIsRecording(false);
      setQuestion("Can you explain that concept in simpler terms?");
    }, 3000);
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    setQuestion("Can you explain that concept in simpler terms?");
  };

  const formatRecordingTime = (seconds: number) => {
    return `0:${seconds.toString().padStart(2, '0')}`;
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
            className="p-2 hover:bg-blue-800/30 rounded-full transition-colors"
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
                  {isRecording ? 'Listening...' : 'Tap to speak your question'}
                </p>

                {/* Microphone Button */}
                <div className="flex justify-center mb-6">
                  {!isRecording ? (
                    <button
                      onClick={handleStartRecording}
                      className="w-24 h-24 rounded-full flex items-center justify-center transition-all hover:scale-105 shadow-lg text-white"
                      style={{ 
                        backgroundColor: '#F59E0B',
                        boxShadow: '0 10px 25px -5px rgba(245, 158, 11, 0.5)'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#D97706'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#F59E0B'}
                      aria-label="Start recording"
                    >
                      <Mic className="w-10 h-10" />
                    </button>
                  ) : (
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
                  )}
                </div>

                {/* Recording Time */}
                {isRecording && (
                  <div className="mb-6">
                    <div className="inline-flex items-center gap-2 bg-neutral-800/50 px-4 py-2 rounded-full border border-neutral-700">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
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

                {/* Transcribed Text Preview */}
                {question && !isRecording && (
                  <div className="bg-blue-900/30 border border-blue-700/50 rounded-2xl p-4 mb-6">
                    <p className="text-sm text-gray-400 mb-2">Your question:</p>
                    <p className="text-white">{question}</p>
                  </div>
                )}

                {/* Type Instead Link */}
                <button
                  onClick={() => setShowTextInput(true)}
                  className="text-gray-400 hover:text-white text-sm flex items-center gap-2 mx-auto transition-colors"
                >
                  <Keyboard className="w-4 h-4" />
                  Or type your question
                </button>
              </div>

              {/* Action Buttons */}
              {question && !isRecording && (
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 bg-white/10 text-white py-4 px-6 rounded-full font-semibold hover:bg-white/20 transition-colors"
                  >
                    Cancel
                  </button>
                  
                  <button
                    onClick={() => onAsk(question)}
                    className="flex-1 text-white py-4 px-6 rounded-full font-bold transition-all hover:scale-105"
                    style={{ backgroundColor: '#F59E0B' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#D97706'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#F59E0B'}
                  >
                    Ask Question
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
                    className="w-full px-5 py-4 bg-blue-900/30 border border-blue-700/50 rounded-2xl focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-500/20 resize-none text-base text-white placeholder:text-gray-500 transition-all"
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
                  className="text-gray-400 hover:text-white text-sm flex items-center gap-2 transition-colors"
                >
                  <Mic className="w-4 h-4" />
                  Use voice instead
                </button>
                
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 bg-white/10 text-white py-4 px-6 rounded-full font-semibold hover:bg-white/20 transition-colors"
                  >
                    Cancel
                  </button>
                  
                  <button
                    type="submit"
                    disabled={!question.trim()}
                    className="flex-1 text-white py-4 px-6 rounded-full font-bold transition-all hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
                    style={{ backgroundColor: !question.trim() ? '#9CA3AF' : '#F59E0B' }}
                    onMouseEnter={(e) => {
                      if (question.trim()) e.currentTarget.style.backgroundColor = '#D97706';
                    }}
                    onMouseLeave={(e) => {
                      if (question.trim()) e.currentTarget.style.backgroundColor = '#F59E0B';
                    }}
                  >
                    Ask Question
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