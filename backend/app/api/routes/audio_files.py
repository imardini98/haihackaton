"""
Audio file serving endpoint
Matches CLAUDE.md pattern for audio file access
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import get_settings
from app.services.elevenlabs_service import elevenlabs_service


router = APIRouter(prefix="/audio", tags=["Audio Files"])


class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    category: str | None = None
    description: str | None = None


@router.get("/{filename}")
async def get_audio_file(filename: str):
    """
    Retrieve a generated audio file.
    Serves files from audio storage directory.
    """
    settings = get_settings()
    file_path = settings.audio_output_path / filename
    
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
        voices = elevenlabs_service.get_available_voices()
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {str(e)}")
