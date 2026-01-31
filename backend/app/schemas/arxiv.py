"""
Pydantic schemas for arXiv semantic search
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ArxivSearchRequest(BaseModel):
    """Request schema for arXiv semantic search"""
    query: str = Field(..., description="The search query for arXiv papers", min_length=1)
    context: str = Field("", description="Additional context to refine the search")
    max_results: int = Field(20, description="Maximum number of papers to fetch from arXiv", ge=1, le=100)
    top_n: int = Field(5, description="Number of top results to return", ge=1, le=20)
    max_pdf_pages: int = Field(50, description="Maximum PDF pages allowed (for filtering)", ge=1, le=500)


class PaperSummary(BaseModel):
    """Summary schema for a paper"""
    index: int
    title: str
    authors: str
    arxiv_id: str
    summary: str
    published: str
    updated: str
    categories: List[str]
    primary_category: str
    pdf_link: str
    abstract_link: str
    page_count: Optional[int] = None
    relevance_score: Optional[int] = None
    relevance_reason: Optional[str] = None
    key_contributions: Optional[str] = None


class RefinedQuery(BaseModel):
    """Schema for refined query data"""
    refined_query: str
    key_concepts: List[str]
    search_focus: str
    additional_filters: Optional[Dict[str, Any]] = None


class ArxivSearchResponse(BaseModel):
    """Response schema for arXiv semantic search"""
    query: str
    timestamp: str
    total_papers_found: int
    papers_excluded_by_page_limit: int
    papers_after_filtering: int
    top_papers_count: int
    refined_query: RefinedQuery
    overall_analysis: str
    top_papers: List[PaperSummary]
    top_5_links: List[str]
    excluded_papers: Optional[List[Dict[str, Any]]] = None


class ArxivErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
