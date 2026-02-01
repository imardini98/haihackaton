"""
Interaction API Routes - "Raise Your Hand" Q&A functionality
Matches CLAUDE.md spec for /api/v1/interaction endpoints
"""

import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.config import get_settings
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service
from app.services.segment_manager import segment_manager
from app.services.voice_service import voice_service


router = APIRouter(prefix="/interaction", tags=["Interaction"])


# ============== Request/Response Models ==============

class AskTextRequest(BaseModel):
    session_id: str
    question: str


class TranscriptionResponse(BaseModel):
    question_text: str
    language: str | None = None


class AnswerResponse(BaseModel):
    answer_id: str
    host_acknowledgment: str
    expert_answer: str
    audio_url: str | None = None


class ContinueResponse(BaseModel):
    resume_phrase: str
    audio_url: str | None = None
    next_segment_id: int | None = None


class ProvideAnswerRequest(BaseModel):
    answer_dialogue: list[dict]


class SessionStartRequest(BaseModel):
    podcast_id: str
    user_id: str | None = None


class SessionUpdateRequest(BaseModel):
    current_segment_id: int
    position_seconds: float


# ============== Endpoints ==============

@router.post("/ask", response_model=TranscriptionResponse)
async def ask_voice_question(audio: UploadFile = File(...)):
    """
    Submit a voice question ("Raise Your Hand").
    
    CLAUDE.md spec: POST /api/v1/interaction/ask
    Accepts audio file, transcribes to text using Whisper STT.
    """
    # Validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/webm", "audio/x-m4a"]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio type. Allowed: {allowed_types}"
        )
    
    # Save uploaded file temporarily
    settings = get_settings()
    temp_filename = f"temp_{uuid.uuid4()}{Path(audio.filename).suffix}"
    temp_path = settings.audio_output_path / temp_filename
    
    try:
        # Write uploaded file
        async with aiofiles.open(temp_path, "wb") as f:
            content = await audio.read()
            await f.write(content)
        
        # Transcribe
        result = stt_service.transcribe(temp_path)
        
        return TranscriptionResponse(
            question_text=result["text"],
            language=result["language"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


@router.post("/ask-text", response_model=TranscriptionResponse)
async def ask_text_question(request: AskTextRequest):
    """
    Submit a text question.
    
    CLAUDE.md spec: POST /api/v1/interaction/ask-text
    """
    return TranscriptionResponse(
        question_text=request.question,
        language=None
    )


@router.get("/{interaction_id}/answer", response_model=AnswerResponse)
async def get_answer(interaction_id: str):
    """
    Get answer audio (HOST + EXPERT).
    
    CLAUDE.md spec: GET /api/v1/interaction/{id}/answer
    Placeholder - needs Gemini integration for real Q&A.
    """
    # TODO: Integrate with Gemini service for real answers
    raise HTTPException(status_code=501, detail="Gemini Q&A not yet implemented")


@router.post("/continue", response_model=ContinueResponse)
async def process_continue(session_id: str):
    """
    Process continue signal, get resume line.
    
    CLAUDE.md spec: POST /api/v1/interaction/continue
    User says "okay thanks" or similar, podcast resumes.
    """
    try:
        result = segment_manager.resume_podcast(session_id)
        
        # Generate audio for resume phrase
        audio_url = None
        try:
            host_voice = voice_service.get_voice_for_speaker(session_id, "host")
            resume_text = f"{result['natural_transition']} {result['resume_phrase']}"
            audio_path = tts_service.generate_audio(
                text=resume_text,
                voice_id=host_voice,
                filename=f"resume_{session_id}_{uuid.uuid4().hex[:8]}.mp3"
            )
            audio_url = f"/api/v1/audio/{audio_path.name}"
        except Exception:
            pass
        
        return ContinueResponse(
            resume_phrase=result.get("resume_phrase", ""),
            audio_url=audio_url,
            next_segment_id=result.get("next_segment", {}).get("id")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/session/start")
async def start_listening_session(request: SessionStartRequest):
    """
    Start a listening session.
    
    CLAUDE.md spec: POST /api/v1/interaction/session/start
    Tracks user's listening position for Q&A context.
    """
    # TODO: Implement session tracking in database
    raise HTTPException(status_code=501, detail="Session tracking not yet implemented")


@router.post("/session/update")
async def update_session_position(request: SessionUpdateRequest):
    """
    Update current position in podcast.
    
    CLAUDE.md spec: POST /api/v1/interaction/session/update
    """
    # TODO: Implement position tracking
    raise HTTPException(status_code=501, detail="Position tracking not yet implemented")


# ============== Temporary endpoints for existing functionality ==============

@router.post("/{session_id}/clarify")
async def request_clarification(session_id: str):
    """Request clarification (temporary)"""
    try:
        result = segment_manager.request_clarification(session_id)
        
        # Generate audio for clarification prompt
        audio_url = None
        try:
            host_voice = voice_service.get_voice_for_speaker(session_id, "host")
            audio_path = tts_service.generate_audio(
                text=result["clarification_prompt"],
                voice_id=host_voice,
                filename=f"clarify_{session_id}_{uuid.uuid4().hex[:8]}.mp3"
            )
            audio_url = f"/api/v1/audio/{audio_path.name}"
        except Exception:
            pass
        
        result["clarification_audio_url"] = audio_url
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{session_id}/answer")
async def provide_answer_temp(session_id: str, request: ProvideAnswerRequest):
    """Provide answer (temporary)"""
    try:
        result = segment_manager.provide_answer(session_id, request.answer_dialogue)
        
        # Get session voices
        voices = voice_service.get_session_voices(session_id)
        if not voices:
            raise ValueError("No voices configured for session")
        
        # Generate audio for each dialogue line
        audio_urls = []
        for i, line in enumerate(result["answer_dialogue"]):
            try:
                voice_id = voices["host"] if line["speaker"] == "host" else voices["expert"]
                audio_path = tts_service.generate_audio(
                    text=line["text"],
                    voice_id=voice_id,
                    filename=f"answer_{result['qa_segment_id']}_{i}.mp3"
                )
                audio_urls.append({
                    "speaker": line["speaker"],
                    "text": line["text"],
                    "audio_url": f"/api/v1/audio/{audio_path.name}"
                })
            except Exception:
                audio_urls.append({
                    "speaker": line["speaker"],
                    "text": line["text"],
                    "audio_url": None
                })
        
        result["audio_dialogue"] = audio_urls
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
