from __future__ import annotations
import os
import uuid
from pathlib import Path
from typing import Optional
from elevenlabs import ElevenLabs
from app.config import get_settings


class ElevenLabsService:
    _client: Optional[ElevenLabs] = None

    @property
    def client(self) -> ElevenLabs:
        """Lazy-load ElevenLabs client."""
        if self._client is None:
            settings = get_settings()
            if not settings.elevenlabs_api_key:
                raise RuntimeError("ElevenLabs API key not configured")
            self._client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        return self._client

    def _get_audio_path(self, filename: str) -> Path:
        """Get full path for audio file."""
        settings = get_settings()
        audio_dir = Path(settings.audio_storage_path)
        audio_dir.mkdir(parents=True, exist_ok=True)
        return audio_dir / filename

    async def text_to_speech(
        self,
        text: str,
        voice_id: str,
        filename: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> str:
        """
        Convert text to speech and save to file.
        
        Supports v3 audio tags in square brackets:
        - Breath & pauses: [inhales], [exhales], [short pause], [long pause]
        - Reactions: [sighs], [gasps], [gulps], [clears throat], [coughs]
        - Laughter: [laughs], [chuckles], [giggles], [snorts]
        - Voice delivery: [whispers], [shouts], [stammers]
        - Emotion: [thoughtful], [confused], [nervous], [relieved], [sarcastic]
        
        Note: If audio tags are being spoken as words instead of performed,
        set ENABLE_AUDIO_TAGS=False in .env to strip them out.
        """
        if not filename:
            filename = f"{uuid.uuid4()}.mp3"

        audio_path = self._get_audio_path(filename)

        # Use configured model or provided override
        settings = get_settings()
        if model_id is None:
            model_id = settings.elevenlabs_model_id
        
        # Strip audio tags if they're not working properly
        if not settings.enable_audio_tags:
            import re
            text = re.sub(r'\[.*?\]', '', text)  # Remove all [tags]
            text = re.sub(r'\s+', ' ', text).strip()  # Clean up extra spaces
        
        # For v3 audio tags, use eleven_v3 or eleven_ttv_v3 (actual v3 models)
        # Note: Some voices may not support all audio tags perfectly
        # If tags are being spoken instead of performed, try:
        # 1. Use eleven_v3 (main v3 model with best audio tag support)
        # 2. Use eleven_ttv_v3 (alternative v3 model)
        # 3. Check if your API tier has v3 access
        # 4. Test with different voices from your account

        # Generate audio with v3 support
        audio = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format="mp3_44100_128"
        )

        # Save to file
        with open(audio_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        return str(audio_path)

    async def generate_segment_audio(
        self,
        dialogue: list[dict],
        segment_id: str
    ) -> str:
        """Generate audio for a full segment dialogue."""
        settings = get_settings()

        # Generate audio for each line and combine
        audio_files = []

        for i, line in enumerate(dialogue):
            speaker = line.get("speaker", "host")
            text = line.get("text", "")

            if not text:
                continue

            # Get voice ID based on speaker
            if speaker == "host":
                voice_id = settings.elevenlabs_host_voice_id
            else:
                voice_id = settings.elevenlabs_expert_voice_id

            filename = f"{segment_id}_line_{i}.mp3"
            audio_path = await self.text_to_speech(text, voice_id, filename)
            audio_files.append(audio_path)

        # For MVP, return the first audio file path
        # TODO: Combine audio files into single segment audio
        if audio_files:
            return audio_files[0]
        return ""

    async def generate_host_audio(self, text: str, filename: Optional[str] = None) -> str:
        """Generate audio with HOST voice."""
        settings = get_settings()
        return await self.text_to_speech(text, settings.elevenlabs_host_voice_id, filename)

    async def generate_expert_audio(self, text: str, filename: Optional[str] = None) -> str:
        """Generate audio with EXPERT voice."""
        settings = get_settings()
        return await self.text_to_speech(text, settings.elevenlabs_expert_voice_id, filename)

    async def speech_to_text(self, audio_path: str) -> str:
        """Transcribe audio to text using ElevenLabs."""
        with open(audio_path, "rb") as audio_file:
            transcription = self.client.speech_to_text.convert(
                audio=audio_file,
                model_id="scribe_v1"
            )
        return transcription.text

    @staticmethod
    def add_audio_tag(text: str, tag: str) -> str:
        """
        Add an audio tag to text for v3 TTS.
        
        Examples:
            add_audio_tag("Let me think about that", "thoughtful")
            -> "[thoughtful] Let me think about that"
            
            add_audio_tag("Really?", "surprised")
            -> "[surprised] Really?"
        """
        return f"[{tag}] {text}"

    @staticmethod
    def wrap_with_pause(text: str, pause_type: str = "short pause") -> str:
        """
        Wrap text with pauses for natural pacing.
        
        Args:
            text: The text to wrap
            pause_type: "short pause" or "long pause"
            
        Example:
            wrap_with_pause("This is important", "short pause")
            -> "[short pause] This is important [short pause]"
        """
        return f"[{pause_type}] {text} [{pause_type}]"


elevenlabs_service = ElevenLabsService()
