import { useState } from 'react';
import { LandingScreen } from './components/LandingScreen';
import { ResearchProgressScreen } from './components/ResearchProgressScreen';
import { LoadingScreen } from './components/LoadingScreen';
import { PlayerScreen } from './components/PlayerScreen';

type AppState = 'landing' | 'research' | 'loading' | 'player';

export default function App() {
  const [appState, setAppState] = useState<AppState>('landing');
  const [topic, setTopic] = useState('');

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

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-950 via-blue-900 to-slate-900">
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
    </div>
  );
}