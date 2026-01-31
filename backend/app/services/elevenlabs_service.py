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
        filename: Optional[str] = None
    ) -> str:
        """Convert text to speech and save to file."""
        if not filename:
            filename = f"{uuid.uuid4()}.mp3"

        audio_path = self._get_audio_path(filename)

        # Generate audio
        audio = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2"
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


elevenlabs_service = ElevenLabsService()
