import React, { useMemo, useState } from 'react';
import logo from '../assets/433dc299e6c56f79156becafd6df63c758f567fc.png';
import { ApiError } from '../api/http';
import { signUp, type AuthResponse } from '../api/auth';

interface SignupScreenProps {
  onSignup: (session: AuthResponse) => void;
  onBackToLogin?: () => void;
}

type SignupState = 'form' | 'emailSent';

const ACCENT = '#F59E0B'; // matches the app's amber accent used elsewhere
const ACCENT_HOVER = '#D97706';
const INPUT_BORDER_IDLE = 'rgba(255, 255, 255, 0.18)';
const INPUT_BG = 'rgba(255, 255, 255, 0.10)';
const INPUT_BG_SOFT = 'rgba(255, 255, 255, 0.06)';

export function SignupScreen({ onSignup, onBackToLogin }: SignupScreenProps) {
  const [signupState, setSignupState] = useState<SignupState>('form');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit = useMemo(() => {
    return (
      firstName.trim().length > 0 &&
      lastName.trim().length > 0 &&
      email.trim().length > 0 &&
      password.trim().length > 0
    );
  }, [firstName, lastName, email, password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedEmail = email.trim();
    const trimmedPassword = password.trim();

    if (!firstName.trim() || !lastName.trim() || !trimmedEmail || !trimmedPassword) {
      setError('Please fill out all fields.');
      return;
    }

    try {
      setIsSubmitting(true);
      const session = await signUp({
        email: trimmedEmail,
        password: trimmedPassword,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });

      // If access_token is empty, email verification is required
      if (!session.access_token) {
        setSignupState('emailSent');
      } else {
        onSignup(session);
      }
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message || 'Sign up failed.');
      } else if (e instanceof Error) {
        setError(e.message || 'Sign up failed.');
      } else {
        setError('Sign up failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Email verification sent screen
  if (signupState === 'emailSent') {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-12 md:px-12 md:py-20 lg:px-24">
        <div className="w-full max-w-[420px] mx-auto text-center">
          {/* Logo */}
          <div className="flex justify-center mb-8 md:mb-10">
            <img
              src={logo}
              alt="PodAsk Logo"
              className="h-20 md:h-24 w-auto object-contain"
            />
          </div>

          {/* Success Icon */}
          <div className="flex justify-center mb-6">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center"
              style={{ backgroundColor: 'rgba(34, 197, 94, 0.15)' }}
            >
              <svg
                className="w-8 h-8 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
          </div>

          <h2 className="text-2xl font-bold text-white mb-3">Check your email</h2>
          <p className="text-gray-300 mb-2">
            We've sent a verification link to:
          </p>
          <p className="text-white font-medium mb-6">{email}</p>
          <p className="text-gray-400 text-sm mb-8">
            Click the link in the email to verify your account, then you can sign in.
          </p>

          <button
            type="button"
            onClick={onBackToLogin}
            className="w-full py-4 px-8 rounded-xl text-base font-semibold transition-colors text-white shadow-lg"
            style={{ backgroundColor: ACCENT }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = ACCENT_HOVER)}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = ACCENT)}
          >
            Back to Sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 md:px-12 md:py-20 lg:px-24">
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
          {/* First name (outlined) */}
          <input
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            autoComplete="given-name"
            placeholder="First name"
            disabled={isSubmitting}
            className="w-full px-6 py-4 rounded-xl focus:outline-none transition-colors text-white placeholder:text-gray-400"
            style={{
              backgroundColor: INPUT_BG,
              border: `2px solid ${INPUT_BORDER_IDLE}`,
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = ACCENT)}
            onBlur={(e) => (e.currentTarget.style.borderColor = INPUT_BORDER_IDLE)}
          />

          {/* Last name (filled) */}
          <input
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            autoComplete="family-name"
            placeholder="Last name"
            disabled={isSubmitting}
            className="w-full px-6 py-4 rounded-xl focus:outline-none transition-colors text-white placeholder:text-gray-400"
            style={{
              backgroundColor: INPUT_BG_SOFT,
              border: `2px solid ${INPUT_BORDER_IDLE}`,
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = ACCENT)}
            onBlur={(e) => (e.currentTarget.style.borderColor = INPUT_BORDER_IDLE)}
          />

          {/* Email (outlined) */}
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

          {/* Password (filled) */}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
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
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </button>

          <div className="text-center pt-2">
            <button
              type="button"
              className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              onClick={onBackToLogin}
              disabled={!onBackToLogin || isSubmitting}
            >
              Already have an account? Sign in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

