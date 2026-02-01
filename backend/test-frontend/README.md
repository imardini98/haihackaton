# PodAsk Backend Test Frontend

Two UIs for testing the backend:

## 1. Full test (index.html)

Manual control over session, segment, raise hand, clarify, answer, resume. Use this to exercise every API endpoint.

## 2. AI Development simulation (simulation.html)

Interactive podcast simulation with **real TTS audio using ElevenLabs streaming**.

- **Topic:** AI development (training, deployment, safety)
- **Audio:** Real TTS via ElevenLabs streaming API (starts playing immediately)
- **Flow:** 
  1. Start podcast → audio starts playing
  2. Raise hand → audio pauses, ask your question
  3. Simulated research → answer audio plays
  4. Resume → next segment plays

---

## How to use

### 1. Set up `.env`

```bash
cd backend
cp .env.example .env
# Edit .env and add your ElevenLabs API key:
# ELEVENLABS_API_KEY=your_key_here
```

### 2. Start the backend (port 8001)

```bash
cd backend
python run.py
```

### 3. Serve the test frontend (separate terminal)

```bash
cd backend
python -m http.server 5173
```

### 4. Open in browser

- **Simulation:** http://localhost:5173/test-frontend/simulation.html
- **Full test:** http://localhost:5173/test-frontend/index.html

### 5. Test connection

Click **"Test connection"** on the page to verify the backend is reachable.

### 6. Start the podcast

Click **"Start AI Development Podcast"** — audio will start streaming!

---

## Streaming TTS

The simulation uses ElevenLabs streaming API (`/api/v1/audio/stream`):
- Audio starts playing immediately while still being generated
- No need to wait for full file generation
- Each dialogue line is streamed separately

**Base URL default:** `http://127.0.0.1:8001`
