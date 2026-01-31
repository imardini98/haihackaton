from __future__ import annotations
import json
from typing import Optional, List, Any

import google.generativeai as genai
from google import genai as genai_client

from app.config import get_settings
from app.services.prompt_service import prompt_service


GEMINI_MODEL = 'gemini-2.5-flash'


class GeminiService:
    _model = None
    _client = None

    @property
    def model(self):
        """Lazy-load Gemini model (for text-based generation)."""
        if self._model is None:
            settings = get_settings()
            if not settings.gemini_api_key:
                raise RuntimeError("Gemini API key not configured")
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(GEMINI_MODEL)
        return self._model

    @property
    def client(self):
        """Lazy-load Gemini client (for Files API / multimodal)."""
        if self._client is None:
            settings = get_settings()
            if not settings.gemini_api_key:
                raise RuntimeError("Gemini API key not configured")
            self._client = genai_client.Client(api_key=settings.gemini_api_key)
        return self._client

    async def generate_podcast_script_from_pdfs(
        self,
        uploaded_files: List[Any],
        topic: str,
        difficulty_level: str = "intermediate"
    ) -> dict:
        """
        Generate a podcast script from uploaded PDF files using Gemini Files API.
        
        Args:
            uploaded_files: List of uploaded file objects from Gemini Files API
            topic: The topic/focus for the podcast
            difficulty_level: beginner, intermediate, or advanced
            
        Returns:
            dict with structured podcast script (metadata + segments)
        """
        settings = get_settings()

        # Build the prompt for PDF-based generation
        prompt = self._build_pdf_podcast_prompt(
            num_papers=len(uploaded_files),
            topic=topic,
            difficulty_level=difficulty_level,
            host_voice_id=settings.elevenlabs_host_voice_id,
            expert_voice_id=settings.elevenlabs_expert_voice_id
        )

        # Build content with all PDFs + prompt
        contents = uploaded_files + [prompt]

        # Generate using the client (supports multimodal content)
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents
        )

        # Extract text from response
        text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                text += part.text

        # Parse JSON from the response
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
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {text[:500]}")

    def _build_pdf_podcast_prompt(
        self,
        num_papers: int,
        topic: str,
        difficulty_level: str,
        host_voice_id: str,
        expert_voice_id: str
    ) -> str:
        """Build the prompt for generating podcast script from PDF documents."""
        return f"""# SYSTEM PROMPT: PodAsk Podcast Script Generator

## ROLE
You generate conversational podcast scripts featuring two voices:
- **HOST:** Warm, curious, guides the conversation. Asks clarifying questions, provides transitions, keeps things accessible.
- **EXPERT:** Knowledgeable guest who explains the research findings. Confident but approachable, uses clear examples.

The format simulates a real podcast interview where the host and expert discuss scientific papers naturally.

## CONTEXT & SOURCES
I have provided {num_papers} research papers from arXiv as PDF documents attached to this message.
Read and analyze ALL the PDF documents thoroughly before generating the script.

## INPUT TOPIC
The focus of today's episode is: "{topic}"

## TARGET AUDIENCE
Difficulty level: {difficulty_level}  <!-- beginner | intermediate | advanced -->

## TASK
Use ONLY the information from the provided PDF papers to generate a structured podcast script in JSON format. Create a natural back-and-forth dialogue between HOST and EXPERT.

**CRITICAL: Emphasize the connections between papers throughout the conversation:**
- Show how papers build on each other
- Highlight where papers agree, disagree, or complement each other
- Use explicit references: "The Stanford team found X, while the MIT paper shows Y..."
- Create a narrative that weaves papers together rather than presenting them separately
- Host should ask about connections: "How does this relate to the earlier finding?"
- Expert should make connections explicit: "This builds directly on what we saw in the first paper..."

If specific information is not found in the sources, the expert should acknowledge the limitation honestly.

## OUTPUT FORMAT (STRICT JSON)
Respond ONLY with a JSON object. Do not include any pre-text or post-text.

### JSON Structure:
- `metadata`: Podcast info and voice assignments.
- `segments`: Modular conversation blocks with dialogue lines.

```json
{{
  "metadata": {{
    "title": "Episode title based on the papers",
    "summary": "2-3 sentence overview of what's covered",
    "sources_analyzed": {num_papers},
    "estimated_duration_minutes": 12,
    "primary_topics": ["topic1", "topic2"],
    "voices": {{
      "host": "{host_voice_id}",
      "expert": "{expert_voice_id}"
    }}
  }},
  "segments": [
    {{
      "id": 1,
      "topic_label": "Segment title",
      "dialogue": [
        {{"speaker": "host", "text": "Host's line..."}},
        {{"speaker": "expert", "text": "Expert's response..."}}
      ],
      "key_terms": ["term1", "term2"],
      "difficulty_level": "beginner|intermediate|advanced",
      "source_reference": "Paper_ID or synthesis note",
      "is_interruptible": true,
      "transition_to_question": "Short HOST phrase inviting questions",
      "resume_phrase": "Short HOST phrase to continue after Q&A"
    }}
  ]
}}
```

## SEGMENT GUIDELINES

Each segment should:
- **Last 15-25 seconds when spoken** (short enough so users don't wait long if they raise hand)
- Feel like a natural conversation, not a lecture
- End at a logical pause point where a listener could "raise their hand"
- ALL segments must have `transition_to_question` and `resume_phrase`

**Q&A Integration Fields (REQUIRED):**
- `transition_to_question`: HOST phrase played when user raises hand (after segment ends). Natural invitation to ask. E.g., "Any questions on that?"
- `resume_phrase`: HOST phrase played after Q&A is complete to bridge back. E.g., "Alright, moving on..."

## DIALOGUE STYLE

### HOST
- Opens with curiosity: "So tell me about...", "I found it interesting that...", "Walk me through..."
- Asks follow-up questions a listener might have
- **Actively asks about connections between papers:** "How does this relate to...", "You mentioned earlier that...", "Is this similar to what the other team found?"
- Bridges between topics naturally while highlighting relationships
- Occasionally summarizes for clarity: "So what you're saying is..."
- Points out patterns: "I'm noticing a trend here...", "All these papers seem to suggest..."
- Keeps energy up but not over the top
- Helps "translate" complex ideas into simple terms: "So in other words...", "That's like..."

### EXPERT
- Explains findings conversationally, not academically
- Uses simple, everyday language - avoids unnecessary jargon
- When technical terms are needed, immediately explains them in plain language
- **Explicitly connects papers throughout the discussion:**
  * References specific papers by author/institution: "The Stanford team found X..."
  * Makes connections explicit: "This builds on...", "While Paper A showed X, Paper B took it further..."
  * Highlights agreements: "All three teams observed..."
  * Points out differences: "Interestingly, the MIT approach differs from Stanford's in that..."
  * Shows evolution of ideas: "Early work established X, then recent papers added Y..."
- Uses specific numbers and citations: "The team at Stanford found a 23% improvement..."
- Always gives analogies and real-world examples to make concepts clear
- Breaks down complex ideas into smaller, digestible pieces
- Acknowledges complexity but then simplifies: "This part gets a bit technical, but think of it like..."
- Speaks with authority but not arrogance
- Focuses on what things DO rather than what they ARE

## STYLE GUIDELINES
1. **Fidelity:** Do not hallucinate. Use exact numbers from papers.
2. **Natural Flow:** The dialogue should feel unscripted, with natural interruptions and reactions.
3. **Paper Connections (CRITICAL):**
   - Never present papers in isolation
   - Always show how papers relate to each other
   - Use explicit connecting language throughout
   - The listener should feel like the papers tell a connected story together
4. **Accessibility & Simplicity:** 
   - Use simple, clear language throughout
   - Replace technical jargon with everyday words whenever possible
   - Explain technical terms immediately when they must be used
   - Include important details but present them in an easy-to-understand way
   - Use analogies, metaphors, and real-world examples extensively
   - Write as if explaining to someone curious but without technical background
5. **Engagement:** The host should react genuinely—surprise, interest, clarification.

## HANDLING MISSING INFORMATION

If a topic would be interesting but isn't covered in the sources, acknowledge limits naturally within the conversation.

Now analyze all the attached PDF documents and generate the podcast script JSON.
"""

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
