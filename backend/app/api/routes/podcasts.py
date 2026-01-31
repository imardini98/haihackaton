"""
Podcasts API Routes
Matches CLAUDE.md spec for /api/v1/podcasts endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.config import get_settings
from app.models.podcast import Podcast
from app.services.segment_manager import segment_manager
from app.services.voice_service import voice_service


router = APIRouter(prefix="/podcasts", tags=["Podcasts"])


# ============== Request/Response Models ==============

class GeneratePodcastRequest(BaseModel):
    paper_ids: list[str]
    title: str | None = None
    host_gender: str | None = None
    expert_gender: str | None = None


class PodcastResponse(BaseModel):
    id: str
    title: str
    summary: str | None = None
    total_segments: int
    status: str
    voices: dict | None = None


class PodcastListResponse(BaseModel):
    podcasts: list[PodcastResponse]
    total: int


# ============== Endpoints ==============

@router.get("", response_model=PodcastListResponse)
async def list_podcasts(skip: int = 0, limit: int = 10):
    """
    List all generated podcasts.
    
    CLAUDE.md spec: GET /api/v1/podcasts
    """
    # TODO: Query from database
    raise HTTPException(status_code=501, detail="Database query not yet implemented")


@router.post("/generate")
async def generate_podcast(request: GeneratePodcastRequest):
    """
    Generate new podcast from papers.
    
    CLAUDE.md spec: POST /api/v1/podcasts/generate
    This is an async job - returns job ID for polling.
    """
    # TODO: Implement async job queue
    # 1. Fetch papers from database
    # 2. Send to Gemini service for script generation
    # 3. Generate audio with ElevenLabs
    # 4. Store in database
    raise HTTPException(status_code=501, detail="Gemini integration not yet implemented")


@router.get("/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(podcast_id: str):
    """
    Get podcast details.
    
    CLAUDE.md spec: GET /api/v1/podcasts/{id}
    """
    # TODO: Query from database
    raise HTTPException(status_code=501, detail="Database query not yet implemented")


@router.get("/{podcast_id}/audio")
async def stream_podcast_audio(podcast_id: str):
    """
    Stream podcast audio.
    
    CLAUDE.md spec: GET /api/v1/podcasts/{id}/audio
    Returns full podcast audio file or streaming response.
    """
    # TODO: Implement audio streaming
    raise HTTPException(status_code=501, detail="Audio streaming not yet implemented")


@router.get("/{podcast_id}/transcript")
async def get_podcast_transcript(podcast_id: str):
    """
    Get full transcript (dialogue format).
    
    CLAUDE.md spec: GET /api/v1/podcasts/{id}/transcript
    Returns the script in dialogue format (HOST + EXPERT).
    """
    # TODO: Query from database
    raise HTTPException(status_code=501, detail="Database query not yet implemented")


@router.delete("/{podcast_id}")
async def delete_podcast(podcast_id: str):
    """
    Remove podcast.
    
    CLAUDE.md spec: DELETE /api/v1/podcasts/{id}
    """
    # TODO: Delete from database and remove audio files
    raise HTTPException(status_code=501, detail="Delete not yet implemented")


# ============== Temporary Session-Based Endpoints ==============
# These match our current implementation for testing

@router.post("/session", response_model=PodcastResponse)
async def create_session(podcast: Podcast, host_gender: str | None = None, expert_gender: str | None = None):
    """
    Create a podcast session (temporary - for testing without database).
    This will be replaced by /generate once Gemini + database are integrated.
    """
    try:
        session = segment_manager.create_session(podcast)
        
        # Select voices
        voices = voice_service.select_voices_for_session(
            session_id=session.session_id,
            host_gender=host_gender,
            expert_gender=expert_gender
        )
        
        return PodcastResponse(
            id=session.session_id,
            title=session.podcast.metadata.title,
            summary=session.podcast.metadata.summary,
            total_segments=len(session.podcast.segments),
            status="ready",
            voices=voices
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """Get current session state (temporary)"""
    try:
        state = segment_manager.get_session_state(session_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/session/{session_id}/start")
async def start_segment(session_id: str):
    """Start playing current segment (temporary)"""
    try:
        result = segment_manager.start_segment(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/session/{session_id}/voices")
async def get_session_voices(session_id: str):
    """Get session voices (temporary)"""
    voices = voice_service.get_session_voices(session_id)
    if not voices:
        raise HTTPException(status_code=404, detail="Session not found or no voices assigned")
    return voices


@router.post("/session/{session_id}/generate-segment-audio/{segment_id}")
async def generate_segment_audio(session_id: str, segment_id: int):
    """Generate audio for a segment (temporary)"""
    session = segment_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Find segment
    segment = None
    for seg in session.podcast.segments:
        if seg.id == segment_id:
            segment = seg
            break
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    # Get session voices
    voices = voice_service.get_session_voices(session_id)
    if not voices:
        raise HTTPException(status_code=400, detail="No voices configured for session")
    
    from app.services.elevenlabs_service import elevenlabs_service
    audio_files = []
    
    for i, line in enumerate(segment.dialogue):
        try:
            voice_id = voices["host"] if line.speaker == "host" else voices["expert"]
            audio_path = elevenlabs_service.generate_audio(
                text=line.text,
                voice_id=voice_id,
                filename=f"seg_{segment_id}_line_{i}.mp3"
            )
            audio_files.append({
                "speaker": line.speaker,
                "text": line.text,
                "audio_url": f"/api/v1/audio/{audio_path.name}"
            })
        except Exception as e:
            audio_files.append({
                "speaker": line.speaker,
                "text": line.text,
                "audio_url": None,
                "error": str(e)
            })
    
    return {
        "segment_id": segment_id,
        "topic_label": segment.topic_label,
        "voices": voices,
        "audio_files": audio_files
    }
