import React, { useEffect, useState } from 'react';
import { LandingScreen } from './components/LandingScreen';
import { ResearchProgressScreen } from './components/ResearchProgressScreen';
import { LoadingScreen } from './components/LoadingScreen';
import { PlayerScreen } from './components/PlayerScreen';
import { LoginScreen } from './components/LoginScreen';
import { SignupScreen } from './components/SignupScreen';
import { ForgotPasswordScreen } from './components/ForgotPasswordScreen';
import { ResetPasswordScreen } from './components/ResetPasswordScreen';
import { getMe, type AuthResponse } from './api/auth';

type AppState = 'landing' | 'research' | 'loading' | 'player';
type AuthState = 'unknown' | 'authenticated' | 'unauthenticated';

const LEGACY_AUTH_STORAGE_KEY = 'podask.authenticated';
const SESSION_STORAGE_KEY = 'podask.session';

type UrlAuthResult =
  | { type: 'recovery'; accessToken: string }
  | { type: 'signup'; accessToken: string; refreshToken?: string }
  | { type: 'error'; code: string; description: string }
  | null;

function parseAuthFromUrl(): UrlAuthResult {
  try {
    const hash = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : window.location.hash;
    const hashParams = new URLSearchParams(hash);
    const queryParams = new URLSearchParams(window.location.search);

    // Check for errors first (e.g., expired email link)
    const error = hashParams.get('error') || queryParams.get('error');
    if (error) {
      return {
        type: 'error',
        code: hashParams.get('error_code') || queryParams.get('error_code') || error,
        description: hashParams.get('error_description') || queryParams.get('error_description') || 'Authentication failed',
      };
    }

    const accessToken = hashParams.get('access_token') || queryParams.get('access_token') || queryParams.get('token');
    if (!accessToken) return null;

    const authType = hashParams.get('type') || queryParams.get('type');

    // Email verification callback (type=signup)
    if (authType === 'signup') {
      return {
        type: 'signup',
        accessToken,
        refreshToken: hashParams.get('refresh_token') || queryParams.get('refresh_token') || undefined,
      };
    }

    // Password recovery callback (type=recovery or no type)
    return { type: 'recovery', accessToken };
  } catch {
    return null;
  }
}

function stripRecoveryParamsFromUrl() {
  try {
    const url = new URL(window.location.href);
    url.hash = '';
    url.searchParams.delete('access_token');
    url.searchParams.delete('refresh_token');
    url.searchParams.delete('token');
    url.searchParams.delete('type');
    window.history.replaceState({}, '', `${url.pathname}${url.search}`);
  } catch {
    // ignore
  }
}

function getStoredSession(): AuthResponse | null {
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<AuthResponse> | null;
    if (!parsed || typeof parsed !== 'object') return null;
    if (typeof parsed.access_token !== 'string' || !parsed.access_token.trim()) return null;
    if (typeof parsed.user_id !== 'string' || typeof parsed.email !== 'string') return null;
    return parsed as AuthResponse;
  } catch {
    return null;
  }
}

