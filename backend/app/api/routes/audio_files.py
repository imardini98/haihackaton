"""
Audio file serving and streaming endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.config import get_settings
from app.services.tts_service import tts_service


router = APIRouter(prefix="/audio", tags=["Audio"])


class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    category: str | None = None
    description: str | None = None


class TTSRequest(BaseModel):
    text: str
    voice_id: str | None = None


@router.get("/voices", response_model=list[VoiceInfo])
async def list_voices():
    """Get available ElevenLabs voices."""
    try:
        voices = tts_service.get_available_voices()
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {str(e)}")


@router.post("/stream")
async def stream_tts(request: TTSRequest):
    """
    Stream TTS audio directly to the client.
    Uses ElevenLabs streaming for immediate playback.
    """
    try:
        def audio_generator():
            for chunk in tts_service.stream_audio(request.text, request.voice_id):
                yield chunk
        
        return StreamingResponse(
            audio_generator(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "no-cache",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS streaming failed: {str(e)}")


@router.get("/stream")
async def stream_tts_get(text: str = Query(...), voice_id: str = Query(None)):
    """
    Stream TTS audio via GET request (for direct <audio src="..."> usage).
    """
    try:
        def audio_generator():
            for chunk in tts_service.stream_audio(text, voice_id):
                yield chunk
        
        return StreamingResponse(
            audio_generator(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "no-cache",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS streaming failed: {str(e)}")


@router.get("/{filename}")
async def get_audio_file(filename: str):
    """Retrieve a generated audio file."""
    settings = get_settings()
    file_path = settings.audio_output_path / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )
