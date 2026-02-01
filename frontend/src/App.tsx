import React, { useEffect, useState } from 'react';
import { LandingScreen } from './components/LandingScreen';
import { ResearchProgressScreen } from './components/ResearchProgressScreen';
import { LoadingScreen } from './components/LoadingScreen';
import { PlayerScreen } from './components/PlayerScreen';
import { LoginScreen } from './components/LoginScreen';
import type { AuthResponse } from './api/auth';

type AppState = 'landing' | 'research' | 'loading' | 'player';
type AuthState = 'unknown' | 'authenticated' | 'unauthenticated';

const LEGACY_AUTH_STORAGE_KEY = 'podask.authenticated';
const SESSION_STORAGE_KEY = 'podask.session';

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

  useEffect(() => {
    try {
      const session = getStoredSession();
      if (session) {
        setAuthState('authenticated');
        return;
      }

      // Clear legacy storage (boolean auth) so we don't show "logged in"
      // without having a real backend session token.
      localStorage.removeItem(LEGACY_AUTH_STORAGE_KEY);
      localStorage.removeItem('podask.email');
      setAuthState('unauthenticated');
    } catch {
      setAuthState('unauthenticated');
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

      {authState !== 'authenticated' ? (
        <LoginScreen onLogin={handleLogin} />
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