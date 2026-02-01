# PodAsk Frontend - Development Plan

## Overview

React + Vite + TypeScript frontend for PodAsk AI - transforming scientific papers into interactive podcasts with "Raise Your Hand" Q&A.

**Live:** https://podask.vercel.app
**Backend API:** https://amusing-luck-production-4d58.up.railway.app/api/v1

---

## Current State (Feb 2026)

### What's DONE ✅

#### Phase 1: API Client Setup ✅ COMPLETE
- [x] `src/api/http.ts` - Fetch wrapper with base URL, error handling, token support
- [x] `src/api/auth.ts` - Auth API functions (signIn, signUp, getMe, passwordReset, updatePassword)
- [x] Environment variables via `VITE_API_BASE_URL`
- [x] Token management in localStorage (`podask.session`)

#### Phase 2: Authentication Integration ✅ COMPLETE
- [x] `LoginScreen.tsx` - Calls `POST /auth/signin`
- [x] `SignupScreen.tsx` - Calls `POST /auth/signup` with first_name/last_name
- [x] Email verification flow (shows "Check your email" when access_token is empty)
- [x] URL callback handling (type=signup vs type=recovery)
- [x] JWT token stored in localStorage
- [x] Token added to authenticated requests via `requestJson()`
- [x] Session validation on app load via `getMe()`
- [x] Logout functionality (clears storage)
- [x] `ForgotPasswordScreen.tsx` - Calls `POST /auth/password-reset`
- [x] `ResetPasswordScreen.tsx` - Calls `POST /auth/password-update`

#### UI Components ✅ COMPLETE (but some are mocked)
- [x] `LandingScreen.tsx` - Topic input form (FUNCTIONAL)
- [x] `ResearchProgressScreen.tsx` - 7-step animation UI (MOCKED - no API calls)
- [x] `PlayerScreen.tsx` - Podcast player UI (MOCKED - fake timer, no audio)
- [x] `QuestionModal.tsx` - Voice/text question UI (MOCKED - no recording)
- [x] `AnswerModal.tsx` - Answer playback UI (MOCKED - no audio)
- [x] `HandRaiseAnimation.tsx` - Full-screen animation (FUNCTIONAL)
- [x] Full shadcn/ui component library available in `src/components/ui/`

---

### What's REMAINING 🔴

#### Phase 3: Paper Search & Ingestion 🔴 NOT STARTED
- [ ] Create `src/api/papers.ts`:
  - [ ] `searchPapers(query, maxResults)` → `POST /papers/search`
  - [ ] `ingestPaper(arxivId)` → `POST /papers/ingest`
  - [ ] `listPapers()` → `GET /papers`
  - [ ] `getPaper(id)` → `GET /papers/{id}`
  - [ ] `deletePaper(id)` → `DELETE /papers/{id}`
- [ ] Update `ResearchProgressScreen.tsx`:
  - [ ] Call search API with user's topic
  - [ ] Display/select papers found
  - [ ] Ingest selected papers
  - [ ] Show real progress (not fake timer)
  - [ ] Store paper IDs for podcast generation

#### Phase 4: Podcast Generation 🔴 NOT STARTED
- [ ] Create `src/api/podcasts.ts`:
  - [ ] `generatePodcast(paperIds, topic)` → `POST /podcasts/generate`
  - [ ] `getPodcastStatus(id)` → `GET /podcasts/{id}/status`
  - [ ] `getPodcast(id)` → `GET /podcasts/{id}`
  - [ ] `listPodcasts()` → `GET /podcasts`
  - [ ] `deletePodcast(id)` → `DELETE /podcasts/{id}`
- [ ] After papers ingested:
  - [ ] Call generate API with paper IDs
  - [ ] Poll status until "ready" or "failed"
  - [ ] Show generation progress
  - [ ] Navigate to player when ready

