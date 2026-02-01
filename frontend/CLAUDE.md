# PodAsk Frontend - Development Plan

## Overview

React + Vite + TypeScript frontend for PodAsk AI - transforming scientific papers into interactive podcasts with "Raise Your Hand" Q&A.

**Live:** https://podask.vercel.app
**Backend API:** https://amusing-luck-production-4d58.up.railway.app/api/v1

---

## Current State

### Existing Components
- `LoginScreen.tsx` - Login/signup (currently mocked with localStorage)
- `LandingScreen.tsx` - Topic input to start podcast generation
- `ResearchProgressScreen.tsx` - Shows paper search/ingestion progress
- `PlayerScreen.tsx` - Podcast player with segments
- `QuestionModal.tsx` - Q&A interface
- `AnswerModal.tsx` - Display answers
- `HandRaiseAnimation.tsx` - "Raise hand" button animation
- `LoadingScreen.tsx` - Loading states

### App Flow (Current - Mocked)
```
Login → Landing → Research Progress → Player
         ↑                              ↓
         └──────── Back to Landing ─────┘
```

---

## Integration Roadmap

### Phase 1: API Client Setup
- [ ] Create `/src/lib/api.ts` - Axios/fetch wrapper with base URL
- [ ] Create `/src/lib/auth.ts` - Token management (localStorage)
- [ ] Create `/src/hooks/useAuth.ts` - Auth state hook
- [ ] Create `/src/contexts/AuthContext.tsx` - Auth context provider
- [ ] Environment variables for API URL (`.env`)

### Phase 2: Authentication Integration
- [ ] Update `LoginScreen.tsx` to call `POST /auth/signin`
- [ ] Add signup flow with `POST /auth/signup`
- [ ] Store JWT token in localStorage
- [ ] Add token to all authenticated requests
- [ ] Handle 401 errors (redirect to login)
- [ ] Implement logout (clear token)

### Phase 3: Paper Search & Ingestion
- [ ] Update `ResearchProgressScreen.tsx`:
  - [ ] Call `POST /papers/search` with topic
  - [ ] Display search results (papers found)
  - [ ] Call `POST /papers/ingest` for selected papers
  - [ ] Show ingestion progress
  - [ ] Store paper IDs for podcast generation

### Phase 4: Podcast Generation
- [ ] After papers ingested, call `POST /podcasts/generate`
- [ ] Poll `GET /podcasts/{id}/status` until "ready"
- [ ] Show generation progress (pending → generating → ready)
- [ ] Handle generation errors
- [ ] Navigate to player when ready

### Phase 5: Podcast Player Integration
- [ ] Update `PlayerScreen.tsx`:
  - [ ] Fetch podcast with `GET /podcasts/{id}`
  - [ ] Load segments and audio URLs
  - [ ] Play segment audio from `GET /podcasts/{id}/audio/{sequence}`
  - [ ] Track current segment
  - [ ] Auto-advance to next segment

### Phase 6: "Raise Your Hand" Q&A
- [ ] Start session with `POST /interaction/session/start`
- [ ] On hand raise:
  - [ ] Wait for current segment to finish
  - [ ] Play `transition_to_question` audio
  - [ ] Open QuestionModal
- [ ] Voice question:
  - [ ] Record audio (Web Audio API)
  - [ ] Send to `POST /interaction/ask`
  - [ ] Play response audio (host + expert)
- [ ] Text question (fallback):
  - [ ] Send to `POST /interaction/ask-text`
  - [ ] Play response audio
- [ ] Continue signal:
  - [ ] Call `POST /interaction/continue`
  - [ ] Play resume audio
  - [ ] Continue to next segment

### Phase 7: Polish & UX
- [ ] Error handling with toast notifications
- [ ] Loading states for all API calls
- [ ] Offline detection
- [ ] Audio buffering/preloading
- [ ] Keyboard shortcuts for player
- [ ] Mobile responsiveness

---

## API Endpoints Summary

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register user |
| POST | `/auth/signin` | Login user |
| GET | `/auth/me` | Get current user |
| POST | `/auth/password-reset` | Request password reset |

### Papers
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/papers/search` | No | Search ArXiv |
| POST | `/papers/ingest` | Yes | Ingest paper |
| GET | `/papers` | Yes | List user's papers |
| GET | `/papers/{id}` | Yes | Get paper |
| DELETE | `/papers/{id}` | Yes | Delete paper |

### Podcasts
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/podcasts/generate` | Start generation |
| GET | `/podcasts/{id}/status` | Poll status |
| GET | `/podcasts` | List podcasts |
| GET | `/podcasts/{id}` | Get with segments |
| GET | `/podcasts/{id}/audio/{seq}` | Stream audio |
| DELETE | `/podcasts/{id}` | Delete podcast |

### Interaction
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/interaction/session/start` | Start session |
| POST | `/interaction/session/{id}/update` | Update position |
| POST | `/interaction/ask` | Voice question |
| POST | `/interaction/ask-text` | Text question |
| POST | `/interaction/continue` | Continue signal |

---

## File Structure (Proposed)

```
src/
├── components/          # UI components (existing)
├── contexts/
│   └── AuthContext.tsx  # Auth state provider
├── hooks/
│   ├── useAuth.ts       # Auth hook
│   ├── usePodcast.ts    # Podcast player hook
│   └── useRecorder.ts   # Audio recording hook
├── lib/
│   ├── api.ts           # API client
│   ├── auth.ts          # Token management
│   └── audio.ts         # Audio utilities
├── types/
│   └── api.ts           # TypeScript types for API
├── App.tsx
└── main.tsx
```

---

## Environment Variables

```env
VITE_API_URL=https://amusing-luck-production-4d58.up.railway.app/api/v1
```

For local development:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Key Integration Points

### 1. Token Management
```typescript
// Store token after login
localStorage.setItem('podask.token', response.access_token);

// Add to requests
headers: {
  'Authorization': `Bearer ${token}`
}
```

### 2. Polling Pattern (Podcast Generation)
```typescript
const pollStatus = async (podcastId: string) => {
  const status = await api.get(`/podcasts/${podcastId}/status`);
  if (status.status === 'ready') return status;
  if (status.status === 'failed') throw new Error(status.error_message);
  await sleep(2000);
  return pollStatus(podcastId);
};
```

### 3. Audio Playback
```typescript
const audio = new Audio(`${API_URL}/podcasts/${id}/audio/${sequence}`);
audio.play();
audio.onended = () => playNextSegment();
```

### 4. Audio Recording (Q&A)
```typescript
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream);
// ... record and send to /interaction/ask
```

---

## Notes

- Backend uses Supabase for auth - tokens are JWTs
- Audio files are MP3 format
- Podcast generation is async - must poll for status
- Q&A supports both voice and text input
- 5-second silence timeout auto-continues podcast
