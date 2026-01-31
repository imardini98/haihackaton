"""
Text-to-Speech Service using ElevenLabs API
Converts text content into high-quality podcast audio
"""

import uuid
from pathlib import Path
from elevenlabs import ElevenLabs, VoiceSettings
from app.config import settings


class TTSService:
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.output_dir = settings.AUDIO_OUTPUT_DIR
    
    def generate_audio(
        self,
        text: str,
        voice_id: str | None = None,
        filename: str | None = None
    ) -> Path:
        """
        Generate audio from text using ElevenLabs.
        
        Args:
            text: The text to convert to speech
            voice_id: ElevenLabs voice ID (uses default if not provided)
            filename: Output filename (generates UUID if not provided)
        
        Returns:
            Path to the generated audio file
        """
        settings = get_settings()
        voice_id = voice_id or settings.default_voice_id
        filename = filename or f"{uuid.uuid4()}.mp3"
        output_path = self.output_dir / filename
        
        # Generate audio with ElevenLabs
        audio_generator = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )
        
        # Write audio bytes to file
        with open(output_path, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)
        
        return output_path
    
    def generate_podcast_segment(
        self,
        content: str,
        segment_id: str,
        voice_id: str | None = None
    ) -> Path:
        """
        Generate a podcast segment with proper naming.
        
        Args:
            content: The podcast script/content
            segment_id: Identifier for this segment
            voice_id: ElevenLabs voice ID
        
        Returns:
            Path to the generated audio file
        """
        filename = f"podcast_{segment_id}.mp3"
        return self.generate_audio(text=content, voice_id=voice_id, filename=filename)
    
    def get_available_voices(self) -> list[dict]:
        """
        Get list of available voices from ElevenLabs.
        
        Returns:
            List of voice information dictionaries
        """
        response = self.client.voices.get_all()
        return [
            {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category,
                "description": voice.description
            }
            for voice in response.voices
        ]


# Singleton instance
tts_service = TTSService()
