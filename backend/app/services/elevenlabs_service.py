from __future__ import annotations
import os
import uuid
from pathlib import Path
from typing import Optional, List
from elevenlabs import ElevenLabs
from pydub import AudioSegment
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
        """Generate audio for a full segment dialogue with both host and expert voices."""
        settings = get_settings()

        # Debug: log dialogue structure
        print(f"[TTS] Generating audio for segment {segment_id}")
        print(f"[TTS] Dialogue has {len(dialogue)} lines")
        for i, line in enumerate(dialogue):
            print(f"[TTS] Line {i}: speaker={line.get('speaker', 'MISSING')}, text={line.get('text', '')[:50]}...")

        # Generate audio for each line
        audio_files: List[str] = []

        for i, line in enumerate(dialogue):
            speaker = line.get("speaker", "host").lower().strip()
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

        if not audio_files:
            return ""

        # If only one file, return it directly
        if len(audio_files) == 1:
            return audio_files[0]

        # Combine all audio files into a single segment
        combined = AudioSegment.empty()

        # Small pause between speakers (300ms)
        pause = AudioSegment.silent(duration=300)

        for i, audio_path in enumerate(audio_files):
            segment = AudioSegment.from_mp3(audio_path)
            if i > 0:
                combined += pause
            combined += segment

        # Export combined audio
        combined_filename = f"{segment_id}_combined.mp3"
        combined_path = self._get_audio_path(combined_filename)
        combined.export(str(combined_path), format="mp3")

        # Clean up individual line files
        for audio_path in audio_files:
            try:
                os.remove(audio_path)
            except OSError:
                pass

        return str(combined_path)

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
