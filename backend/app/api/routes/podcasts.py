from __future__ import annotations
import asyncio
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path

from app.schemas.podcast import (
    PodcastGenerateRequest,
    PodcastResponse,
    PodcastListResponse,
    PodcastStatusResponse,
    SegmentResponse,
    DialogueLine
)
from app.services.podcast_service import podcast_service
from app.services.supabase_service import supabase_service
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/podcasts", tags=["podcasts"])


def _format_podcast_response(podcast: dict, include_segments: bool = False) -> PodcastResponse:
    """Format podcast dict to response model."""
    segments = []
    if include_segments and "segments" in podcast:
        for seg in podcast["segments"]:
            dialogue = [
                DialogueLine(
                    speaker=line.get("speaker", "host"),
                    text=line.get("text", ""),
                    audio_url=line.get("audio_url")
                )
                for line in seg.get("dialogue", [])
            ]
            segments.append(SegmentResponse(
                id=seg["id"],
                sequence=seg.get("sequence", 0),
                topic_label=seg.get("topic_label"),
                dialogue=dialogue,
                key_terms=seg.get("key_terms", []),
                difficulty_level=seg.get("difficulty_level"),
                audio_url=seg.get("audio_url"),
                duration_seconds=seg.get("duration_seconds"),
                transition_to_question=seg.get("transition_to_question"),
                resume_phrase=seg.get("resume_phrase")
            ))

    return PodcastResponse(
        id=podcast["id"],
        title=podcast["title"],
        summary=podcast.get("summary"),
        topic=podcast.get("topic"),
        paper_ids=[str(pid) for pid in podcast.get("paper_ids", [])],
        status=podcast["status"],
        total_duration_seconds=podcast.get("total_duration_seconds"),
        error_message=podcast.get("error_message"),
        created_at=podcast["created_at"],
        segments=segments
    )


@router.post("/generate", response_model=PodcastResponse)
async def generate_podcast(
    request: PodcastGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start podcast generation from papers. Returns immediately, generation happens in background."""
    # Verify papers exist
    for paper_id in request.paper_ids:
        papers = await supabase_service.select("papers", filters={"id": paper_id})
        if not papers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paper not found: {paper_id}"
            )

    # Create podcast record
    podcast = await podcast_service.create_podcast(
        paper_ids=request.paper_ids,
        topic=request.topic,
        difficulty_level=request.difficulty_level,
        user_id=current_user.id
    )

    # Start generation in background
    background_tasks.add_task(
        podcast_service.generate_podcast,
        podcast["id"]
    )

    return _format_podcast_response(podcast)


@router.get("", response_model=PodcastListResponse)
async def list_podcasts(current_user: dict = Depends(get_current_user)):
    """List all podcasts for the current user."""
    podcasts = await supabase_service.select(
        "podcasts",
        filters={"user_id": current_user.id}
    )

    return PodcastListResponse(
        podcasts=[_format_podcast_response(p) for p in podcasts],
        total=len(podcasts)
    )


@router.get("/{podcast_id}", response_model=PodcastResponse)
async def get_podcast(
    podcast_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get podcast with all segments."""
    podcast = await podcast_service.get_podcast_with_segments(podcast_id)

    if not podcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )

    # Verify ownership
    if podcast.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return _format_podcast_response(podcast, include_segments=True)


@router.get("/{podcast_id}/status", response_model=PodcastStatusResponse)
async def get_podcast_status(
    podcast_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get podcast generation status (for polling)."""
    podcasts = await supabase_service.select(
        "podcasts",
        filters={"id": podcast_id}
    )

    if not podcasts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )

    podcast = podcasts[0]

    if podcast.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return PodcastStatusResponse(
        id=podcast["id"],
        status=podcast["status"],
        error_message=podcast.get("error_message")
    )


@router.get("/{podcast_id}/audio/{segment_sequence}")
async def get_segment_audio(
    podcast_id: str,
    segment_sequence: int,
    current_user: dict = Depends(get_current_user)
):
    """Stream audio for a specific segment."""
    # Verify ownership
    podcasts = await supabase_service.select(
        "podcasts",
        filters={"id": podcast_id}
    )
    if not podcasts or podcasts[0].get("user_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Get segment
    segments = await supabase_service.select(
        "segments",
        filters={"podcast_id": podcast_id}
    )

    segment = next(
        (s for s in segments if s.get("sequence") == segment_sequence),
        None
    )

    if not segment or not segment.get("audio_url"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment audio not found"
        )

    audio_path = Path(segment["audio_url"])
    if not audio_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=f"segment_{segment_sequence}.mp3"
    )


@router.delete("/{podcast_id}")
async def delete_podcast(
    podcast_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a podcast and its segments."""
    podcasts = await supabase_service.select(
        "podcasts",
        filters={"id": podcast_id}
    )

    if not podcasts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )

    if podcasts[0].get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Segments will be deleted via CASCADE
    await supabase_service.delete("podcasts", filters={"id": podcast_id})

    return {"status": "deleted"}
