from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class PodcastGenerateRequest(BaseModel):
    paper_ids: list[str]
    topic: str
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced


class DialogueLine(BaseModel):
    speaker: str  # "host" or "expert"
    text: str
    audio_url: Optional[str] = None


class SegmentResponse(BaseModel):
    id: str
    sequence: int
    topic_label: Optional[str] = None
    dialogue: list[DialogueLine]
    key_terms: list[str] = []
    difficulty_level: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    transition_to_question: Optional[str] = None
    resume_phrase: Optional[str] = None


class PodcastResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    topic: Optional[str] = None
    paper_ids: list[str]
    status: str
    total_duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    segments: list[SegmentResponse] = []


class PodcastListResponse(BaseModel):
    podcasts: list[PodcastResponse]
    total: int


class PodcastStatusResponse(BaseModel):
    id: str
    status: str
    error_message: Optional[str] = None