export default function App() {
  const [appState, setAppState] = useState<AppState>('landing');
  const [topic, setTopic] = useState('');
  const [authState, setAuthState] = useState<AuthState>('unknown');
  const [authView, setAuthView] = useState<'login' | 'signup' | 'forgotPassword' | 'resetPassword'>('login');
  const [recoveryToken, setRecoveryToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const clearStoredSession = () => {
      try {
        localStorage.removeItem(SESSION_STORAGE_KEY);
        localStorage.removeItem(LEGACY_AUTH_STORAGE_KEY);
        localStorage.removeItem('podask.email');
      } catch {
        // ignore
      }
    };

    const bootstrapAuth = async () => {
      const session = getStoredSession();

      if (!session) {
        clearStoredSession();
        if (!cancelled) setAuthState('unauthenticated');
        return;
      }

      try {
        await getMe(session.access_token);
        if (!cancelled) setAuthState('authenticated');
      } catch {
        clearStoredSession();
        if (!cancelled) setAuthState('unauthenticated');
      }
    };

    bootstrapAuth();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const authResult = parseAuthFromUrl();
    if (!authResult) return;

    stripRecoveryParamsFromUrl();

    if (authResult.type === 'error') {
      // Email verification or other auth error
      const message = authResult.description.replace(/\+/g, ' ');
      setAuthError(message);
      setAuthView('login');
      return;
    }

    if (authResult.type === 'signup') {
      // Email verification successful - auto-login
      (async () => {
        try {
          const userInfo = await getMe(authResult.accessToken);
          const session: AuthResponse = {
            access_token: authResult.accessToken,
            user_id: userInfo.id,
            email: userInfo.email,
            first_name: userInfo.first_name,
            last_name: userInfo.last_name,
          };
          localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
          setAuthState('authenticated');
        } catch {
          setAuthError('Email verified but failed to retrieve user info. Please sign in.');
          setAuthView('login');
        }
      })();
      return;
    }

    if (authResult.type === 'recovery') {
      // Password reset flow
      setRecoveryToken(authResult.accessToken);
      setAuthView('resetPassword');
    }
  }, []);

  const handleGeneratePodcast = (userTopic: string) => {
    setTopic(userTopic);
    setAppState('research');
  };

  const handleResearchComplete = () => {
    setAppState('player');
  };
  
  const handleBackToLanding = () => {
    setAppState('landing');
    setTopic('');
  };

  const handleLogin = (session: AuthResponse) => {
    try {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    } catch {
      // ignore
    }
    setAuthState('authenticated');
  };

  const handleLogout = () => {
    try {
      localStorage.removeItem(SESSION_STORAGE_KEY);
      localStorage.removeItem(LEGACY_AUTH_STORAGE_KEY);
      localStorage.removeItem('podask.email');
    } catch {
      // ignore
    }
    setAuthState('unauthenticated');
    setAuthView('login');
    setRecoveryToken(null);
    handleBackToLanding();
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900">
      {authState === 'authenticated' && (
        <button
          onClick={handleLogout}
          className="fixed top-4 right-4 z-50 px-4 py-2 rounded-full bg-black/30 hover:bg-black/50 backdrop-blur-sm transition-all text-white text-sm"
          aria-label="Log out"
        >
          Log out
        </button>
      )}

      {authState === 'unknown' ? (
        <div className="min-h-screen flex items-center justify-center px-6 py-12 md:py-16">
          <div className="text-white/80 text-sm">Checking session…</div>
        </div>
      ) : authState !== 'authenticated' ? (
        authView === 'signup' ? (
          <SignupScreen onSignup={handleLogin} onBackToLogin={() => setAuthView('login')} />
        ) : authView === 'forgotPassword' ? (
          <ForgotPasswordScreen onBackToLogin={() => setAuthView('login')} />
        ) : authView === 'resetPassword' ? (
          <ResetPasswordScreen
            accessToken={recoveryToken || ''}
            onBackToLogin={() => {
              setRecoveryToken(null);
              setAuthView('login');
            }}
          />
        ) : (
          <LoginScreen
            onLogin={handleLogin}
            onCreateAccount={() => setAuthView('signup')}
            onForgotPassword={() => setAuthView('forgotPassword')}
            initialError={authError}
            onClearError={() => setAuthError(null)}
          />
        )
      ) : (
        <>
          {appState === 'landing' && (
            <LandingScreen onGeneratePodcast={handleGeneratePodcast} />
          )}
          {appState === 'research' && (
            <ResearchProgressScreen topic={topic} onComplete={handleResearchComplete} />
          )}
          {appState === 'loading' && (
            <LoadingScreen />
          )}
          {appState === 'player' && (
            <PlayerScreen topic={topic} onBackToLanding={handleBackToLanding} />
          )}
        </>
      )}
    </div>
  );
}