#### Phase 5: Podcast Player Integration 🔴 NOT STARTED
- [ ] Update `PlayerScreen.tsx`:
  - [ ] Accept `podcastId` prop
  - [ ] Fetch podcast with segments via API
  - [ ] Create HTML5 Audio element
  - [ ] Build audio URL: `/podcasts/{id}/audio/{sequence}`
  - [ ] Track current segment
  - [ ] Play/pause, skip, seek controls
  - [ ] Auto-advance on segment end
  - [ ] Display segment info and progress

#### Phase 6: "Raise Your Hand" Q&A 🔴 NOT STARTED
- [ ] Create `src/api/interaction.ts`:
  - [ ] `startSession(podcastId, segmentId)` → `POST /interaction/session/start`
  - [ ] `askText(sessionId, question)` → `POST /interaction/ask-text`
  - [ ] `askVoice(sessionId, audioBlob)` → `POST /interaction/ask`
  - [ ] `continueSession(sessionId)` → `POST /interaction/continue`
- [ ] Session management:
  - [ ] Start session when player loads
  - [ ] Update position on segment change
- [ ] Q&A flow:
  - [ ] On hand raise: wait for segment end
  - [ ] Open QuestionModal
  - [ ] Text question: send to API, play response audio
  - [ ] Voice question: record audio, send to API, play response
  - [ ] Continue: call API, play resume audio, next segment

#### Phase 7: Polish & UX
- [ ] Error handling with toast notifications (Sonner installed)
- [ ] Loading states for all API calls
- [ ] Podcast list view (show previous podcasts)
- [ ] Audio buffering/preloading
- [ ] Mobile responsiveness improvements

---

## Implementation Priority

### HIGH PRIORITY - Core Podcast Flow
Must complete for MVP:

| # | Task | Status |
|---|------|--------|
| 1 | Create `src/api/papers.ts` | 🔴 |
| 2 | Create `src/api/podcasts.ts` | 🔴 |
| 3 | Integrate ResearchProgressScreen with APIs | 🔴 |
| 4 | Implement status polling for generation | 🔴 |
| 5 | Integrate PlayerScreen with real audio | 🔴 |

### MEDIUM PRIORITY - Q&A Feature
Interactive functionality:

| # | Task | Status |
|---|------|--------|
| 6 | Create `src/api/interaction.ts` | 🔴 |
| 7 | Implement text Q&A flow | 🔴 |
| 8 | Implement voice recording (Web Audio API) | 🔴 |
| 9 | Implement voice Q&A flow | 🔴 |

### LOW PRIORITY - Polish
After core features:

| # | Task | Status |
|---|------|--------|
| 10 | Error toasts | 🔴 |
| 11 | Podcast history list | 🔴 |
| 12 | OAuth sign-in buttons | 🔴 |

---

## App Flow

### Current Flow (Mocked)
```
Login → Landing → Research Progress (fake) → Player (fake)
         ↑                                      ↓
         └──────────── Back to Landing ─────────┘
```

### Target Flow (Integrated)
```
Login → Landing → Search Papers → Ingest Papers → Generate Podcast → Poll Status → Player
         ↑                                                                           ↓
         │                                                            [Hand Raise] → Q&A
         │                                                                           ↓
         └───────────────────────────── Back to Landing ─────────────────────────────┘
```

---

## File Structure

```
src/
├── api/
│   ├── http.ts              ✅ HTTP client with error handling
│   ├── auth.ts              ✅ Auth functions (signIn, signUp, etc.)
│   ├── papers.ts            🔴 TODO: Paper search/ingest
│   ├── podcasts.ts          🔴 TODO: Podcast generation/playback
│   └── interaction.ts       🔴 TODO: Q&A session
├── components/
│   ├── LoginScreen.tsx      ✅ Functional
│   ├── SignupScreen.tsx     ✅ Functional
│   ├── ForgotPasswordScreen.tsx  ✅ Functional
│   ├── ResetPasswordScreen.tsx   ✅ Functional
│   ├── LandingScreen.tsx    ✅ Functional
│   ├── ResearchProgressScreen.tsx  ⚠️ UI only, needs API
│   ├── PlayerScreen.tsx     ⚠️ UI only, needs API + audio
│   ├── QuestionModal.tsx    ⚠️ UI only, needs API + recording
│   ├── AnswerModal.tsx      ⚠️ UI only, needs audio
│   ├── HandRaiseAnimation.tsx    ✅ Functional
│   ├── LoadingScreen.tsx    ✅ Functional
│   └── ui/                  ✅ shadcn/ui components
├── App.tsx                  ✅ Root with auth state
└── main.tsx                 ✅ Entry point
```

