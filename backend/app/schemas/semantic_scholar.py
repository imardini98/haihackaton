"""
Pydantic schemas for Semantic Scholar API
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List


class SemanticScholarSearchRequest(BaseModel):
    """Request schema for Semantic Scholar search"""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    year_range: Optional[str] = Field(
        default=None,
        description="Year range filter (e.g., '2020-2024')"
    )
    fields_of_study: Optional[List[str]] = Field(
        default=None,
        description="Filter by fields (e.g., ['Computer Science', 'Medicine'])"
    )
    open_access_only: bool = Field(
        default=False,
        description="Only return papers with open access PDFs"
    )


class SemanticScholarPaper(BaseModel):
    """Paper from Semantic Scholar"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    citation_count: int = 0
    fields_of_study: List[str] = []
    publication_date: Optional[str] = None
    source: str = "semantic_scholar"


class SemanticScholarSearchResponse(BaseModel):
    """Response schema for Semantic Scholar search"""
    query: str
    total: int
    offset: int
    limit: int
    papers: List[SemanticScholarPaper]
    timestamp: str


class SemanticScholarIngestRequest(BaseModel):
    """Request to ingest a paper from Semantic Scholar"""
    paper_id: str = Field(..., description="Semantic Scholar paper ID")
