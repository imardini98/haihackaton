import React, { useMemo, useState } from 'react';
import logo from '../assets/433dc299e6c56f79156becafd6df63c758f567fc.png';
import { ApiError } from '../api/http';
import { requestPasswordReset } from '../api/auth';

interface ForgotPasswordScreenProps {
  onBackToLogin?: () => void;
}

const ACCENT = '#F59E0B';
const ACCENT_HOVER = '#D97706';
const INPUT_BORDER_IDLE = 'rgba(255, 255, 255, 0.18)';
const INPUT_BG = 'rgba(255, 255, 255, 0.10)';

export function ForgotPasswordScreen({ onBackToLogin }: ForgotPasswordScreenProps) {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit = useMemo(() => email.trim().length > 0, [email]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    const trimmedEmail = email.trim();
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/0e77b2eb-a7f1-4359-ad19-ef751822d1d5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'frontend/src/components/ForgotPasswordScreen.tsx:handleSubmit',message:'Forgot password submit',data:{emailLen:trimmedEmail.length,hasAt:trimmedEmail.includes('@'),isSubmittingBefore:isSubmitting},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H1'})}).catch(()=>{});
    // #endregion
    if (!trimmedEmail) {
      setError('Please enter your email.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await requestPasswordReset({ email: trimmedEmail });
      setMessage(res.message);
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/0e77b2eb-a7f1-4359-ad19-ef751822d1d5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'frontend/src/components/ForgotPasswordScreen.tsx:handleSubmit',message:'Forgot password success UI',data:{messageLen:(res?.message||'').length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H2'})}).catch(()=>{});
      // #endregion
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message || 'Password reset failed.');
      } else if (e instanceof Error) {
        setError(e.message || 'Password reset failed.');
      } else {
        setError('Password reset failed.');
      }
      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/0e77b2eb-a7f1-4359-ad19-ef751822d1d5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'frontend/src/components/ForgotPasswordScreen.tsx:handleSubmit',message:'Forgot password error UI',data:{errorType:(e instanceof ApiError)?'ApiError':(e instanceof Error)?'Error':'Unknown'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H3'})}).catch(()=>{});
      // #endregion
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 md:py-16">
      <div className="w-full max-w-[420px] mx-auto">
        {/* Logo */}
        <div className="flex justify-center mb-8 md:mb-10">
          <img
            src={logo}
            alt="PodAsk Logo"
            className="h-20 md:h-24 w-auto object-contain"
          />
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="text-center">
            <div className="text-white text-xl font-semibold">Reset your password</div>
            <div className="text-gray-300 text-sm mt-2">
              Enter your email and we’ll send you a reset link.
            </div>
          </div>

          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            placeholder="Email"
            disabled={isSubmitting}
            className="w-full px-6 py-4 rounded-xl focus:outline-none transition-colors text-white placeholder:text-gray-400"
            style={{
              backgroundColor: INPUT_BG,
              border: `2px solid ${INPUT_BORDER_IDLE}`,
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = ACCENT)}
            onBlur={(e) => (e.currentTarget.style.borderColor = INPUT_BORDER_IDLE)}
          />

          {message && (
            <div
              className="rounded-xl px-4 py-3 text-sm"
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.35)',
              }}
            >
              <p className="text-white">{message}</p>
            </div>
          )}

          {error && (
            <div
              className="rounded-xl px-4 py-3 text-sm"
              style={{
                backgroundColor: 'rgba(244, 63, 94, 0.12)',
                border: '1px solid rgba(244, 63, 94, 0.35)',
              }}
            >
              <p className="text-white">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={!canSubmit || isSubmitting}
            className="w-full py-4 px-8 rounded-xl text-base font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-white shadow-lg"
            style={{ backgroundColor: ACCENT }}
            onMouseEnter={(e) => {
              if (!e.currentTarget.disabled) e.currentTarget.style.backgroundColor = ACCENT_HOVER;
            }}
            onMouseLeave={(e) => {
              if (!e.currentTarget.disabled) e.currentTarget.style.backgroundColor = ACCENT;
            }}
          >
            {isSubmitting ? 'Sending…' : 'Send reset link'}
          </button>

          <div className="text-center pt-2">
            <button
              type="button"
              className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              onClick={onBackToLogin}
              disabled={!onBackToLogin || isSubmitting}
            >
              Back to sign in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

