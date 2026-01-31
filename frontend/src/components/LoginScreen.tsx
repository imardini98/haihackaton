import React, { useMemo, useState } from 'react';
import logo from '../assets/433dc299e6c56f79156becafd6df63c758f567fc.png';

interface LoginScreenProps {
  onLogin: (payload: { email: string }) => void;
}

const ACCENT = '#F59E0B'; // matches the app's amber accent used elsewhere
const ACCENT_HOVER = '#D97706';
const INPUT_BORDER_IDLE = 'rgba(255, 255, 255, 0.18)';
const INPUT_BG = 'rgba(255, 255, 255, 0.10)';
const INPUT_BG_SOFT = 'rgba(255, 255, 255, 0.06)';

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => {
    return email.trim().length > 0 && password.trim().length > 0;
  }, [email, password]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError('Please enter an email and password.');
      return;
    }

    // Frontend-only: accept any non-empty credentials for now.
    onLogin({ email: email.trim() });
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
          {/* Email (outlined) */}
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            placeholder="Email"
            className="w-full px-6 py-4 rounded-xl focus:outline-none transition-colors text-white placeholder:text-gray-400"
            style={{
              backgroundColor: INPUT_BG,
              border: `2px solid ${ACCENT}`,
            }}
          />

          {/* Password (filled) */}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            placeholder="Password"
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
            disabled={!canSubmit}
            className="w-full py-4 px-8 rounded-xl text-base font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-white shadow-lg"
            style={{ backgroundColor: ACCENT }}
            onMouseEnter={(e) => {
              if (!e.currentTarget.disabled) e.currentTarget.style.backgroundColor = ACCENT_HOVER;
            }}
            onMouseLeave={(e) => {
              if (!e.currentTarget.disabled) e.currentTarget.style.backgroundColor = ACCENT;
            }}
          >
            Sign in
          </button>

          <div className="text-center pt-2">
            <button type="button" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
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
    </div>
  );
}

