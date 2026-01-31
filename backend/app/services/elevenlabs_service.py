"""
ElevenLabs Service - Combined TTS + STT (CLAUDE.md naming)
This service combines Text-to-Speech and Speech-to-Text functionality.
"""

import uuid
from pathlib import Path
from elevenlabs import ElevenLabs, VoiceSettings
from faster_whisper import WhisperModel
from app.config import get_settings


class ElevenLabsService:
    """
    Combined TTS and STT service using ElevenLabs for TTS and Whisper for STT.
    Matches CLAUDE.md service naming convention.
    """
    
    def __init__(self):
        settings = get_settings()
        # TTS client
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.output_dir = settings.audio_output_path
        
        # STT model (lazy loaded)
        self._whisper_model = None
        self._whisper_model_name = settings.whisper_model
    
    # ============== TTS Methods ==============
    
    def generate_audio(
        self,
        text: str,
        voice_id: str | None = None,
        filename: str | None = None
    ) -> Path:
        """
        Generate audio from text using ElevenLabs TTS.
        
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
    
    # ============== STT Methods ==============
    
    @property
    def whisper_model(self):
        """Lazy load Whisper model to avoid startup delay."""
        if self._whisper_model is None:
            self._whisper_model = WhisperModel(
                self._whisper_model_name,
                device="cpu",
                compute_type="int8"
            )
        return self._whisper_model
    
    def transcribe(self, audio_path: Path | str) -> dict:
        """
        Transcribe audio file to text using Whisper STT.
        
        Args:
            audio_path: Path to the audio file
        
        Returns:
            Dictionary with transcription results including:
            - text: The transcribed text
            - language: Detected language
            - segments: Detailed segment information
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        segments, info = self.whisper_model.transcribe(
            str(audio_path),
            language=None,  # Auto-detect language
        )
        
        # Collect segments
        segment_list = []
        full_text = []
        for seg in segments:
            segment_list.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip()
            })
            full_text.append(seg.text.strip())
        
        return {
            "text": " ".join(full_text),
            "language": info.language,
            "segments": segment_list
        }
    
    def transcribe_question(self, audio_path: Path | str) -> str:
        """
        Simple transcription for user questions.
        Returns just the text for quick processing.
        
        Args:
            audio_path: Path to the audio file
        
        Returns:
            Transcribed text string
        """
        result = self.transcribe(audio_path)
        return result["text"]


# Singleton instance
elevenlabs_service = ElevenLabsService()

# Backward compatibility aliases
tts_service = elevenlabs_service  # TTS methods
stt_service = elevenlabs_service  # STT methods
