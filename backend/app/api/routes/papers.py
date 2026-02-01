from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional

from app.schemas.paper import (
    PaperIngestRequest,
    PaperResponse,
    PaperListResponse
)
from app.schemas.arxiv import (
    ArxivSearchRequest,
    ArxivSearchResponse,
    PaperSummary,
    RefinedQuery
)
from app.services.arxiv_service import arxiv_service
from app.services.supabase_service import supabase_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/search", response_model=ArxivSearchResponse)
async def search_arxiv(request: ArxivSearchRequest):
    """
    Semantic search for arXiv papers using Gemini AI for query refinement and ranking.

    - **query**: The search query for arXiv papers (required)
    - **context**: Additional context to refine the search (optional)
    - **max_results**: Maximum number of papers to fetch from arXiv (default: 20, max: 100)
    - **top_n**: Number of top results to return (default: 5, max: 20)
    - **max_pdf_pages**: Maximum PDF pages allowed for filtering (default: 50)

    Returns a ranked list of relevant papers with:
    - Refined query with key concepts
    - Top N papers with relevance scores and contributions
    - PDF links for direct download
    - Excluded papers info (if any exceeded page limit)
    """
    logger.info(f"POST /api/v1/papers/search - query: '{request.query}'")

    result = arxiv_service.semantic_search(
        user_query=request.query,
        user_context=request.context,
        max_results=request.max_results,
        top_n=request.top_n,
        max_pdf_pages=request.max_pdf_pages
    )

    # Check for errors
    if 'error' in result:
        logger.error(f"Search error: {result.get('message')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('message', 'Unknown error occurred')
        )

    # Convert excluded_papers for response (keep only essential fields)
    excluded_papers = None
    if result.get('excluded_papers'):
        excluded_papers = [
            {
                'title': p['title'],
                'arxiv_id': p['arxiv_id'],
                'page_count': p.get('page_count'),
                'pdf_link': p['pdf_link']
            }
            for p in result['excluded_papers']
        ]

    # Build refined query object
    refined_query = RefinedQuery(
        refined_query=result['refined_query']['refined_query'],
        key_concepts=result['refined_query']['key_concepts'],
        search_focus=result['refined_query']['search_focus'],
        additional_filters=result['refined_query'].get('additional_filters')
    )

    # Build paper summaries
    top_papers = [
        PaperSummary(**paper) for paper in result['top_papers']
    ]

    return ArxivSearchResponse(
        query=result['query'],
        timestamp=result['timestamp'],
        total_papers_found=result['total_papers_found'],
        papers_excluded_by_page_limit=result['papers_excluded_by_page_limit'],
        papers_after_filtering=result['papers_after_filtering'],
        top_papers_count=result['top_papers_count'],
        refined_query=refined_query,
        overall_analysis=result['overall_analysis'],
        top_papers=top_papers,
        top_5_links=result['top_5_links'],
        excluded_papers=excluded_papers
    )

    logger.info(f"Search successful - returning {len(top_papers)} papers")


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
