# PodAsk API Documentation

**Base URL:** `http://localhost:8000/api/v1`

**Interactive Docs:** `http://localhost:8000/docs`

---

## Authentication

All endpoints marked with a lock require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Auth

#### POST `/auth/signup`
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "user@example.com"
}
```

---

#### POST `/auth/signin`
Sign in an existing user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "user@example.com"
}
```

---

#### GET `/auth/me` (Auth Required)
Get current user profile.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com"
}
```

---

#### POST `/auth/password-reset`
Request a password reset email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If an account exists with this email, a password reset link has been sent."
}
```

---

#### POST `/auth/password-update` (Auth Required)
Update password (use access token from password reset email link).

**Request:**
```json
{
  "new_password": "newsecurepassword"
}
```

**Response:**
```json
{
  "message": "Password updated successfully."
}
```

---

### Papers

#### POST `/papers/search`
Search ArXiv for papers. **No auth required.**

**Request:**
```json
{
  "query": "machine learning",
  "max_results": 10,
  "sort_by": "submitted"
}
```

**Response:**
```json
[
  {
    "arxiv_id": "2401.12345",
    "title": "Paper Title",
    "authors": ["Author One", "Author Two"],
    "abstract": "Paper abstract...",
    "pdf_url": "https://arxiv.org/pdf/2401.12345",
    "published_date": "2024-01-15T00:00:00Z",
    "categories": ["cs.LG", "cs.AI"]
  }
]
```

---

#### POST `/papers/ingest` (Auth Required)
Ingest a paper from ArXiv and save to database.

**Request:**
```json
{
  "arxiv_id": "2401.12345"
}
```

**Response:**
```json
{
  "id": "uuid",
  "arxiv_id": "2401.12345",
  "title": "Paper Title",
  "authors": ["Author One"],
  "abstract": "...",
  "content": "...",
  "pdf_url": "https://...",
  "published_date": "2024-01-15T00:00:00Z",
  "categories": ["cs.LG"],
  "created_at": "2024-01-20T12:00:00Z"
}
```

---

#### GET `/papers` (Auth Required)
List all papers for the current user.

**Response:**
```json
{
  "papers": [...],
  "total": 5
}
```

---

#### GET `/papers/{paper_id}` (Auth Required)
Get a specific paper.

---

#### DELETE `/papers/{paper_id}` (Auth Required)
Delete a paper.

**Response:**
```json
{
  "status": "deleted"
}
```

---

### Podcasts

#### POST `/podcasts/generate` (Auth Required)
Start podcast generation from papers. Returns immediately, generation happens in background.

**Request:**
```json
{
  "paper_ids": ["uuid1", "uuid2"],
  "topic": "Machine Learning Advances",
  "difficulty_level": "intermediate"
}
```

`difficulty_level` options: `"beginner"`, `"intermediate"`, `"advanced"`

**Response:**
```json
{
  "id": "podcast-uuid",
  "title": "Generating...",
  "paper_ids": ["uuid1", "uuid2"],
  "status": "pending",
  "created_at": "2024-01-20T12:00:00Z",
  "segments": []
}
```

---

#### GET `/podcasts/{podcast_id}/status` (Auth Required)
Poll for generation status.

**Response:**
```json
{
  "id": "podcast-uuid",
  "status": "generating",
  "error_message": null
}
```

`status` values: `"pending"`, `"generating"`, `"ready"`, `"failed"`

---

#### GET `/podcasts` (Auth Required)
List all podcasts for the current user.

**Response:**
```json
{
  "podcasts": [...],
  "total": 3
}
```

---

#### GET `/podcasts/{podcast_id}` (Auth Required)
Get podcast with all segments.

**Response:**
```json
{
  "id": "podcast-uuid",
  "title": "ML Advances Podcast",
  "summary": "...",
  "topic": "Machine Learning",
  "paper_ids": ["uuid1"],
  "status": "ready",
  "total_duration_seconds": 300,
  "created_at": "...",
  "segments": [
    {
      "id": "segment-uuid",
      "sequence": 0,
      "topic_label": "Introduction",
      "dialogue": [
        {"speaker": "host", "text": "Welcome to..."},
        {"speaker": "expert", "text": "Thanks for having me..."}
      ],
      "key_terms": ["neural networks", "deep learning"],
      "audio_url": "/audio/segment-uuid.mp3",
      "duration_seconds": 45.5,
      "transition_to_question": "Any questions about this so far?",
      "resume_phrase": "Alright, let's continue..."
    }
  ]
}
```

---

#### GET `/podcasts/{podcast_id}/audio/{segment_sequence}` (Auth Required)
Stream audio for a specific segment.

**Response:** Audio file (MP3)

---

#### DELETE `/podcasts/{podcast_id}` (Auth Required)
Delete a podcast and its segments.

---

### Health

#### GET `/health`
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "podask-api"
}
```

---

#### GET `/health/services`
Check status of external services.

---

## Podcast Generation Flow

1. **Search papers:** `POST /papers/search` (find papers on ArXiv)
2. **Ingest papers:** `POST /papers/ingest` (save to your library)
3. **Generate podcast:** `POST /podcasts/generate` (starts async generation)
4. **Poll status:** `GET /podcasts/{id}/status` (wait for `"ready"`)
5. **Get podcast:** `GET /podcasts/{id}` (get full podcast with segments)
6. **Stream audio:** `GET /podcasts/{id}/audio/{sequence}` (play segment audio)

---

## Segment Structure

Each podcast is divided into segments. Each segment contains:

- **dialogue:** Array of `{speaker, text}` objects alternating between "host" and "expert"
- **transition_to_question:** Phrase played when user raises hand (after segment completes)
- **resume_phrase:** Phrase to resume podcast after Q&A ends
- **key_terms:** Important terms discussed in this segment

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing or invalid token)
- `404` - Not Found
- `422` - Validation Error (check request body)
- `500` - Internal Server Error

---

## OpenAPI Spec

Full OpenAPI 3.1 specification available at:
- JSON: `GET /openapi.json`
- Interactive: `GET /docs`
