"""
Pydantic schemas for podcast generation and segments
Uses paper_ids (ingested papers) + Segment system
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List


class PodcastGenerateRequest(BaseModel):
    """Request schema for podcast generation from ingested paper IDs"""
    paper_ids: List[str] = Field(
        ...,
        description="List of ingested paper UUIDs to synthesize",
        min_length=1,
        max_length=10
    )
    topic: str = Field(..., description="Topic/context for the podcast")
    difficulty_level: str = Field(
        default="intermediate",
        description="Difficulty level: beginner, intermediate, advanced"
    )


class DialogueLine(BaseModel):
    speaker: str  # "host" or "expert"
    text: str
    audio_url: Optional[str] = None


class SegmentResponse(BaseModel):
    id: str
    sequence: int
    topic_label: Optional[str] = None
    dialogue: List[DialogueLine]
    key_terms: List[str] = []
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
    paper_ids: List[str] = []
    status: str
    total_duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    segments: List[SegmentResponse] = []


class PodcastListResponse(BaseModel):
    podcasts: List[PodcastResponse]
    total: int


class PodcastStatusResponse(BaseModel):
    id: str
    status: str
    error_message: Optional[str] = None


# Legacy schemas for backward compatibility (simple synthesis endpoint)
class PodcastSynthesisRequest(BaseModel):
    """Request schema for simple podcast synthesis (no DB storage)"""
    pdf_links: List[str] = Field(
        ..., 
        description="List of arXiv PDF URLs to synthesize", 
        min_length=1, 
        max_length=10
    )
    topic: str = Field(default="", description="Optional topic/context for the synthesis")


class PodcastSynthesisResponse(BaseModel):
    """Response schema for simple podcast synthesis"""
    success: bool
    podcast_script: str
    pdf_links: List[str]
    topic: str
    uploaded_files: List[str]
    tokens_used: Optional[str] = None
    timestamp: str
