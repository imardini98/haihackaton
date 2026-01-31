"""
Audio Pipeline API Routes
Handles TTS (podcast generation) and STT (raise hand transcription)
"""

import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings
from app.services.tts_service import tts_service
from app.services.stt_service import stt_service


router = APIRouter(prefix="/audio", tags=["Audio Pipeline"])


# ============== Request/Response Models ==============

class TextToSpeechRequest(BaseModel):
    text: str
    voice_id: str | None = None
    segment_id: str | None = None


class TextToSpeechResponse(BaseModel):
    audio_url: str
    filename: str
    segment_id: str


class TranscriptionResponse(BaseModel):
    text: str
    language: str | None = None


class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    category: str | None = None
    description: str | None = None


# ============== TTS Endpoints ==============

@router.post("/tts", response_model=TextToSpeechResponse)
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech using ElevenLabs.
    
    Use this to generate podcast audio from synthesized paper content.
    """
    try:
        segment_id = request.segment_id or str(uuid.uuid4())[:8]
        
        audio_path = tts_service.generate_podcast_segment(
            content=request.text,
            segment_id=segment_id,
            voice_id=request.voice_id
        )
        
        return TextToSpeechResponse(
            audio_url=f"/audio/files/{audio_path.name}",
            filename=audio_path.name,
            segment_id=segment_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.get("/files/{filename}")
async def get_audio_file(filename: str):
    """
    Retrieve a generated audio file.
    """
    file_path = settings.AUDIO_OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )


@router.get("/voices", response_model=list[VoiceInfo])
async def list_voices():
    """
    Get available ElevenLabs voices.
    """
    try:
        voices = tts_service.get_available_voices()
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {str(e)}")


# ============== STT Endpoints ==============

@router.post("/stt", response_model=TranscriptionResponse)
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using Whisper.
    
    Use this for the "Raise Hand" feature to convert user questions to text.
    Accepts audio files (mp3, wav, m4a, webm).
    """
    # Validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/webm", "audio/x-m4a"]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio type. Allowed: {allowed_types}"
        )
    
    # Save uploaded file temporarily
    temp_filename = f"temp_{uuid.uuid4()}{Path(audio.filename).suffix}"
    temp_path = settings.AUDIO_OUTPUT_DIR / temp_filename
    
    try:
        # Write uploaded file
        async with aiofiles.open(temp_path, "wb") as f:
            content = await audio.read()
            await f.write(content)
        
        # Transcribe
        result = stt_service.transcribe(temp_path)
        
        return TranscriptionResponse(
            text=result["text"],
            language=result["language"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


@router.post("/raise-hand", response_model=TranscriptionResponse)
async def raise_hand(audio: UploadFile = File(...)):
    """
    "Raise Hand" endpoint - Transcribe a user's spoken question.
    
    This is the core interaction point for the MVP:
    1. User pauses podcast and speaks their question
    2. Audio is sent here for transcription
    3. Transcribed text is returned for LLM processing
    """
    return await speech_to_text(audio)
