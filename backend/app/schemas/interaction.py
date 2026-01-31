from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class SessionStartRequest(BaseModel):
    podcast_id: str
    segment_id: str


class SessionStartResponse(BaseModel):
    session_id: str
    podcast_id: str
    current_segment_id: str
    status: str


class SessionUpdateRequest(BaseModel):
    current_segment_id: str
    audio_timestamp: float = 0.0


class SessionUpdateResponse(BaseModel):
    session_id: str
    status: str


class AskTextRequest(BaseModel):
    session_id: str
    question: str
    audio_timestamp: float = 0.0


class AskResponse(BaseModel):
    exchange_id: str
    host_acknowledgment: str
    expert_answer: str
    host_audio_url: Optional[str] = None
    expert_audio_url: Optional[str] = None
    confidence: str = "medium"
    topics_discussed: list[str] = []


class ContinueRequest(BaseModel):
    session_id: str
    user_signal: str = "okay thanks"


class ContinueResponse(BaseModel):
    resume_line: str
    resume_audio_url: Optional[str] = None
    next_segment_id: Optional[str] = None


class ProcessVoiceResponse(BaseModel):
    transcription: str
    is_question: bool
    is_continue_signal: bool
    exchange: Optional[AskResponse] = None
    resume: Optional[ContinueResponse] = None


class SessionResponse(BaseModel):
    id: str
    podcast_id: str
    current_segment_id: str
    status: str
    created_at: str
    updated_at: str


class QAExchangeResponse(BaseModel):
    id: str
    session_id: str
    segment_id: str
    question_text: str
    question_audio_url: Optional[str] = None
    host_acknowledgment: str
    expert_answer: str
    answer_audio_url: Optional[str] = None
    created_at: str
