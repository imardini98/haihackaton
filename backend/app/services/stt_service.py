"""
Speech-to-Text Service using Faster Whisper
Transcribes user voice questions for the "Raise Hand" feature
"""

from faster_whisper import WhisperModel
from pathlib import Path
from app.config import get_settings


class STTService:
    def __init__(self):
        self._model = None
    
    @property
    def model(self):
        """Lazy load Whisper model to avoid startup delay."""
        if self._model is None:
            settings = get_settings()
            self._model = WhisperModel(
                settings.whisper_model,
                device="cpu",
                compute_type="int8"
            )
        return self._model
    
    def transcribe(self, audio_path: Path | str) -> dict:
        """
        Transcribe audio file to text.
        
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
        
        segments, info = self.model.transcribe(
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
stt_service = STTService()
