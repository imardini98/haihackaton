# PodAsk AI - Backend Development Plan

## Overview

FastAPI backend to orchestrate the PodAsk AI platform - transforming scientific papers into interactive podcasts with "Raise Your Hand" Q&A functionality.

**Podcast Format:** Two-voice conversation between a HOST (warm, curious mediator) and an EXPERT (knowledgeable guest). Simulates a real podcast interview where listeners can interrupt like raising a hand in an auditorium.

---

## Confirmed Tech Stack (MVP)

| Component | Choice | Notes |
|-----------|--------|-------|
| **Framework** | FastAPI | Async Python, auto docs |
| **Database** | Supabase (PostgreSQL) | Hosted, built-in auth |
| **Auth** | Supabase Email/Password | Simple signup/login |
| **LLM** | Gemini 1.5 Pro | Script generation, Q&A |
| **TTS** | ElevenLabs | Two voices (HOST + EXPERT) |
| **STT** | ElevenLabs | Transcribe user questions |
| **Papers** | ArXiv API | Research paper ingestion |
| **Audio Storage** | Local filesystem | Railway persistent storage |
| **Deployment** | Railway | Easy FastAPI deploy |
| **API Style** | REST + Async polling | Generation jobs, poll for status |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Railway)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │   Paper      │  │   Podcast    │  │   Voice      │               │
│  │   Ingestion  │  │   Generator  │  │   Interaction│               │
│  │   Service    │  │   Service    │  │   Service    │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                        │
│  ┌──────▼───────┐  ┌──────────────▼──────────────────┐               │
│  │  ArXiv API   │  │          ElevenLabs             │               │
│  │              │  │   TTS (HOST + EXPERT) + STT     │               │
│  └──────────────┘  └─────────────────────────────────┘               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     Gemini 1.5 Pro                              │ │
│  │         (Script Generation, Q&A, Resume Transitions)            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        Prompt Templates                         │ │
│  │    podcast_generation | question_answer | resume_conversation   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Supabase (PostgreSQL + Auth)                 │ │
│  │           Papers, Episodes, Transcripts, Sessions, Users        │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Podcast Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     "Raise Your Hand" Flow                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   [Podcast Playing: HOST + EXPERT dialogue - Segment N]             │
│                        │                                             │
│                        ▼                                             │
│   [User presses "Raise Hand" button]                                │
│                        │                                             │
│                        ▼                                             │
│   [Segment N continues until END - not interrupted mid-sentence]    │
│                        │                                             │
│                        ▼                                             │
│   [Play transition_to_question phrase from segment]                 │
│   HOST: "Any questions about how they measured that?"               │
│                        │                                             │
│                        ▼                                             │
│   [Mic opens → User speaks question]                                │
│                        │                                             │
│                        ▼                                             │
│   [ElevenLabs STT → Gemini Q&A → ElevenLabs TTS]                    │
│                        │                                             │
│                        ▼                                             │
│   [Play HOST acknowledgment + EXPERT answer]                        │
│                        │                                             │
│                        ▼                                             │
│   [Mic stays open - listening for follow-up]                        │
│                        │                                             │
│            ┌───────────┼───────────────────┐                        │
│            ▼           ▼                   ▼                         │
│   [Follow-up    [Continue signal]    [Silence 5s]                   │
│    question]     "okay thanks"        (timeout)                     │
│            │           │                   │                         │
│            ▼           ▼                   ▼                         │
│   [Repeat Q&A]  [Play resume_phrase]  [Play resume_phrase]          │
│                 "Alright, moving on"  "Alright, moving on"          │
│                        │                   │                         │
│                        └─────────┬─────────┘                        │
│                                  ▼                                   │
│                    [Mic closes → Play Segment N+1]                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Key behaviors:**
1. Button press marks intent, but segment finishes naturally
2. `transition_to_question` phrase invites the question (from podcast script)
3. After Q&A, `resume_phrase` bridges back to next segment
4. Both phrases are pre-generated per segment in podcast script

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings & environment variables
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Supabase auth endpoints
│   │   │   ├── papers.py       # Paper ingestion endpoints
│   │   │   ├── podcasts.py     # Podcast generation endpoints
│   │   │   ├── interaction.py  # "Raise Your Hand" endpoints
│   │   │   └── health.py       # Health check
│   │   └── dependencies.py     # Auth middleware, Supabase client
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── supabase_service.py # Supabase client wrapper
│   │   ├── arxiv_service.py    # ArXiv API integration
│   │   ├── gemini_service.py   # Gemini 1.5 Pro integration
│   │   ├── elevenlabs_service.py  # TTS + STT
│   │   ├── podcast_service.py  # Podcast orchestration + job queue
│   │   └── prompt_service.py   # Load and render prompt templates
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── paper.py            # Pydantic schemas for papers
│   │   ├── podcast.py          # Pydantic schemas for podcasts
│   │   ├── interaction.py      # Schemas for Q&A
│   │   └── auth.py             # Auth request/response schemas
│   │
│   └── utils/
│       ├── __init__.py
│       ├── audio.py            # Audio processing utilities
│       └── continue_signals.py # Detect "okay thanks", "continue", etc.
│
├── prompts/                    # Gemini prompt templates
│   ├── podcast_generation.md   # HOST + EXPERT script generation
│   ├── question_answer.md      # Q&A exchange (HOST ack + EXPERT answer)
│   └── resume_conversation.md  # HOST transition back to podcast
│
├── audio_files/                # Generated audio storage
│   └── .gitkeep
│
├── tests/
│   └── ...
│
├── requirements.txt
├── .env.example
├── Dockerfile
├── railway.toml                # Railway deployment config
└── CLAUDE.md
```

---

## Prompt Templates

Located in `/prompts/` directory. Used by `gemini_service.py` via `prompt_service.py`.

### 1. `podcast_generation.md`
Generates the main podcast script as a HOST + EXPERT dialogue.
- Input: Paper content, topic, difficulty level
- Output: JSON with metadata + dialogue segments
- Each segment is interruptible for Q&A

### 2. `question_answer.md`
Handles "Raise Your Hand" questions.
- Input: Question, podcast context, source documents
- Output: HOST acknowledgment + EXPERT answer
- Natural exchange, no counter-questions
- Ends and waits for more questions or continue signal

### 3. `resume_conversation.md`
Generates transition when user signals to continue.
- Input: Last segment, Q&A topics discussed, user signal
- Output: Brief HOST line to resume podcast
- Seamless re-entry into conversation

---

## Voice Configuration

Two distinct voices via ElevenLabs:

| Role    | Characteristics                          | Voice Style         |
|---------|------------------------------------------|---------------------|
| HOST    | Warm, curious, guides conversation       | Friendly, engaging  |
| EXPERT  | Knowledgeable, explains findings         | Confident, clear    |

```python
VOICES = {
    "host": {
        "voice_id": "{{ELEVENLABS_HOST_VOICE_ID}}",
        "stability": 0.5,
        "similarity_boost": 0.75
    },
    "expert": {
        "voice_id": "{{ELEVENLABS_EXPERT_VOICE_ID}}",
        "stability": 0.6,
        "similarity_boost": 0.8
    }
}
```

---

## MVP Interaction Details

**Button press = intent to ask, but segment completes naturally first.**

| Step | What Happens |
|------|--------------|
| 1 | User presses "Raise Hand" during segment N |
| 2 | Segment N plays to completion (no mid-sentence cut) |
| 3 | `transition_to_question` phrase plays (pre-generated in script) |
| 4 | Mic opens → User speaks question |
| 5 | ElevenLabs STT → Gemini Q&A → ElevenLabs TTS |
| 6 | HOST acknowledgment + EXPERT answer plays |
| 7 | Mic stays open for follow-up (no button needed) |
| 8 | Outcome: follow-up question OR continue signal OR 5s silence |
| 9 | `resume_phrase` plays → Segment N+1 starts |

**Continue signal phrases** (detected via ElevenLabs STT):

```python
CONTINUE_SIGNALS = [
    "okay thanks",
    "ok thanks",
    "got it",
    "continue",
    "let's keep going",
    "lets keep going",
    "thanks",
    "alright",
    "i'm good",
    "im good",
    "next",
    "move on",
    "keep going",
    "go ahead"
]
```

**Key behaviors:**
- Segment always finishes before Q&A (natural pause point)
- `transition_to_question` is from the podcast script (per segment)
- `resume_phrase` is also from the podcast script (per segment)
- 5-second silence timeout = auto-play resume phrase and continue

---

## Core Services

### 1. Paper Ingestion Service (`arxiv_service.py`)
- Search ArXiv by topic/keywords
- Download and parse PDF content
- Extract metadata (title, authors, abstract, date)
- Store in database with embeddings for RAG

### 2. Gemini Service (`gemini_service.py`)
- Load prompts from `/prompts/` directory
- Generate HOST + EXPERT podcast scripts
- Process Q&A with full context
- Generate resume transitions
- Maintain conversation context for follow-up questions

### 3. ElevenLabs Service (`elevenlabs_service.py`)
**Text-to-Speech:**
- Convert dialogue to audio with correct voice per speaker
- Interleave HOST and EXPERT audio segments
- Generate Q&A response audio (both voices)
- Stream audio chunks for real-time playback

**Speech-to-Text:**
- Transcribe user voice questions
- Detect continue signals
- Handle audio file uploads

### 4. Podcast Orchestration Service (`podcast_service.py`)
- Coordinate paper -> script -> audio pipeline
- Manage segment-by-segment playback
- Handle Q&A interruption and resume flow
- Track session state

### 6. Prompt Service (`prompt_service.py`)
- Load markdown prompt templates
- Render with variables (Jinja2 style)
- Cache loaded prompts

---

## API Endpoints

### Papers
```
GET    /api/v1/papers              # List all papers
POST   /api/v1/papers/search       # Search ArXiv for papers
POST   /api/v1/papers/ingest       # Ingest specific paper by ID
GET    /api/v1/papers/{id}         # Get paper details
DELETE /api/v1/papers/{id}         # Remove paper
```

### Podcasts
```
GET    /api/v1/podcasts            # List all generated podcasts
POST   /api/v1/podcasts/generate   # Generate new podcast from papers
GET    /api/v1/podcasts/{id}       # Get podcast details
GET    /api/v1/podcasts/{id}/audio # Stream podcast audio
GET    /api/v1/podcasts/{id}/transcript  # Get full transcript (dialogue format)
DELETE /api/v1/podcasts/{id}       # Remove podcast
```

### Interaction ("Raise Your Hand")
```
POST   /api/v1/interaction/ask          # Submit voice question (audio file)
POST   /api/v1/interaction/ask-text     # Submit text question
GET    /api/v1/interaction/{id}/answer  # Get answer audio (HOST + EXPERT)
POST   /api/v1/interaction/continue     # Process continue signal, get resume line
POST   /api/v1/interaction/session/start   # Start listening session
POST   /api/v1/interaction/session/update  # Update current position
```

### Health
```
GET    /api/v1/health              # Service health check
GET    /api/v1/health/services     # External services status
```

---

## Database Schema (Supabase SQL)

```sql
-- Papers table
CREATE TABLE papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  arxiv_id TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  authors TEXT[] NOT NULL,
  abstract TEXT,
  content TEXT,
  pdf_url TEXT,
  published_date TIMESTAMPTZ,
  categories TEXT[],
  user_id UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Podcasts table
