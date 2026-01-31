from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaperSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    sort_by: str = "submitted"  # submitted (newest first), relevance, updated


class ArxivPaperResponse(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    pdf_url: str
    published_date: str
    categories: list[str]


class PaperIngestRequest(BaseModel):
    arxiv_id: str


class PaperResponse(BaseModel):
    id: str
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: Optional[str] = None
    content: Optional[str] = None
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None
    categories: list[str] = []
    created_at: str

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    papers: list[PaperResponse]
    total: int
