# How to Use the PodAsk Backend

## Run the backend

From the **backend** folder:

```bash
cd backend
pip install -r requirements.txt
# Copy .env.example to .env and set ELEVENLABS_API_KEY (and others if needed)
python run.py
```

- API: **http://localhost:8000**
- Swagger docs (dev): **http://localhost:8000/docs**
- ReDoc (dev): **http://localhost:8000/redoc**

---

## Features & endpoints (all under `/api/v1`)

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Basic health check |
| GET | `/api/v1/health/services` | Status of Supabase, Gemini, ElevenLabs config |

### Auth (Supabase)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Register user |
| POST | `/api/v1/auth/signin` | Sign in |
| GET | `/api/v1/auth/me` | Current user (needs token) |

### Podcasts

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| GET | `/api/v1/podcasts` | Stub (501) | List podcasts |
| POST | `/api/v1/podcasts/generate` | Stub (501) | Generate podcast from papers |
| GET | `/api/v1/podcasts/{id}` | Stub (501) | Get podcast |
| GET | `/api/v1/podcasts/{id}/audio` | Stub (501) | Stream podcast audio |
| GET | `/api/v1/podcasts/{id}/transcript` | Stub (501) | Get transcript |
| DELETE | `/api/v1/podcasts/{id}` | Stub (501) | Delete podcast |
| **POST** | **`/api/v1/podcasts/session`** | **Working** | Create listening session (send podcast JSON + optional voice prefs) |
| **GET** | **`/api/v1/podcasts/session/{session_id}`** | **Working** | Get session state |
| **POST** | **`/api/v1/podcasts/session/{session_id}/start`** | **Working** | Start current segment |
| **GET** | **`/api/v1/podcasts/session/{session_id}/voices`** | **Working** | Get session host/expert voice IDs |
| **POST** | **`/api/v1/podcasts/session/{session_id}/generate-segment-audio/{segment_id}`** | **Working** | Generate TTS for a segment’s dialogue |

### Interaction (raise hand / Q&A)

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| **POST** | **`/api/v1/interaction/ask`** | **Working** | Submit voice question (upload audio → transcribe) |
| **POST** | **`/api/v1/interaction/ask-text`** | **Working** | Submit text question |
| GET | `/api/v1/interaction/{id}/answer` | Stub (501) | Get answer (needs Gemini) |
| **POST** | **`/api/v1/interaction/continue`** | **Working** | Resume podcast (query: `?session_id=...`) |
| POST | `/api/v1/interaction/session/start` | Stub (501) | Start listening session |
| POST | `/api/v1/interaction/session/update` | Stub (501) | Update position |
| **POST** | **`/api/v1/interaction/{session_id}/clarify`** | **Working** | Request clarification (host asks for more detail) |
| **POST** | **`/api/v1/interaction/{session_id}/answer`** | **Working** | Provide answer dialogue (body: `answer_dialogue`) |

### Audio files

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| **GET** | **`/api/v1/audio/{filename}`** | **Working** | Download a generated audio file |
| **GET** | **`/api/v1/audio/voices`** | **Working** | List ElevenLabs voices |

---

## Quick test flow (no DB)

1. **Create session**  
   `POST /api/v1/podcasts/session`  
   Body: `{ "podcast": <your podcast JSON>, "host_gender": "female", "expert_gender": "male" }`  
   → Returns `id` (session_id) and `voices`.

2. **Start segment**  
   `POST /api/v1/podcasts/session/{session_id}/start`  
   → Returns current segment and whether it’s interruptible.

3. **Raise hand (text)**  
   `POST /api/v1/interaction/ask-text`  
   Body: `{ "session_id": "<session_id>", "question": "What is X?" }`  
   → Enters Q&A mode.

4. **Clarify (optional)**  
   `POST /api/v1/interaction/{session_id}/clarify`  
   → Host asks for more detail (returns text + optional audio URL).

5. **Provide answer**  
   `POST /api/v1/interaction/{session_id}/answer`  
   Body: `{ "answer_dialogue": [ { "speaker": "host", "text": "..." }, { "speaker": "expert", "text": "..." } ] }`  
   → Returns answer with generated audio URLs.

6. **Resume**  
   `POST /api/v1/interaction/continue?session_id={session_id}`  
   → Returns resume phrase and next segment.

---

## Test frontend

- **Location:** `backend/test-frontend/`
- **Use:** Open `index.html` (or serve via `python -m http.server 5173` and open `http://localhost:5173/test-frontend/`).
- **Base URL:** Set to `http://localhost:8000` so all calls hit the backend.

---

## Summary

- **Working:** Health, auth (if Supabase is set), podcast **sessions** (create, state, start segment, voices, segment audio), **interaction** (ask, ask-text, clarify, answer, continue), **audio** (file by filename, voices).
- **Stubs (501):** Podcast CRUD from DB, podcast generation from papers, interaction answer from Gemini, session start/update.
