from __future__ import annotations
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import json, time

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

# #region agent log
LOG_PATH = r"e:\Hackathon\odask\haihackaton\backend\debug.log"
def _debug_log(hyp, loc, msg, data=None):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"hypothesisId":hyp,"location":loc,"message":msg,"data":data,"timestamp":int(time.time()*1000),"sessionId":"debug-session"})+"\n")
        print(f"DEBUG: {loc} - {msg}")
    except Exception as ex:
        print(f"DEBUG_LOG_ERROR: {ex}")
# #endregion

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
    # #region agent log
    _debug_log("B", "papers.py:ingest_paper:entry", "Ingest started", {"arxiv_id": request.arxiv_id, "current_user_type": str(type(current_user)), "current_user_repr": repr(current_user)[:300]})
    # #endregion
    
    try:
        # #region agent log
        _debug_log("B", "papers.py:ingest_paper:access_user_id", "Attempting to access current_user.id", {"has_id": hasattr(current_user, 'id')})
        # #endregion
        user_id_test = current_user.id  # Test if this works
        # #region agent log
        _debug_log("B", "papers.py:ingest_paper:user_id_success", "Got user_id", {"user_id": str(user_id_test)})
        # #endregion
    except Exception as e:
        # #region agent log
        _debug_log("B", "papers.py:ingest_paper:user_id_error", "Failed to get user_id", {"error": str(e), "error_type": str(type(e))})
        # #endregion
        raise
    
    # Check if paper already exists
    # #region agent log
    _debug_log("D", "papers.py:ingest_paper:before_select", "About to check existing papers", {"arxiv_id": request.arxiv_id})
    # #endregion
    try:
        existing = await supabase_service.select(
            "papers",
            filters={"arxiv_id": request.arxiv_id}
        )
        # #region agent log
        _debug_log("D", "papers.py:ingest_paper:after_select", "Select completed", {"existing_count": len(existing) if existing else 0})
        # #endregion
    except Exception as e:
        # #region agent log
        _debug_log("D", "papers.py:ingest_paper:select_error", "Select failed", {"error": str(e), "error_type": str(type(e))})
        # #endregion
        raise
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
    # #region agent log
    _debug_log("E", "papers.py:ingest_paper:before_arxiv", "About to fetch from arxiv", {"arxiv_id": request.arxiv_id})
    # #endregion
    try:
        arxiv_paper = await arxiv_service.get_by_id(request.arxiv_id)
        # #region agent log
        _debug_log("E", "papers.py:ingest_paper:after_arxiv", "Arxiv fetch done", {"found": arxiv_paper is not None, "title": arxiv_paper.title[:50] if arxiv_paper else None})
        # #endregion
    except Exception as e:
        # #region agent log
        _debug_log("E", "papers.py:ingest_paper:arxiv_error", "Arxiv fetch failed", {"error": str(e), "error_type": str(type(e))})
        # #endregion
        raise
    if not arxiv_paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper not found on ArXiv: {request.arxiv_id}"
        )

    # Get content (abstract for MVP)
    content = await arxiv_service.get_paper_content(request.arxiv_id)
    # #region agent log
    _debug_log("E", "papers.py:ingest_paper:got_content", "Got paper content", {"content_length": len(content) if content else 0})
    # #endregion

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

    # #region agent log
    _debug_log("F", "papers.py:ingest_paper:before_insert", "About to insert paper", {"paper_data_keys": list(paper_data.keys()), "user_id": paper_data.get("user_id")})
    # #endregion
    try:
        saved = await supabase_service.insert("papers", paper_data)
        # #region agent log
        _debug_log("F", "papers.py:ingest_paper:after_insert", "Insert completed", {"saved": saved is not None, "saved_id": saved.get("id") if saved else None})
        # #endregion
    except Exception as e:
        # #region agent log
        _debug_log("F", "papers.py:ingest_paper:insert_error", "Insert failed", {"error": str(e)[:300], "error_type": str(type(e))})
        # #endregion
        raise
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
