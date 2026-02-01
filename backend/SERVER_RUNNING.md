# 🚀 PodAsk API - Running on localhost:8000

## Server Status: ✅ RUNNING

The FastAPI server is now running at:
- **Base URL:** `http://localhost:8000`
- **API Docs (Swagger):** `http://localhost:8000/docs`
- **Alternative Docs (ReDoc):** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/api/v1/health`

## Quick Test Results

✅ **Health Endpoint Test:**
```json
{
  "status": "healthy",
  "service": "podask-api"
}
```

## 📋 Available API Endpoints

### Health & Status

#### Get Health Status
```bash
GET http://localhost:8000/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "podask-api"
}
```

---

### Papers Management

#### Search ArXiv Papers
```bash
POST http://localhost:8000/api/v1/papers/search
Content-Type: application/json

{
  "query": "machine learning",
  "max_results": 5
}
```

#### Ingest a Paper
```bash
POST http://localhost:8000/api/v1/papers/ingest
Content-Type: application/json

{
  "arxiv_id": "2301.00001"
}
```

#### List All Papers
```bash
GET http://localhost:8000/api/v1/papers
```

#### Get Specific Paper
```bash
GET http://localhost:8000/api/v1/papers/{paper_id}
```

---

### Podcast Generation

#### Generate a New Podcast
```bash
POST http://localhost:8000/api/v1/podcasts/generate
Content-Type: application/json

{
  "paper_ids": ["uuid-1", "uuid-2"],
  "topic": "Understanding Transformers in AI",
  "difficulty_level": "intermediate"
}
```

**Response:**
```json
{
  "podcast_id": "uuid",
  "status": "pending",
  "message": "Podcast generation started"
}
```

#### Get Podcast Status
```bash
GET http://localhost:8000/api/v1/podcasts/{podcast_id}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Understanding Transformers in AI",
  "status": "ready",  // or "generating", "pending", "failed"
  "segments": [...]
}
```

#### List All Podcasts
```bash
GET http://localhost:8000/api/v1/podcasts
```

#### Stream Podcast Audio
```bash
GET http://localhost:8000/api/v1/podcasts/{podcast_id}/audio
```

---

### Interactive Q&A ("Raise Your Hand")

#### Ask a Question (Text)
```bash
POST http://localhost:8000/api/v1/interaction/ask-text
Content-Type: application/json

{
  "question": "How does the attention mechanism work?",
  "podcast_id": "uuid",
  "segment_id": "uuid",
  "session_id": "uuid"
}
```

#### Ask a Question (Audio)
```bash
POST http://localhost:8000/api/v1/interaction/ask
Content-Type: multipart/form-data

audio_file: <audio file>
podcast_id: uuid
segment_id: uuid
session_id: uuid
```

#### Get Answer Audio
```bash
GET http://localhost:8000/api/v1/interaction/{exchange_id}/answer
```

---

## 🧪 Testing with curl

### Test Health
```bash
curl http://localhost:8000/api/v1/health
```

### Search Papers
```bash
curl -X POST http://localhost:8000/api/v1/papers/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "transformers",
    "max_results": 3
  }'
```

### List Papers
```bash
curl http://localhost:8000/api/v1/papers
```

---

## 🧪 Testing with Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Test health
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Search papers
response = requests.post(
    f"{BASE_URL}/papers/search",
    json={
        "query": "neural networks",
        "max_results": 5
    }
)
papers = response.json()
print(f"Found {len(papers)} papers")

# Generate podcast
response = requests.post(
    f"{BASE_URL}/podcasts/generate",
    json={
        "paper_ids": ["paper-uuid-1"],
        "topic": "Neural Networks Explained",
        "difficulty_level": "beginner"
    }
)
podcast = response.json()
print(f"Podcast ID: {podcast['podcast_id']}")

# Check podcast status
podcast_id = podcast['podcast_id']
response = requests.get(f"{BASE_URL}/podcasts/{podcast_id}")
status = response.json()
print(f"Status: {status['status']}")
```

---

## 🌐 Browser Testing

### Interactive API Documentation (Recommended!)

Open in your browser:
```
http://localhost:8000/docs
```

This provides:
- ✅ Interactive API testing interface
- ✅ Automatic request/response examples
- ✅ Try out endpoints directly from browser
- ✅ See all available parameters and schemas

### Alternative Documentation
```
http://localhost:8000/redoc
```

---

## 📝 Configuration

The server is using:
- **Model:** `eleven_v3` (v3 with audio tags support)
- **Audio Tags:** Enabled
- **HOST Voice:** `XA2bIQ92TabjGbpO2xRr`
- **EXPERT Voice:** `PoHUWWWMHFrA8z7Q88pu`
- **Audio Storage:** `./audio_files/`

---

## 🔧 Common Operations

### 1. Search and Ingest a Paper
```bash
# Step 1: Search
curl -X POST http://localhost:8000/api/v1/papers/search \
  -H "Content-Type: application/json" \
  -d '{"query": "attention mechanism", "max_results": 1}'

# Step 2: Get the arxiv_id from response
# Step 3: Ingest
curl -X POST http://localhost:8000/api/v1/papers/ingest \
  -H "Content-Type: application/json" \
  -d '{"arxiv_id": "2301.00001"}'
```

### 2. Generate a Podcast
```bash
# Get paper_id from previous step
curl -X POST http://localhost:8000/api/v1/podcasts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "paper_ids": ["paper-uuid"],
    "topic": "Attention Mechanisms",
    "difficulty_level": "intermediate"
  }'
```

### 3. Poll for Completion
```bash
# Keep checking status
curl http://localhost:8000/api/v1/podcasts/{podcast_id}

# When status is "ready", get audio
curl http://localhost:8000/api/v1/podcasts/{podcast_id}/audio > podcast.mp3
```

---

## 🛠️ Server Management

### Check Server Logs
The server terminal is running and logging to:
```
C:\Users\param\.cursor\projects\e-Hackathon-odask-haihackaton\terminals\564481.txt
```

### Stop Server
Press `CTRL+C` in the terminal where the server is running, or:
```bash
# Find and kill the process
taskkill /F /PID <process_id>
```

### Restart Server
```bash
cd e:\Hackathon\odask\haihackaton\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📚 API Documentation

**Full API specification available at:**
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- ReDoc: http://localhost:8000/redoc

**Additional docs:**
- `backend/API_DOCS.md` - Detailed API documentation
- `backend/api-spec.json` - OpenAPI specification

---

## ✅ Server is Ready!

Your PodAsk API is now running with:
- ✅ v3 audio model with audio tags
- ✅ Gemini integration for script generation
- ✅ ElevenLabs TTS with HOST & EXPERT voices
- ✅ ArXiv paper ingestion
- ✅ Async podcast generation
- ✅ Interactive Q&A support

**Start testing at:** http://localhost:8000/docs 🚀
