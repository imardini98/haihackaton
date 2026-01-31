from __future__ import annotations
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import json


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str = ""
    elevenlabs_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # ElevenLabs Voice Config
    elevenlabs_host_voice_id: str = ""
    elevenlabs_expert_voice_id: str = ""
    
    # Audio Pipeline Settings
    default_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    audio_output_dir: str = "./audio_output"
    whisper_model: str = "base"

    # App Config
    app_env: str = "development"
    debug: bool = True
    cors_origins: str = '["http://localhost:3000","http://localhost:5173"]'

    # Audio Config
    audio_storage_path: str = "./audio_files"
    max_question_duration_seconds: int = 30
    qa_silence_timeout_seconds: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return json.loads(self.cors_origins)

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"
    
    @property
    def audio_output_path(self) -> Path:
        """Get audio output directory as Path object"""
        path = Path(self.audio_output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()

# Backward compatibility alias
settings = get_settings()
