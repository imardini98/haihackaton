"""
Podcast Session and Segment API Routes
Handles podcast playback, hand raising, and Q&A flow
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.models.podcast import Podcast, DialogueLine
from app.services.segment_manager import segment_manager
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service
from app.services.voice_service import voice_service, VOICES
from app.config import get_settings

import uuid
import aiofiles
from pathlib import Path


router = APIRouter(prefix="/podcast", tags=["Podcast Sessions"])


# ============== Request/Response Models ==============

class CreateSessionRequest(BaseModel):
    podcast: Podcast
    # Optional voice preferences
    host_gender: str | None = None  # "male" or "female"
    expert_gender: str | None = None  # "male" or "female"
    host_voice_id: str | None = None  # Specific voice ID override
    expert_voice_id: str | None = None  # Specific voice ID override


class CreateSessionResponse(BaseModel):
    session_id: str
    podcast_title: str
    total_segments: int
    voices: dict  # Selected voice IDs for this session


class RaiseHandRequest(BaseModel):
    question: str


class RaiseHandAudioResponse(BaseModel):
    status: str
    transition_phrase: str
    segment_transition: str
    user_question: str
    qa_segment_id: str
    # Audio URLs for the transition phrases
    transition_audio_url: str | None = None


class AnswerRequest(BaseModel):
    answer_dialogue: list[dict]


class SkipRequest(BaseModel):
    segment_id: int


# ============== Session Management ==============

@router.post("/session", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new podcast listening session.
    Load the podcast data and initialize playback state.
    Selects consistent voices for host and expert.
    """
    try:
        session = segment_manager.create_session(request.podcast)
        
        # Select voices for this session
        voices = voice_service.select_voices_for_session(
            session_id=session.session_id,
            host_gender=request.host_gender,
            expert_gender=request.expert_gender,
            host_voice_id=request.host_voice_id,
            expert_voice_id=request.expert_voice_id
        )
        
        return CreateSessionResponse(
            session_id=session.session_id,
            podcast_title=session.podcast.metadata.title,
            total_segments=len(session.podcast.segments),
            voices=voices
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get current session state"""
    try:
        state = segment_manager.get_session_state(session_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/session/{session_id}/start")
async def start_segment(session_id: str):
    """
    Start playing the current segment.
    Returns segment data and whether it can be interrupted.
    """
    try:
        result = segment_manager.start_segment(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Hand Raise / Q&A Flow ==============

@router.post("/session/{session_id}/raise-hand")
async def raise_hand_text(session_id: str, request: RaiseHandRequest):
    """
    Raise hand with a text question.
    Pauses podcast and enters Q&A mode.
    """
    try:
        result = segment_manager.raise_hand(session_id, request.question)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/session/{session_id}/raise-hand-audio")
async def raise_hand_audio(session_id: str, audio: UploadFile = File(...)):
    """
    Raise hand with audio question.
    Transcribes the audio, then enters Q&A mode.
    Also generates audio for the transition phrase.
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
        
        # Transcribe the question
        transcription = stt_service.transcribe(temp_path)
        user_question = transcription["text"]
        
        # Raise hand with transcribed question
        result = segment_manager.raise_hand(session_id, user_question)
        
        if result["status"] == "not_interruptible":
            return result
        
        # Generate audio for the transition phrase (use host voice)
        transition_audio = None
        try:
            transition_text = result["transition_phrase"]
            host_voice = voice_service.get_voice_for_speaker(session_id, "host")
            audio_path = tts_service.generate_audio(
                text=transition_text,
                voice_id=host_voice,
                filename=f"transition_{result['qa_segment_id']}.mp3"
            )
            transition_audio = f"/audio/files/{audio_path.name}"
        except Exception:
            # TTS failed, continue without audio
            pass
        
        return RaiseHandAudioResponse(
            status=result["status"],
            transition_phrase=result["transition_phrase"],
            segment_transition=result["segment_transition"],
            user_question=result["user_question"],
            qa_segment_id=result["qa_segment_id"],
            transition_audio_url=transition_audio
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


@router.post("/session/{session_id}/clarify")
async def request_clarification(session_id: str):
    """
    AI requests clarification for an unclear question.
    Returns a natural prompt asking for more details.
    """
    try:
        result = segment_manager.request_clarification(session_id)
        
        # Generate audio for clarification prompt (use host voice)
        try:
            host_voice = voice_service.get_voice_for_speaker(session_id, "host")
            audio_path = tts_service.generate_audio(
                text=result["clarification_prompt"],
                voice_id=host_voice,
                filename=f"clarify_{session_id}_{uuid.uuid4().hex[:8]}.mp3"
            )
            result["clarification_audio_url"] = f"/audio/files/{audio_path.name}"
        except Exception:
            result["clarification_audio_url"] = None
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/session/{session_id}/answer")
async def provide_answer(session_id: str, request: AnswerRequest):
    """
    Provide the answer dialogue for the current Q&A.
    The dialogue will be spoken by host/expert voices.
    """
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
                    "audio_url": f"/audio/files/{audio_path.name}"
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


@router.post("/session/{session_id}/resume")
async def resume_podcast(session_id: str):
    """
    Resume the podcast after Q&A is complete.
    Moves to the next segment with a natural transition.
    """
    try:
        result = segment_manager.resume_podcast(session_id)
        
        # Generate audio for resume phrase (use host voice)
        try:
            host_voice = voice_service.get_voice_for_speaker(session_id, "host")
            resume_text = f"{result['natural_transition']} {result['resume_phrase']}"
            audio_path = tts_service.generate_audio(
                text=resume_text,
                voice_id=host_voice,
                filename=f"resume_{session_id}_{uuid.uuid4().hex[:8]}.mp3"
            )
            result["resume_audio_url"] = f"/audio/files/{audio_path.name}"
        except Exception:
            result["resume_audio_url"] = None
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/session/{session_id}/skip")
async def skip_to_segment(session_id: str, request: SkipRequest):
    """Skip to a specific segment by ID"""
    try:
        result = segment_manager.skip_to_segment(session_id, request.segment_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== Segment Audio Generation ==============

@router.post("/session/{session_id}/generate-segment-audio/{segment_id}")
async def generate_segment_audio(session_id: str, segment_id: int):
    """
    Generate TTS audio for a specific segment's dialogue.
    Returns URLs to audio files for each dialogue line.
    Uses the session's assigned voices consistently.
    """
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
    
    audio_files = []
    
    for i, line in enumerate(segment.dialogue):
        try:
            voice_id = voices["host"] if line.speaker == "host" else voices["expert"]
            audio_path = tts_service.generate_audio(
                text=line.text,
                voice_id=voice_id,
                filename=f"seg_{segment_id}_line_{i}.mp3"
            )
            audio_files.append({
                "speaker": line.speaker,
                "text": line.text,
                "audio_url": f"/audio/files/{audio_path.name}"
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


# ============== Voice Management ==============

@router.get("/voices")
async def get_available_voices():
    """
    Get all available voices organized by category.
    """
    return {
        "voices": VOICES,
        "categories": ["female_hosts", "female_experts", "male_hosts", "male_experts"]
    }


@router.get("/session/{session_id}/voices")
async def get_session_voices(session_id: str):
    """
    Get the voices assigned to a specific session.
    """
    voices = voice_service.get_session_voices(session_id)
    if not voices:
        raise HTTPException(status_code=404, detail="Session not found or no voices assigned")
    return voices
