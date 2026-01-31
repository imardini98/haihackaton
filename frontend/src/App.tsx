import React, { useEffect, useState } from 'react';
import { LandingScreen } from './components/LandingScreen';
import { ResearchProgressScreen } from './components/ResearchProgressScreen';
import { LoadingScreen } from './components/LoadingScreen';
import { PlayerScreen } from './components/PlayerScreen';
import { LoginScreen } from './components/LoginScreen';

type AppState = 'landing' | 'research' | 'loading' | 'player';
type AuthState = 'unknown' | 'authenticated' | 'unauthenticated';

const AUTH_STORAGE_KEY = 'podask.authenticated';

export default function App() {
  const [appState, setAppState] = useState<AppState>('landing');
  const [topic, setTopic] = useState('');
  const [authState, setAuthState] = useState<AuthState>('unknown');

  useEffect(() => {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      setAuthState(stored === 'true' ? 'authenticated' : 'unauthenticated');
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

  const handleLogin = ({ email }: { email: string }) => {
    // Frontend-only: persist a boolean, ignore credentials for now.
    try {
      localStorage.setItem(AUTH_STORAGE_KEY, 'true');
      localStorage.setItem('podask.email', email);
    } catch {
      // ignore
    }
    setAuthState('authenticated');
  };

  const handleLogout = () => {
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
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