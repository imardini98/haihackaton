"""
Text-to-Speech Service using ElevenLabs API
Supports both file generation and streaming
"""

import uuid
from pathlib import Path
from typing import Generator
from elevenlabs import ElevenLabs, VoiceSettings
from app.config import get_settings


class TTSService:
    def __init__(self):
        settings = get_settings()
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.output_dir = settings.audio_output_path
    
    def generate_audio(
        self,
        text: str,
        voice_id: str | None = None,
        filename: str | None = None
    ) -> Path:
        """
        Generate audio from text and save to file.
        
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
    
    def stream_audio(
        self,
        text: str,
        voice_id: str | None = None
    ) -> Generator[bytes, None, None]:
        """
        Stream audio from text using ElevenLabs streaming API.
        Returns a generator that yields audio chunks.
        
        Args:
            text: The text to convert to speech
            voice_id: ElevenLabs voice ID
        
        Yields:
            Audio bytes chunks (MP3 format)
        """
        settings = get_settings()
        voice_id = voice_id or settings.default_voice_id
        
        # Use streaming endpoint
        audio_stream = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )
        
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                yield chunk
    
    def generate_podcast_segment(
        self,
        content: str,
        segment_id: str,
        voice_id: str | None = None
    ) -> Path:
        """Generate a podcast segment with proper naming."""
        filename = f"podcast_{segment_id}.mp3"
        return self.generate_audio(text=content, voice_id=voice_id, filename=filename)
    
    def get_available_voices(self) -> list[dict]:
        """Get list of available voices from ElevenLabs."""
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
