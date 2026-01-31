"""
Segment Manager Service
Handles podcast playback state, interruptions, and Q&A flow
"""

import random
import uuid
from typing import Optional
from app.models.podcast import Podcast, Segment, QASegment, DialogueLine


# Natural transition phrases when someone raises their hand
# Varied to feel like a real classroom/lecture
HAND_RAISE_TRANSITIONS = [
    "Oh, looks like we have a question! Let's pause here.",
    "Hold on—someone wants to jump in. Go ahead!",
    "I see a hand up. What's on your mind?",
    "Wait, we've got a question. Let's hear it.",
    "Ah, someone has something to ask. Please, go ahead.",
    "Let's stop here for a moment—there's a question.",
    "One second—looks like someone wants to chime in.",
    "I think we have a question brewing. What is it?",
    "Before we continue, let's take this question.",
    "Interesting timing—someone has a question. Yes?",
    "Let me pause—we've got a curious mind here.",
    "Oh! A question already. I love it. What's up?",
]

# Phrases when the question isn't clear enough
CLARIFICATION_PROMPTS = [
    "Hmm, I want to make sure I understand. Could you elaborate a bit?",
    "Interesting question! Can you be more specific about what part you mean?",
    "I think I get it, but could you clarify what exactly you're asking about?",
    "Good question—but help me understand: which aspect are you curious about?",
    "Let me make sure I'm on the same page. What specifically do you want to know?",
    "That's a broad topic. Can you narrow down what you'd like me to explain?",
]

# Phrases to resume the podcast after Q&A
RESUME_TRANSITIONS = [
    "Great question! Now, back to where we were.",
    "Alright, hopefully that clears things up. Let's continue.",
    "Good stuff. Now, moving on...",
    "Thanks for asking! So, as I was saying...",
    "Excellent. With that answered, let's get back on track.",
    "Hope that helps! Now, let's pick up where we left off.",
]


class PodcastSession:
    """Represents an active podcast listening session"""
    
    def __init__(self, podcast: Podcast, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.podcast = podcast
        self.current_segment_index = 0
        self.is_playing = False
        self.is_in_qa = False
        self.current_qa: Optional[QASegment] = None
        self.qa_history: list[QASegment] = []
        
    @property
    def current_segment(self) -> Optional[Segment]:
        if 0 <= self.current_segment_index < len(self.podcast.segments):
            return self.podcast.segments[self.current_segment_index]
        return None
    
    @property
    def is_finished(self) -> bool:
        return self.current_segment_index >= len(self.podcast.segments)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "podcast_title": self.podcast.metadata.title,
            "current_segment_index": self.current_segment_index,
            "total_segments": len(self.podcast.segments),
            "is_playing": self.is_playing,
            "is_in_qa": self.is_in_qa,
            "is_finished": self.is_finished,
            "current_segment": self.current_segment.model_dump() if self.current_segment else None
        }


class SegmentManager:
    """Manages podcast sessions and segment flow"""
    
    def __init__(self):
        self.sessions: dict[str, PodcastSession] = {}
    
    def create_session(self, podcast: Podcast) -> PodcastSession:
        """Create a new podcast listening session"""
        session = PodcastSession(podcast)
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[PodcastSession]:
        """Get an existing session"""
        return self.sessions.get(session_id)
    
    def start_segment(self, session_id: str) -> dict:
        """Start playing the current segment"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if session.is_finished:
            return {
                "status": "finished",
                "message": "Podcast has ended"
            }
        
        session.is_playing = True
        segment = session.current_segment
        
        return {
            "status": "playing",
            "segment": segment.model_dump(),
            "can_interrupt": segment.is_interruptible
        }
    
    def raise_hand(self, session_id: str, user_question: str) -> dict:
        """
        Handle user raising their hand to ask a question.
        Returns transition phrase and enters Q&A mode.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        segment = session.current_segment
        if not segment:
            raise ValueError("No current segment")
        
        if not segment.is_interruptible:
            return {
                "status": "not_interruptible",
                "message": "Please wait until this section is complete."
            }
        
        # Stop current playback, enter Q&A mode
        session.is_playing = False
        session.is_in_qa = True
        
        # Create Q&A segment
        qa_segment = QASegment(
            id=f"qa_after_{segment.id}",
            original_segment_id=segment.id,
            user_question=user_question
        )
        session.current_qa = qa_segment
        
        # Get natural transition phrase
        hand_raise_phrase = random.choice(HAND_RAISE_TRANSITIONS)
        
        return {
            "status": "hand_raised",
            "transition_phrase": hand_raise_phrase,
            "segment_transition": segment.transition_to_question,
            "user_question": user_question,
            "qa_segment_id": qa_segment.id
        }
    
    def request_clarification(self, session_id: str) -> dict:
        """
        When the AI needs more info about the question.
        """
        session = self.get_session(session_id)
        if not session or not session.current_qa:
            raise ValueError("No active Q&A session")
        
        session.current_qa.needs_clarification = True
        clarification = random.choice(CLARIFICATION_PROMPTS)
        session.current_qa.clarification_prompt = clarification
        
        return {
            "status": "needs_clarification",
            "clarification_prompt": clarification
        }
    
    def provide_answer(
        self, 
        session_id: str, 
        answer_dialogue: list[dict]
    ) -> dict:
        """
        Provide the answer to the user's question.
        """
        session = self.get_session(session_id)
        if not session or not session.current_qa:
            raise ValueError("No active Q&A session")
        
        # Convert to DialogueLine objects
        dialogue = [DialogueLine(**d) for d in answer_dialogue]
        session.current_qa.answer_dialogue = dialogue
        session.current_qa.is_complete = True
        
        return {
            "status": "answered",
            "answer_dialogue": [d.model_dump() for d in dialogue],
            "qa_segment_id": session.current_qa.id
        }
    
    def resume_podcast(self, session_id: str) -> dict:
        """
        Resume the podcast after Q&A is complete.
        Moves to the next segment.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Store Q&A in history
        if session.current_qa:
            session.qa_history.append(session.current_qa)
        
        # Get resume phrase from current segment before moving on
        current_segment = session.current_segment
        resume_phrase = current_segment.resume_phrase if current_segment else ""
        
        # Also add a natural transition
        natural_resume = random.choice(RESUME_TRANSITIONS)
        
        # Exit Q&A mode and move to next segment
        session.is_in_qa = False
        session.current_qa = None
        session.current_segment_index += 1
        
        if session.is_finished:
            return {
                "status": "finished",
                "resume_phrase": resume_phrase,
                "natural_transition": natural_resume,
                "message": "That was the last segment. Podcast complete!"
            }
        
        return {
            "status": "resuming",
            "resume_phrase": resume_phrase,
            "natural_transition": natural_resume,
            "next_segment": session.current_segment.model_dump()
        }
    
    def skip_to_segment(self, session_id: str, segment_id: int) -> dict:
        """Skip to a specific segment"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Find segment index
        for i, seg in enumerate(session.podcast.segments):
            if seg.id == segment_id:
                session.current_segment_index = i
                session.is_in_qa = False
                session.current_qa = None
                return {
                    "status": "skipped",
                    "segment": session.current_segment.model_dump()
                }
        
        raise ValueError(f"Segment not found: {segment_id}")
    
    def get_session_state(self, session_id: str) -> dict:
        """Get current session state"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        return session.to_dict()


# Singleton instance
segment_manager = SegmentManager()