---

## API Endpoints Summary

### Auth ✅ INTEGRATED
| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `/auth/signup` | ✅ |
| POST | `/auth/signin` | ✅ |
| GET | `/auth/me` | ✅ |
| POST | `/auth/password-reset` | ✅ |
| POST | `/auth/password-update` | ✅ |

### Papers 🔴 NOT INTEGRATED
| Method | Endpoint | Auth | Status |
|--------|----------|------|--------|
| POST | `/papers/search` | No | 🔴 |
| POST | `/papers/ingest` | Yes | 🔴 |
| GET | `/papers` | Yes | 🔴 |
| GET | `/papers/{id}` | Yes | 🔴 |
| DELETE | `/papers/{id}` | Yes | 🔴 |

### Podcasts 🔴 NOT INTEGRATED
| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `/podcasts/generate` | 🔴 |
| GET | `/podcasts/{id}/status` | 🔴 |
| GET | `/podcasts` | 🔴 |
| GET | `/podcasts/{id}` | 🔴 |
| GET | `/podcasts/{id}/audio/{seq}` | 🔴 |
| DELETE | `/podcasts/{id}` | 🔴 |

### Interaction 🔴 NOT INTEGRATED
| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `/interaction/session/start` | 🔴 |
| POST | `/interaction/session/{id}/update` | 🔴 |
| POST | `/interaction/ask` | 🔴 |
| POST | `/interaction/ask-text` | 🔴 |
| POST | `/interaction/continue` | 🔴 |

---

## API Types

```typescript
// Papers
interface Paper {
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract: string;
  published_date?: string;
  pdf_url?: string;
}

interface IngestedPaper extends Paper {
  id: string;
  content?: string;
}

// Podcasts
interface Podcast {
  id: string;
  title: string;
  status: 'pending' | 'generating' | 'ready' | 'failed';
  total_duration_seconds?: number;
  segments: Segment[];
}

interface Segment {
  id: string;
  sequence: number;
  topic_label?: string;
  audio_url?: string;
  duration_seconds?: number;
}

// Interaction
interface QAExchange {
  exchange_id: string;
  host_acknowledgment: string;
  expert_answer: string;
  answer_audio_url?: string;
}
```

---

## Environment Variables

```env
# Production
VITE_API_BASE_URL=https://amusing-luck-production-4d58.up.railway.app/api/v1

# Local development
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Key Implementation Patterns

### 1. Authenticated Requests
```typescript
import { requestJson } from './http';

// Token passed automatically from localStorage
const session = JSON.parse(localStorage.getItem('podask.session'));
const data = await requestJson('/papers', { token: session.access_token });
```

### 2. Polling Pattern (Podcast Generation)
```typescript
const pollStatus = async (podcastId: string): Promise<PodcastStatus> => {
  const status = await getPodcastStatus(podcastId);
  if (status.status === 'ready') return status;
  if (status.status === 'failed') throw new Error(status.error_message);
  await new Promise(r => setTimeout(r, 3000));
  return pollStatus(podcastId);
};
```

### 3. Audio Playback
```typescript
const audio = new Audio();
audio.src = `${API_URL}/podcasts/${podcastId}/audio/${sequence}`;
audio.play();
audio.onended = () => playNextSegment();
```

### 4. Audio Recording (Q&A)
```typescript
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream);
const chunks: Blob[] = [];
recorder.ondataavailable = (e) => chunks.push(e.data);
recorder.onstop = () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  // Send to /interaction/ask
};
recorder.start();
```

---

## Notes

- Backend uses Supabase for auth - tokens are JWTs
- Audio files are MP3 format
- Podcast generation is async - must poll for status
- Q&A supports both voice and text input
- Hand raise waits for segment to finish before Q&A
