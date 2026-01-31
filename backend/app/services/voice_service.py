"""
Voice Service
Manages voice selection for podcasts - picks consistent voices per session
"""

import random
from dataclasses import dataclass
from enum import Enum


class VoiceGender(Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class VoiceConfig:
    voice_id: str
    gender: VoiceGender
    role: str  # "host" or "expert"


# Available voices from ElevenLabs
VOICES = {
    "female_hosts": [
        "EST9Ui6982FZPSi7gCHi",
        "uYXf8XasLslADfZ2MB4u",
        "kdmDKE6EkgrWrrykO9Qt",
        "yM93hbw8Qtvdma2wCnJG",
        "aMSt68OGf4xUZAnLpTU8",
    ],
    "female_experts": [
        "PoHUWWWMHFrA8z7Q88pu",
        "P7x743VjyZEOihNNygQ9",
        "MClEFoImJXBTgLwdLI5n",
        "aTxZrSrp47xsP6Ot4Kgd",
        "gJx1vCzNCD1EQHT212Ls",
    ],
    "male_hosts": [
        "XA2bIQ92TabjGbpO2xRr",
        "DMyrgzQFny3JI1Y1paM5",
        "scOwDtmlUjD3prqpp97I",
        "f5HLTX707KIM4SzJYzSz",
        "1t1EeRixsJrKbiF1zwM6",
    ],
    "male_experts": [
        "c6SfcYrb2t09NHXiT80T",
        "kdVjFjOXaqExaDvXZECX",
        "ZauUyVXAz5znrgRuElJ5",
        "RPEIZnKMqlQiZyZd1Dae",
        "EOVAuWqgSZN2Oel78Psj",
    ],
}


class VoiceService:
    """Service for selecting and managing podcast voices"""
    
    def __init__(self):
        # Cache selected voices per session
        self._session_voices: dict[str, dict[str, str]] = {}
    
    def select_voices_for_session(
        self,
        session_id: str,
        host_gender: VoiceGender | str = None,
        expert_gender: VoiceGender | str = None,
        host_voice_id: str = None,
        expert_voice_id: str = None
    ) -> dict[str, str]:
        """
        Select voices for a podcast session.
        If specific voice IDs are provided, use those.
        Otherwise, randomly select based on gender (or random gender if not specified).
        
        Returns dict with 'host' and 'expert' voice IDs.
        """
        # Convert string to enum if needed
        if isinstance(host_gender, str):
            host_gender = VoiceGender(host_gender.lower())
        if isinstance(expert_gender, str):
            expert_gender = VoiceGender(expert_gender.lower())
        
        # Select host voice
        if host_voice_id:
            host = host_voice_id
        else:
            if host_gender is None:
                host_gender = random.choice([VoiceGender.MALE, VoiceGender.FEMALE])
            
            host_pool = (
                VOICES["female_hosts"] 
                if host_gender == VoiceGender.FEMALE 
                else VOICES["male_hosts"]
            )
            host = random.choice(host_pool)
        
        # Select expert voice
        if expert_voice_id:
            expert = expert_voice_id
        else:
            if expert_gender is None:
                expert_gender = random.choice([VoiceGender.MALE, VoiceGender.FEMALE])
            
            expert_pool = (
                VOICES["female_experts"]
                if expert_gender == VoiceGender.FEMALE
                else VOICES["male_experts"]
            )
            expert = random.choice(expert_pool)
        
        # Cache for this session
        voices = {"host": host, "expert": expert}
        self._session_voices[session_id] = voices
        
        return voices
    
    def get_session_voices(self, session_id: str) -> dict[str, str] | None:
        """Get the voices assigned to a session"""
        return self._session_voices.get(session_id)
    
    def get_voice_for_speaker(self, session_id: str, speaker: str) -> str | None:
        """Get the voice ID for a specific speaker in a session"""
        voices = self.get_session_voices(session_id)
        if voices:
            return voices.get(speaker)
        return None
    
    def get_all_voices(self) -> dict:
        """Get all available voices organized by category"""
        return VOICES
    
    def clear_session(self, session_id: str):
        """Remove cached voices for a session"""
        if session_id in self._session_voices:
            del self._session_voices[session_id]


# Singleton instance
voice_service = VoiceService()
