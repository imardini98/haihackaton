from __future__ import annotations
import json
import google.generativeai as genai
from typing import Optional
from app.config import get_settings
from app.services.prompt_service import prompt_service


class GeminiService:
    _model = None

    @property
    def model(self):
        
        """Lazy-load Gemini model."""
        if self._model is None:
            settings = get_settings()
            if not settings.gemini_api_key:
                raise RuntimeError("Gemini API key not configured")
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel("gemini-2.5-flash")
        return self._model

    async def generate_podcast_script(
        self,
        documents_content: str,
        topic: str,
        difficulty_level: str = "intermediate"
    ) -> dict:
        """Generate a podcast script from documents."""
        settings = get_settings()

        prompt = prompt_service.get_podcast_generation_prompt(
            document_context=documents_content,
            user_topic=topic,
            difficulty_level=difficulty_level,
            host_voice_id=settings.elevenlabs_host_voice_id,
            expert_voice_id=settings.elevenlabs_expert_voice_id
        )

        response = self.model.generate_content(prompt)

        # Extract JSON from response
        text = response.text

        # Try to parse JSON from the response
        try:
            # Look for JSON block in the response
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()

            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {text[:500]}")

    async def generate_qa_response(
        self,
        documents_content: str,
        episode_title: str,
        current_segment_id: int,
        current_segment_label: str,
        current_segment_content: str,
        current_key_terms: list[str],
        audio_timestamp: float,
        conversation_history: str,
        user_question: str
    ) -> dict:
        """Generate a Q&A response for a user question."""
        settings = get_settings()

        prompt = prompt_service.get_question_answer_prompt(
            document_context=documents_content,
            episode_title=episode_title,
            current_segment_id=current_segment_id,
            current_segment_label=current_segment_label,
            current_segment_content=current_segment_content,
            current_key_terms=current_key_terms,
            audio_timestamp=audio_timestamp,
            conversation_history=conversation_history,
            user_question=user_question,
            host_voice_id=settings.elevenlabs_host_voice_id,
            expert_voice_id=settings.elevenlabs_expert_voice_id
        )

        response = self.model.generate_content(prompt)
        text = response.text

        try:
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()

            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Q&A response as JSON: {e}")

    async def generate_resume_line(
        self,
        episode_title: str,
        last_segment_id: int,
        last_segment_label: str,
        next_segment_id: int,
        next_segment_label: str,
        question_text: str,
        topics_discussed: list[str],
        user_signal: str
    ) -> dict:
        """Generate a resume line after Q&A."""
        prompt = prompt_service.get_resume_prompt(
            episode_title=episode_title,
            last_segment_id=last_segment_id,
            last_segment_label=last_segment_label,
            next_segment_id=next_segment_id,
            next_segment_label=next_segment_label,
            question_text=question_text,
            topics_discussed=topics_discussed,
            user_signal=user_signal
        )

        response = self.model.generate_content(prompt)
        text = response.text

        try:
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()

            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse resume response as JSON: {e}")


gemini_service = GeminiService()
