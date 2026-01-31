from __future__ import annotations
from pathlib import Path
from functools import lru_cache
from jinja2 import Template


PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


@lru_cache
def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = PROMPTS_DIR / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {name}")

    return prompt_path.read_text()


def render_prompt(name: str, **variables) -> str:
    """Load and render a prompt template with variables."""
    template_content = load_prompt(name)
    template = Template(template_content)
    return template.render(**variables)


class PromptService:
    """Service for managing Gemini prompt templates."""

    @staticmethod
    def get_podcast_generation_prompt(
        document_context: str,
        user_topic: str,
        difficulty_level: str = "intermediate",
        host_voice_id: str = "",
        expert_voice_id: str = ""
    ) -> str:
        """Get the podcast generation prompt with context."""
        return render_prompt(
            "podcast_generation",
            document_context=document_context,
            user_topic=user_topic,
            difficulty_level=difficulty_level,
            host_voice_id=host_voice_id,
            expert_voice_id=expert_voice_id
        )

    @staticmethod
    def get_question_answer_prompt(
        document_context: str,
        episode_title: str,
        current_segment_id: int,
        current_segment_label: str,
        current_segment_content: str,
        current_key_terms: list[str],
        audio_timestamp: float,
        conversation_history: str,
        user_question: str,
        host_voice_id: str = "",
        expert_voice_id: str = ""
    ) -> str:
        """Get the Q&A prompt with full context."""
        return render_prompt(
            "question_answer",
            document_context=document_context,
            episode_title=episode_title,
            current_segment_id=current_segment_id,
            current_segment_label=current_segment_label,
            current_segment_content=current_segment_content,
            current_key_terms=", ".join(current_key_terms),
            audio_timestamp=audio_timestamp,
            conversation_history=conversation_history,
            user_question=user_question,
            host_voice_id=host_voice_id,
            expert_voice_id=expert_voice_id
        )

    @staticmethod
    def get_resume_prompt(
        episode_title: str,
        last_segment_id: int,
        last_segment_label: str,
        next_segment_id: int,
        next_segment_label: str,
        question_text: str,
        topics_discussed: list[str],
        user_signal: str
    ) -> str:
        """Get the resume conversation prompt."""
        return render_prompt(
            "resume_conversation",
            episode_title=episode_title,
            last_segment_id=last_segment_id,
            last_segment_label=last_segment_label,
            next_segment_id=next_segment_id,
            next_segment_label=next_segment_label,
            question_text=question_text,
            topics_discussed=", ".join(topics_discussed),
            user_signal=user_signal
        )


prompt_service = PromptService()
