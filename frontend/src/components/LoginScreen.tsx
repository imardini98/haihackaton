import React, { useMemo, useState } from 'react';
import logo from '../assets/433dc299e6c56f79156becafd6df63c758f567fc.png';
import { ApiError } from '../api/http';
import { signIn, type AuthResponse } from '../api/auth';

interface LoginScreenProps {
  onLogin: (session: AuthResponse) => void;
  onCreateAccount?: () => void;
  onForgotPassword?: () => void;
  initialError?: string | null;
  onClearError?: () => void;
}

const ACCENT = '#F59E0B'; // matches the app's amber accent used elsewhere
const ACCENT_HOVER = '#D97706';
const INPUT_BORDER_IDLE = 'rgba(255, 255, 255, 0.18)';
const INPUT_BG = 'rgba(255, 255, 255, 0.10)';
const INPUT_BG_SOFT = 'rgba(255, 255, 255, 0.06)';

export function LoginScreen({ onLogin, onCreateAccount, onForgotPassword, initialError, onClearError }: LoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(initialError || null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Clear initial error when user starts typing
  const handleInputChange = () => {
    if (initialError && onClearError) {
      onClearError();
    }
  };

  const canSubmit = useMemo(() => {
    return email.trim().length > 0 && password.trim().length > 0;
  }, [email, password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedEmail = email.trim();
    const trimmedPassword = password.trim();

    if (!trimmedEmail || !trimmedPassword) {
      setError('Please enter an email and password.');
      return;
    }

    try {
      setIsSubmitting(true);
      const session = await signIn({ email: trimmedEmail, password: trimmedPassword });
      onLogin(session);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message || 'Sign in failed.');
      } else if (e instanceof Error) {
        setError(e.message || 'Sign in failed.');
      } else {
        setError('Sign in failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left spacer - visible on md+ */}
      <div className="hidden md:block md:flex-1" />

      {/* Center content */}
      <div className="w-full md:w-[400px] md:flex-shrink-0 flex flex-col justify-center px-6 py-12">
        {/* Logo */}
        <div className="flex justify-center mb-8 md:mb-10">
          <img
            src={logo}
            alt="PodAsk Logo"
            className="h-20 md:h-24 w-auto object-contain"
          />
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Email (outlined) */}
          <input
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); handleInputChange(); }}
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

          {/* Password (filled) */}
          <input
            type="password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); handleInputChange(); }}
            autoComplete="current-password"
            placeholder="Password"
            disabled={isSubmitting}
            className="w-full px-6 py-4 rounded-xl focus:outline-none transition-colors text-white placeholder:text-gray-400"
            style={{
              backgroundColor: INPUT_BG_SOFT,
              border: `2px solid ${INPUT_BORDER_IDLE}`,
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = ACCENT)}
            onBlur={(e) => (e.currentTarget.style.borderColor = INPUT_BORDER_IDLE)}
          />

          <div className="flex justify-end">
            <button
              type="button"
              className="text-sm font-semibold transition-colors"
              style={{ color: ACCENT }}
              onMouseEnter={(e) => (e.currentTarget.style.color = ACCENT_HOVER)}
              onMouseLeave={(e) => (e.currentTarget.style.color = ACCENT)}
              onClick={onForgotPassword}
              disabled={!onForgotPassword || isSubmitting}
            >
              Forgot your password?
            </button>
          </div>

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
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>

          <div className="text-center pt-2">
            <button
              type="button"
              className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              onClick={onCreateAccount}
              disabled={!onCreateAccount || isSubmitting}
            >
              Create new account
            </button>
          </div>

          <div className="text-center pt-6">
            <div className="text-sm font-semibold mb-4" style={{ color: ACCENT }}>
              Or continue with
            </div>

            <div className="flex items-center justify-center gap-4">
              <button
                type="button"
                aria-label="Continue with Google"
                className="w-12 h-12 rounded-xl flex items-center justify-center transition-colors"
                style={{ backgroundColor: 'rgba(255, 255, 255, 0.14)', border: `1px solid ${INPUT_BORDER_IDLE}` }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.18)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.14)')}
              >
                <span className="text-lg font-semibold text-white">G</span>
              </button>

              <button
                type="button"
                aria-label="Continue with Facebook"
                className="w-12 h-12 rounded-xl flex items-center justify-center transition-colors"
                style={{ backgroundColor: 'rgba(255, 255, 255, 0.14)', border: `1px solid ${INPUT_BORDER_IDLE}` }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.18)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.14)')}
              >
                <span className="text-lg font-semibold text-white">f</span>
              </button>

              <button
                type="button"
                aria-label="Continue with Apple"
                className="w-12 h-12 rounded-xl flex items-center justify-center transition-colors"
                style={{ backgroundColor: 'rgba(255, 255, 255, 0.14)', border: `1px solid ${INPUT_BORDER_IDLE}` }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.18)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.14)')}
              >
                <span className="text-lg font-semibold text-white"></span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Right spacer - visible on md+ */}
      <div className="hidden md:block md:flex-1" />
    </div>
  );
}

