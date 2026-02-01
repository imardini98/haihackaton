from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
import json

# Find .env file - check multiple locations
def _find_env_file() -> str:
    """Find .env file in backend directory or current directory."""
    # Check backend directory (where config.py is located)
    backend_env = Path(__file__).parent.parent / ".env"
    if backend_env.exists():
        return str(backend_env.resolve())
    
    # Check current working directory
    cwd_env = Path(".env")
    if cwd_env.exists():
        return str(cwd_env.resolve())
    
    # Check root directory (parent of backend)
    root_env = Path(__file__).parent.parent.parent / ".env"
    if root_env.exists():
        return str(root_env.resolve())
    
    # Default to .env (will use environment variables if file doesn't exist)
    return ".env"


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

    # App Config
    app_env: str = "development"
    debug: bool = True
    cors_origins: str = '["http://localhost:3000","http://localhost:5173"]'
    auth_enabled: bool = False  # Set to True to require auth on endpoints

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

    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
