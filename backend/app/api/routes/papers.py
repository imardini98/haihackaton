from __future__ import annotations
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional

from app.schemas.paper import (
    PaperSearchRequest,
    ArxivPaperResponse,
    PaperIngestRequest,
    PaperResponse,
    PaperListResponse
)
from app.services.arxiv_service import arxiv_service
from app.services.supabase_service import supabase_service
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/search", response_model=list[ArxivPaperResponse])
async def search_arxiv(request: PaperSearchRequest):
    """Search ArXiv for papers. No auth required."""
    try:
        papers = await arxiv_service.search(
            query=request.query,
            max_results=request.max_results,
            sort_by=request.sort_by
        )
        return [
            ArxivPaperResponse(
                arxiv_id=p.arxiv_id,
                title=p.title,
                authors=p.authors,
                abstract=p.abstract,
                pdf_url=p.pdf_url,
                published_date=p.published_date,
                categories=p.categories
            )
            for p in papers
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ArXiv search failed: {str(e)}"
        )


@router.post("/ingest", response_model=PaperResponse)
async def ingest_paper(
    request: PaperIngestRequest,
    current_user: dict = Depends(get_current_user)
):
    """Ingest a paper from ArXiv by ID and save to database."""
    # Check if paper already exists
    existing = await supabase_service.select(
        "papers",
        filters={"arxiv_id": request.arxiv_id}
    )
    if existing:
        # Return existing paper
        paper = existing[0]
        return PaperResponse(
            id=paper["id"],
            arxiv_id=paper["arxiv_id"],
            title=paper["title"],
            authors=paper["authors"],
            abstract=paper.get("abstract"),
            content=paper.get("content"),
            pdf_url=paper.get("pdf_url"),
            published_date=paper.get("published_date"),
            categories=paper.get("categories", []),
            created_at=paper["created_at"]
        )

    # Fetch from ArXiv
    arxiv_paper = await arxiv_service.get_by_id(request.arxiv_id)
    if not arxiv_paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper not found on ArXiv: {request.arxiv_id}"
        )

    # Get content (abstract for MVP)
    content = await arxiv_service.get_paper_content(request.arxiv_id)

    # Save to database
    paper_data = {
        "arxiv_id": arxiv_paper.arxiv_id,
        "title": arxiv_paper.title,
        "authors": arxiv_paper.authors,
        "abstract": arxiv_paper.abstract,
        "content": content,
        "pdf_url": arxiv_paper.pdf_url,
        "published_date": arxiv_paper.published_date,
        "categories": arxiv_paper.categories,
        "user_id": current_user.id
    }

    saved = await supabase_service.insert("papers", paper_data)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save paper"
        )

    return PaperResponse(
        id=saved["id"],
        arxiv_id=saved["arxiv_id"],
        title=saved["title"],
        authors=saved["authors"],
        abstract=saved.get("abstract"),
        content=saved.get("content"),
        pdf_url=saved.get("pdf_url"),
        published_date=saved.get("published_date"),
        categories=saved.get("categories", []),
        created_at=saved["created_at"]
    )


@router.get("", response_model=PaperListResponse)
async def list_papers(current_user: dict = Depends(get_current_user)):
    """List all papers for the current user."""
    papers = await supabase_service.select(
        "papers",
        filters={"user_id": current_user.id}
    )

    return PaperListResponse(
        papers=[
            PaperResponse(
                id=p["id"],
                arxiv_id=p["arxiv_id"],
                title=p["title"],
                authors=p["authors"],
                abstract=p.get("abstract"),
                content=p.get("content"),
                pdf_url=p.get("pdf_url"),
                published_date=p.get("published_date"),
                categories=p.get("categories", []),
                created_at=p["created_at"]
            )
            for p in papers
        ],
        total=len(papers)
    )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific paper by ID."""
    papers = await supabase_service.select(
        "papers",
        filters={"id": paper_id, "user_id": current_user.id}
    )

    if not papers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    p = papers[0]
    return PaperResponse(
        id=p["id"],
        arxiv_id=p["arxiv_id"],
        title=p["title"],
        authors=p["authors"],
        abstract=p.get("abstract"),
        content=p.get("content"),
        pdf_url=p.get("pdf_url"),
        published_date=p.get("published_date"),
        categories=p.get("categories", []),
        created_at=p["created_at"]
    )


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a paper."""
    await supabase_service.delete(
        "papers",
        filters={"id": paper_id, "user_id": current_user.id}
    )
    return {"status": "deleted"}
