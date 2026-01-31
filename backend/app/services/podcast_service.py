"""
Podcast Service - Full orchestration (CLAUDE.md naming)
Coordinates paper -> script -> audio pipeline
"""

from app.services.segment_manager import segment_manager
from app.services.elevenlabs_service import elevenlabs_service
from app.services.voice_service import voice_service


class PodcastService:
    """
    Orchestrates the full podcast generation pipeline.
    Matches CLAUDE.md service naming convention.
    
    This wraps segment_manager and adds higher-level orchestration.
    """
    
    def __init__(self):
        self.segment_manager = segment_manager
        self.elevenlabs = elevenlabs_service
        self.voice_service = voice_service
    
    def create_session(self, podcast_data, host_gender=None, expert_gender=None):
        """Create a podcast listening session"""
        return self.segment_manager.create_session(podcast_data)
    
    def get_session(self, session_id: str):
        """Get session by ID"""
        return self.segment_manager.get_session(session_id)
    
    def start_playback(self, session_id: str):
        """Start playing current segment"""
        return self.segment_manager.start_segment(session_id)
    
    def handle_raise_hand(self, session_id: str, question: str):
        """Handle user raising hand with question"""
        return self.segment_manager.raise_hand(session_id, question)
    
    def provide_answer(self, session_id: str, answer_dialogue: list):
        """Provide answer to user question"""
        return self.segment_manager.provide_answer(session_id, answer_dialogue)
    
    def resume_playback(self, session_id: str):
        """Resume podcast after Q&A"""
        return self.segment_manager.resume_podcast(session_id)
    
    # TODO: Add methods for full pipeline orchestration
    # - generate_from_papers(paper_ids) -> podcast
    # - queue_generation_job(paper_ids) -> job_id
    # - get_generation_status(job_id) -> status


# Singleton instance
podcast_service = PodcastService()
