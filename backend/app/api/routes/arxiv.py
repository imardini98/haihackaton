"""
arXiv Semantic Search API Routes
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.schemas.arxiv import (
    ArxivSearchRequest,
    ArxivSearchResponse,
    ArxivErrorResponse,
    PaperSummary,
    RefinedQuery
)
from app.services.arxiv_service import ArxivSemanticSearchService

router = APIRouter(prefix="/arxiv", tags=["arxiv"])

# Initialize service
arxiv_service = ArxivSemanticSearchService()


@router.post("/search", response_model=ArxivSearchResponse)
async def search_arxiv_papers(request: ArxivSearchRequest) -> ArxivSearchResponse:
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
    result = arxiv_service.semantic_search(
        user_query=request.query,
        user_context=request.context,
        max_results=request.max_results,
        top_n=request.top_n,
        max_pdf_pages=request.max_pdf_pages
    )

    # Check for errors
    if 'error' in result:
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


@router.get("/health")
async def arxiv_health_check() -> Dict[str, str]:
    """
    Health check for the arXiv service
    """
    return {
        "service": "arxiv-semantic-search",
        "status": "healthy"
    }