CREATE TABLE podcasts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  summary TEXT,
  paper_ids UUID[] NOT NULL,
  script_json JSONB,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'ready', 'failed')),
  total_duration_seconds INTEGER,
  user_id UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Segments table
CREATE TABLE segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
  sequence INTEGER NOT NULL,
  topic_label TEXT,
  dialogue JSONB NOT NULL,
  key_terms TEXT[],
  difficulty_level TEXT,
  audio_url TEXT,
  duration_seconds FLOAT,
  transition_to_question TEXT,
  resume_phrase TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Listening sessions table
CREATE TABLE listening_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  podcast_id UUID REFERENCES podcasts(id),
  user_id UUID REFERENCES auth.users(id),
  current_segment_id UUID REFERENCES segments(id),
  status TEXT DEFAULT 'playing' CHECK (status IN ('playing', 'paused', 'qa_active', 'completed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Q&A exchanges table
CREATE TABLE qa_exchanges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES listening_sessions(id) ON DELETE CASCADE,
  segment_id UUID REFERENCES segments(id),
  question_text TEXT NOT NULL,
  question_audio_url TEXT,
  host_acknowledgment TEXT,
  expert_answer TEXT,
  answer_audio_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE podcasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE listening_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE qa_exchanges ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
CREATE POLICY "Users can view own papers" ON papers FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own papers" ON papers FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view own podcasts" ON podcasts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own podcasts" ON podcasts FOR INSERT WITH CHECK (auth.uid() = user_id);
```

---

## Environment Variables

```bash
# API Keys
GEMINI_API_KEY=
ELEVENLABS_API_KEY=

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=           # For server-side operations

# ElevenLabs Voice Config
ELEVENLABS_HOST_VOICE_ID=       # HOST voice
ELEVENLABS_EXPERT_VOICE_ID=     # EXPERT voice

# App Config
APP_ENV=development
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]

# Audio Config
AUDIO_STORAGE_PATH=./audio_files
MAX_QUESTION_DURATION_SECONDS=30
QA_PAUSE_DURATION_SECONDS=2.5
QA_SILENCE_TIMEOUT_SECONDS=5
```

---

## Development Phases (Full Flow MVP)

### Phase 1: Foundation
- [ ] FastAPI project structure
- [ ] Supabase client setup (DB + Auth)
- [ ] Configuration management (.env)
- [ ] Health endpoints
- [ ] Prompt service (load templates)
- [ ] Basic auth middleware (Supabase JWT)

### Phase 2: Paper Ingestion
- [ ] ArXiv API service
- [ ] Paper model in Supabase
- [ ] Search endpoint
- [ ] Ingest endpoint (by ArXiv ID)

### Phase 3: Podcast Generation (Async)
- [ ] Gemini service + `podcast_generation.md` prompt
- [ ] ElevenLabs TTS (HOST + EXPERT voices)
- [ ] Job queue for async generation
- [ ] Polling endpoint for status
- [ ] Audio file storage + streaming

### Phase 4: "Raise Your Hand" Q&A
- [ ] ElevenLabs STT (transcribe audio upload)
- [ ] Q&A flow with `question_answer.md` prompt
- [ ] Continue signal detection
- [ ] Resume with `resume_conversation.md` prompt
- [ ] Session tracking in Supabase

### Phase 5: Integration & Deploy
- [ ] End-to-end testing
- [ ] Railway deployment config
- [ ] CORS for frontend
- [ ] Error handling

---

## Commands

```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env      # Add your API keys

# Run development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Deploy to Railway
railway up
```

## Supabase Setup

1. Create project at supabase.com
2. Go to SQL Editor, run the schema (see Database Schema section)
3. Enable Email auth in Authentication > Providers
4. Copy URL and keys to .env

---

## Dependencies (requirements.txt)

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-multipart>=0.0.6
httpx>=0.26.0
aiofiles>=23.2.0
jinja2>=3.1.0

# Database & Auth
supabase>=2.0.0

# AI/ML
google-generativeai>=0.3.0
elevenlabs>=1.0.0

# Paper Ingestion
arxiv>=2.1.0

# Utilities
python-dotenv>=1.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
```

---

## Notes

- Use async/await throughout for non-blocking I/O
- Two distinct ElevenLabs voices for HOST and EXPERT
- Q&A flow: answer → pause → listen → either more questions or continue
- Continue signals trigger resume line generation before podcast resumes
- Segment-based audio allows precise Q&A context tracking
- Consider WebSocket for real-time voice interaction in future iterations
