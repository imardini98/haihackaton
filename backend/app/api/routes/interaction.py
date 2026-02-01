from __future__ import annotations
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import Optional
from datetime import datetime

from app.schemas.interaction import (
    SessionStartRequest,
    SessionStartResponse,
    SessionUpdateRequest,
    SessionUpdateResponse,
    AskTextRequest,
    AskResponse,
    ContinueRequest,
    ContinueResponse,
    ProcessVoiceResponse,
    SessionResponse
)
from app.services.supabase_service import supabase_service
from app.services.gemini_service import gemini_service
from app.services.elevenlabs_service import elevenlabs_service
from app.api.dependencies import get_current_user
from app.utils.continue_signals import is_continue_signal, is_question

router = APIRouter(prefix="/interaction", tags=["interaction"])


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session(
    request: SessionStartRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start a new listening session for a podcast."""
    # Verify podcast exists and belongs to user
    podcasts = await supabase_service.select(
        "podcasts",
        filters={"id": request.podcast_id, "user_id": current_user.id}
    )
    if not podcasts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found"
        )

    # Create session
    session_data = {
        "podcast_id": request.podcast_id,
        "user_id": current_user.id,
        "current_segment_id": request.segment_id,
        "status": "playing"
    }

    session = await supabase_service.insert("listening_sessions", session_data)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )

    return SessionStartResponse(
        session_id=session["id"],
        podcast_id=session["podcast_id"],
        current_segment_id=session["current_segment_id"],
        status=session["status"]
    )


@router.post("/session/{session_id}/update", response_model=SessionUpdateResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update current position in listening session."""
    # Verify session belongs to user
    sessions = await supabase_service.select(
        "listening_sessions",
        filters={"id": session_id, "user_id": current_user.id}
    )
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Update session
    updated = await supabase_service.update(
        "listening_sessions",
        {
            "current_segment_id": request.current_segment_id,
            "updated_at": datetime.utcnow().isoformat()
        },
        {"id": session_id}
    )

    return SessionUpdateResponse(
        session_id=session_id,
        status=updated.get("status", "playing") if updated else "playing"
    )


@router.post("/ask", response_model=ProcessVoiceResponse)
async def ask_voice_question(
    session_id: str,
    audio: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Submit a voice question (audio file). Transcribes and processes."""
    # Get session
    sessions = await supabase_service.select(
        "listening_sessions",
        filters={"id": session_id, "user_id": current_user.id}
    )
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    session = sessions[0]

    # Save audio file with user/podcast folder structure
    audio_filename = f"question_{session_id}_{uuid.uuid4()}.mp3"
    audio_dir = Path(f"./audio_files/{current_user.id}/{session['podcast_id']}")
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / audio_filename

    with open(audio_path, "wb") as f:
        content = await audio.read()
        f.write(content)

    # Transcribe audio
    transcription = await elevenlabs_service.speech_to_text(str(audio_path))

    # Check if it's a continue signal or a question
    if is_continue_signal(transcription):
        # Process as continue signal
        resume_response = await _process_continue(session, transcription, current_user)
        return ProcessVoiceResponse(
            transcription=transcription,
            is_question=False,
            is_continue_signal=True,
            resume=resume_response
        )
    elif is_question(transcription) or len(transcription) > 10:
        # Process as question
        exchange = await _process_question(session, transcription, current_user)
        return ProcessVoiceResponse(
            transcription=transcription,
            is_question=True,
            is_continue_signal=False,
            exchange=exchange
        )
    else:
        # Unclear - treat as continue
        resume_response = await _process_continue(session, transcription, current_user)
        return ProcessVoiceResponse(
            transcription=transcription,
            is_question=False,
            is_continue_signal=True,
            resume=resume_response
        )


@router.post("/ask-text", response_model=AskResponse)
async def ask_text_question(
    request: AskTextRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit a text question."""
    # Get session
    sessions = await supabase_service.select(
        "listening_sessions",
        filters={"id": request.session_id, "user_id": current_user.id}
    )
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    session = sessions[0]

    # Process question
    exchange = await _process_question(session, request.question, current_user)
    return exchange


@router.post("/continue", response_model=ContinueResponse)
async def continue_podcast(
    request: ContinueRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process continue signal and get resume line."""
    # Get session
    sessions = await supabase_service.select(
        "listening_sessions",
        filters={"id": request.session_id, "user_id": current_user.id}
    )
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    session = sessions[0]

    return await _process_continue(session, request.user_signal, current_user)


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get session details."""
    sessions = await supabase_service.select(
        "listening_sessions",
        filters={"id": session_id, "user_id": current_user.id}
    )
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    s = sessions[0]
    return SessionResponse(
        id=s["id"],
        podcast_id=s["podcast_id"],
        current_segment_id=s["current_segment_id"],
        status=s["status"],
        created_at=s["created_at"],
        updated_at=s.get("updated_at", s["created_at"])
    )


async def _process_question(session: dict, question: str, current_user: dict) -> AskResponse:
    """Process a user question and generate response."""
    # Get podcast and current segment
    podcasts = await supabase_service.select(
        "podcasts",
        filters={"id": session["podcast_id"]}
    )
    if not podcasts:
        raise HTTPException(status_code=404, detail="Podcast not found")
    podcast = podcasts[0]

    segments = await supabase_service.select(
        "segments",
        filters={"id": session["current_segment_id"]}
    )
    current_segment = segments[0] if segments else None

    # Get paper content for context
    paper_ids = podcast.get("paper_ids", [])
    documents_content = ""
    if paper_ids:
        papers = await supabase_service.select("papers")
        for paper in papers:
            if paper["id"] in paper_ids:
                documents_content += f"\n\n--- {paper['title']} ---\n"
                documents_content += paper.get("abstract", "")
                documents_content += "\n" + paper.get("content", "")

    # Get conversation history
    qa_exchanges = await supabase_service.select(
        "qa_exchanges",
        filters={"session_id": session["id"]}
    )
    conversation_history = ""
    for qa in qa_exchanges:
        conversation_history += f"Q: {qa['question_text']}\n"
        conversation_history += f"A: {qa['expert_answer']}\n\n"

    # Generate Q&A response
    segment_content = ""
    segment_label = "Current segment"
    key_terms = []
    if current_segment:
        dialogue = current_segment.get("dialogue", [])
        segment_content = " ".join([d.get("text", "") for d in dialogue])
        segment_label = current_segment.get("topic_label", "Current segment")
        key_terms = current_segment.get("key_terms", [])

    qa_response = await gemini_service.generate_qa_response(
        documents_content=documents_content,
        episode_title=podcast.get("title", "Podcast"),
        current_segment_id=current_segment.get("sequence", 0) if current_segment else 0,
        current_segment_label=segment_label,
        current_segment_content=segment_content,
        current_key_terms=key_terms,
        audio_timestamp=0.0,
        conversation_history=conversation_history,
        user_question=question
    )

    exchange_data = qa_response.get("exchange", {})
    metadata = qa_response.get("metadata", {})

    host_ack = exchange_data.get("host_acknowledgment", "Great question.")
    expert_answer = exchange_data.get("expert_answer", "Let me explain...")

    # Generate audio for host and expert with user/podcast folder structure
    exchange_id = str(uuid.uuid4())
    user_id = current_user.id
    podcast_id = session["podcast_id"]
    
    host_audio_url = await elevenlabs_service.generate_host_audio(
        host_ack,
        f"qa_{exchange_id}_host.mp3",
        user_id=user_id,
        podcast_id=podcast_id
    )
    expert_audio_url = await elevenlabs_service.generate_expert_audio(
        expert_answer,
        f"qa_{exchange_id}_expert.mp3",
        user_id=user_id,
        podcast_id=podcast_id
    )

    # Save Q&A exchange to database
    qa_data = {
        "session_id": session["id"],
        "segment_id": session["current_segment_id"],
        "question_text": question,
        "host_acknowledgment": host_ack,
        "expert_answer": expert_answer,
        "answer_audio_url": expert_audio_url
    }
    saved = await supabase_service.insert("qa_exchanges", qa_data)

    # Update session status
    await supabase_service.update(
        "listening_sessions",
        {"status": "qa_active", "updated_at": datetime.utcnow().isoformat()},
        {"id": session["id"]}
    )

    return AskResponse(
        exchange_id=saved["id"] if saved else exchange_id,
        host_acknowledgment=host_ack,
        expert_answer=expert_answer,
        host_audio_url=host_audio_url,
        expert_audio_url=expert_audio_url,
        confidence=metadata.get("confidence", "medium"),
        topics_discussed=metadata.get("topics_discussed", [])
    )


async def _process_continue(session: dict, user_signal: str, current_user: dict) -> ContinueResponse:
    """Process continue signal and generate resume line."""
    # Get podcast and segments
    podcasts = await supabase_service.select(
        "podcasts",
        filters={"id": session["podcast_id"]}
    )
    podcast = podcasts[0] if podcasts else None

    # Get current and next segment
    segments = await supabase_service.select(
        "segments",
        filters={"podcast_id": session["podcast_id"]}
    )
    segments = sorted(segments, key=lambda s: s.get("sequence", 0))

    current_segment = None
    next_segment = None
    for i, seg in enumerate(segments):
        if seg["id"] == session["current_segment_id"]:
            current_segment = seg
            if i + 1 < len(segments):
                next_segment = segments[i + 1]
            break

    # Get last Q&A exchange for context
    qa_exchanges = await supabase_service.select(
        "qa_exchanges",
        filters={"session_id": session["id"]}
    )
    last_qa = qa_exchanges[-1] if qa_exchanges else None
    question_text = last_qa["question_text"] if last_qa else ""
    topics_discussed = []

    # Check if segment has a pre-generated resume phrase
    if current_segment and current_segment.get("resume_phrase"):
        resume_line = current_segment["resume_phrase"]
    else:
        # Generate resume line dynamically
        resume_response = await gemini_service.generate_resume_line(
            episode_title=podcast.get("title", "Podcast") if podcast else "Podcast",
            last_segment_id=current_segment.get("sequence", 0) if current_segment else 0,
            last_segment_label=current_segment.get("topic_label", "") if current_segment else "",
            next_segment_id=next_segment.get("sequence", 0) if next_segment else 0,
            next_segment_label=next_segment.get("topic_label", "") if next_segment else "",
            question_text=question_text,
            topics_discussed=topics_discussed,
            user_signal=user_signal
        )
        resume_line = resume_response.get("resume_line", {}).get("text", "Alright, let's continue.")

    # Generate audio for resume line with user/podcast folder structure
    resume_audio_url = await elevenlabs_service.generate_host_audio(
        resume_line,
        f"resume_{session['id']}_{uuid.uuid4()}.mp3",
        user_id=current_user.id,
        podcast_id=session["podcast_id"]
    )

    # Update session to playing and move to next segment
    next_segment_id = next_segment["id"] if next_segment else session["current_segment_id"]
    await supabase_service.update(
        "listening_sessions",
        {
            "status": "playing",
            "current_segment_id": next_segment_id,
            "updated_at": datetime.utcnow().isoformat()
        },
        {"id": session["id"]}
    )

    return ContinueResponse(
        resume_line=resume_line,
        resume_audio_url=resume_audio_url,
        next_segment_id=next_segment_id
    )
