"""
Podcast Synthesis API Routes
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Dict, Any
import os
from datetime import datetime

from app.schemas.podcast import (
    PodcastSynthesisRequest,
    PodcastSynthesisResponse,
    PodcastErrorResponse
)
from app.services.podcast_service import PodcastSynthesisService
from app.config import get_settings

router = APIRouter(prefix="/podcasts", tags=["podcasts"])
settings = get_settings()

# Initialize service
podcast_service = PodcastSynthesisService()


def save_podcast_script_to_file(podcast_script: str, topic: str) -> str:
    """
    Save podcast script to a markdown file
    """
    os.makedirs(settings.audio_storage_path, exist_ok=True)

    timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
    safe_topic = topic.replace(' ', '_').replace('/', '_')[:50] if topic else 'general'
    filename = f'{settings.audio_storage_path}/podcast_script_{safe_topic}_{timestamp}.md'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(podcast_script)

    return filename


@router.post("/synthesize", response_model=PodcastSynthesisResponse)
async def synthesize_podcast(
    request: PodcastSynthesisRequest,
    background_tasks: BackgroundTasks
) -> PodcastSynthesisResponse:
    """
    Synthesize multiple arXiv papers into a podcast script using Gemini AI.

    - **pdf_links**: List of arXiv PDF URLs to synthesize (1-10 papers)
    - **topic**: Optional topic/context for the synthesis

    The process:
    1. Downloads PDFs from arXiv
    2. Uploads them to Gemini Files API for processing
    3. Uses Gemini to synthesize into a cohesive podcast script
    4. Returns the script with metadata

    **Note:** This endpoint may take 30-90 seconds to complete depending on the number and size of PDFs.
    """
    try:
        result = podcast_service.synthesize_papers_to_podcast(
            pdf_links=request.pdf_links,
            topic=request.topic
        )

        # Optionally save to file in background
        if result.get('podcast_script'):
            filename = save_podcast_script_to_file(
                result['podcast_script'],
                request.topic
            )
            result['filename'] = filename

        return PodcastSynthesisResponse(
            success=True,
            podcast_script=result['podcast_script'],
            pdf_links=result['pdf_links'],
            topic=result['topic'],
            uploaded_files=result['uploaded_files'],
            tokens_used=result.get('usage'),
            timestamp=result['timestamp']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def podcast_health_check() -> Dict[str, str]:
    """
    Health check for the podcast synthesis service
    """
    return {
        "service": "podcast-synthesis",
        "status": "healthy"
    }
