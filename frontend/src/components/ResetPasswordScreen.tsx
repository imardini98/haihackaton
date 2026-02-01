import React, { useMemo, useState } from 'react';
import logo from '../assets/433dc299e6c56f79156becafd6df63c758f567fc.png';
import { ApiError } from '../api/http';
import { updatePassword } from '../api/auth';

interface ResetPasswordScreenProps {
  accessToken: string;
  onBackToLogin?: () => void;
}

const ACCENT = '#F59E0B';
const ACCENT_HOVER = '#D97706';
const INPUT_BORDER_IDLE = 'rgba(255, 255, 255, 0.18)';
const INPUT_BG = 'rgba(255, 255, 255, 0.10)';
const INPUT_BG_SOFT = 'rgba(255, 255, 255, 0.06)';

export function ResetPasswordScreen({ accessToken, onBackToLogin }: ResetPasswordScreenProps) {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit = useMemo(() => {
    return (
      accessToken.trim().length > 0 &&
      newPassword.trim().length > 0 &&
      confirmPassword.trim().length > 0 &&
      newPassword === confirmPassword
    );
  }, [accessToken, newPassword, confirmPassword]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!accessToken.trim()) {
      setError('Missing recovery token. Please use the reset link from your email.');
      return;
    }

    if (!newPassword.trim() || !confirmPassword.trim()) {
      setError('Please enter and confirm your new password.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await updatePassword(accessToken, { new_password: newPassword });
      setMessage(res.message);
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.message || 'Password update failed.');
      } else if (e instanceof Error) {
        setError(e.message || 'Password update failed.');
      } else {
        setError('Password update failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

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
          <div className="text-center">
            <div className="text-white text-xl font-semibold">Choose a new password</div>
            <div className="text-gray-300 text-sm mt-2">Set a new password for your account.</div>
          </div>

          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            autoComplete="new-password"
            placeholder="New password"
            disabled={isSubmitting}
            className="w-full px-6 py-4 rounded-xl focus:outline-none transition-colors text-white placeholder:text-gray-400"
            style={{
              backgroundColor: INPUT_BG,
              border: `2px solid ${INPUT_BORDER_IDLE}`,
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = ACCENT)}
            onBlur={(e) => (e.currentTarget.style.borderColor = INPUT_BORDER_IDLE)}
          />

          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            placeholder="Confirm new password"
            disabled={isSubmitting}
            className="w-full px-6 py-4 rounded-xl focus:outline-none transition-colors text-white placeholder:text-gray-400"
            style={{
              backgroundColor: INPUT_BG_SOFT,
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
            {isSubmitting ? 'Updating…' : 'Update password'}
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

