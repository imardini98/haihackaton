from __future__ import annotations
import asyncio
from typing import Optional
from app.services.supabase_service import supabase_service
from app.services.gemini_service import gemini_service
from app.services.elevenlabs_service import elevenlabs_service


class PodcastService:
    """Orchestrates podcast generation pipeline."""

    async def create_podcast(
        self,
        paper_ids: list[str],
        topic: str,
        difficulty_level: str,
        user_id: str
    ) -> dict:
        """Create a new podcast record and start generation."""
        # Create podcast record with pending status
        podcast_data = {
            "paper_ids": paper_ids,
            "topic": topic,
            "title": f"Podcast: {topic}",
            "status": "pending",
            "user_id": user_id
        }

        podcast = await supabase_service.insert("podcasts", podcast_data)
        return podcast

    async def generate_podcast(self, podcast_id: str) -> None:
        """Generate podcast script and audio (run as background task)."""
        try:
            # Update status to generating
            await supabase_service.update(
                "podcasts",
                {"status": "generating"},
                {"id": podcast_id}
            )

            # Get podcast details
            podcasts = await supabase_service.select(
                "podcasts",
                filters={"id": podcast_id}
            )
            if not podcasts:
                raise ValueError("Podcast not found")

            podcast = podcasts[0]
            paper_ids = podcast["paper_ids"]
            topic = podcast["topic"]

            # Get papers content
            documents_content = await self._get_papers_content(paper_ids)

            # Generate script with Gemini
            script = await gemini_service.generate_podcast_script(
                documents_content=documents_content,
                topic=topic,
                difficulty_level="intermediate"
            )

            # Update podcast with script
            title = script.get("metadata", {}).get("title", f"Podcast: {topic}")
            summary = script.get("metadata", {}).get("summary", "")

            await supabase_service.update(
                "podcasts",
                {
                    "title": title,
                    "summary": summary,
                    "script_json": script
                },
                {"id": podcast_id}
            )

            # Create segments and generate audio
            segments = script.get("segments", [])
            total_duration = 0

            for segment_data in segments:
                segment = await self._create_segment(podcast_id, segment_data)
                if segment and segment.get("duration_seconds"):
                    total_duration += segment["duration_seconds"]

            # Update final status
            await supabase_service.update(
                "podcasts",
                {
                    "status": "ready",
                    "total_duration_seconds": int(total_duration)
                },
                {"id": podcast_id}
            )

        except Exception as e:
            # Update status to failed
            await supabase_service.update(
                "podcasts",
                {
                    "status": "failed",
                    "error_message": str(e)
                },
                {"id": podcast_id}
            )
            raise

    async def _get_papers_content(self, paper_ids: list[str]) -> str:
        """Get combined content from papers."""
        contents = []

        for paper_id in paper_ids:
            papers = await supabase_service.select(
                "papers",
                filters={"id": paper_id}
            )
            if papers:
                paper = papers[0]
                content = f"""
<paper id="{paper['arxiv_id']}">
<title>{paper['title']}</title>
<authors>{', '.join(paper.get('authors', []))}</authors>
<abstract>{paper.get('abstract', '')}</abstract>
<content>{paper.get('content', paper.get('abstract', ''))}</content>
</paper>
"""
                contents.append(content)

        return "\n".join(contents)

    async def _create_segment(self, podcast_id: str, segment_data: dict) -> Optional[dict]:
        """Create a segment and generate its audio."""
        dialogue = segment_data.get("dialogue", [])

        # Generate audio for segment
        segment_id = f"{podcast_id}_{segment_data.get('id', 0)}"

        try:
            audio_url = await elevenlabs_service.generate_segment_audio(
                dialogue=dialogue,
                segment_id=segment_id
            )
        except Exception as e:
            print(f"Audio generation failed for segment: {e}")
            audio_url = None

        # Estimate duration (rough: 150 words per minute)
        total_words = sum(len(line.get("text", "").split()) for line in dialogue)
        duration_seconds = (total_words / 150) * 60

        segment_record = {
            "podcast_id": podcast_id,
            "sequence": segment_data.get("id", 0),
            "topic_label": segment_data.get("topic_label"),
            "dialogue": dialogue,
            "key_terms": segment_data.get("key_terms", []),
            "difficulty_level": segment_data.get("difficulty_level"),
            "audio_url": audio_url,
            "duration_seconds": duration_seconds,
            "transition_to_question": segment_data.get("transition_to_question"),
            "resume_phrase": segment_data.get("resume_phrase")
        }

        return await supabase_service.insert("segments", segment_record)

    async def get_podcast_with_segments(self, podcast_id: str) -> Optional[dict]:
        """Get podcast with all its segments."""
        podcasts = await supabase_service.select(
            "podcasts",
            filters={"id": podcast_id}
        )
        if not podcasts:
            return None

        podcast = podcasts[0]

        # Get segments
        segments = await supabase_service.select(
            "segments",
            filters={"podcast_id": podcast_id}
        )

        # Sort by sequence
        segments = sorted(segments, key=lambda x: x.get("sequence", 0))

        podcast["segments"] = segments
        return podcast


podcast_service = PodcastService()
