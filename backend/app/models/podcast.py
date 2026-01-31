"""
Podcast and Segment data models
"""

from pydantic import BaseModel


class DialogueLine(BaseModel):
    speaker: str  # "host" or "expert"
    text: str


class Segment(BaseModel):
    id: int
    topic_label: str
    dialogue: list[DialogueLine]
    key_terms: list[str] = []
    difficulty_level: str = "beginner"
    source_reference: str = ""
    is_interruptible: bool = True
    transition_to_question: str = "Any questions?"
    resume_phrase: str = "Let's continue."


class PodcastVoices(BaseModel):
    host: str
    expert: str


class PodcastMetadata(BaseModel):
    title: str
    summary: str
    sources_analyzed: int = 0
    estimated_duration_minutes: int = 0
    primary_topics: list[str] = []
    voices: PodcastVoices


class Podcast(BaseModel):
    metadata: PodcastMetadata
    segments: list[Segment]


class QASegment(BaseModel):
    """Dynamic Q&A segment generated when user raises hand"""
    id: str  # e.g., "qa_after_2"
    original_segment_id: int
    user_question: str
    needs_clarification: bool = False
    clarification_prompt: str | None = None
    answer_dialogue: list[DialogueLine] = []
    is_complete: bool = False
