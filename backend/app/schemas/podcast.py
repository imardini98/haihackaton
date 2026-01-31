"""
Pydantic schemas for podcast synthesis
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class PodcastSynthesisRequest(BaseModel):
    """Request schema for podcast synthesis from PDFs"""
    pdf_links: List[str] = Field(..., description="List of arXiv PDF URLs to synthesize", min_length=1, max_length=10)
    topic: str = Field("", description="Optional topic/context for the synthesis")


class PodcastSynthesisResponse(BaseModel):
    """Response schema for podcast synthesis"""
    success: bool
    podcast_script: str
    pdf_links: List[str]
    topic: str
    uploaded_files: List[str]
    tokens_used: Optional[str] = None
    timestamp: str


class PodcastErrorResponse(BaseModel):
    """Error response schema for podcast synthesis"""
    success: bool = False
    error: str
    detail: Optional[str] = None
