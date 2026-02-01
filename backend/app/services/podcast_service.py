"""
Podcast Service - Orchestrates podcast generation pipeline
Merged: Uses Gemini Files API with PDF links + Segment system from main
"""

from __future__ import annotations
import asyncio
import io
import time
from typing import Optional, List, Any

import requests
from google import genai

from app.config import get_settings
from app.services.supabase_service import supabase_service
from app.services.gemini_service import gemini_service
from app.services.elevenlabs_service import elevenlabs_service
from app.services.arxiv_service import arxiv_service


class PodcastService:
    """Orchestrates podcast generation pipeline using PDF links."""

    def __init__(self):
        settings = get_settings()
        self.gemini_client = genai.Client(api_key=settings.gemini_api_key)

    def download_and_upload_pdfs(self, pdf_links: List[str]) -> List[Any]:
        """
        Download PDFs from arXiv and upload them to Gemini Files API.

        Args:
            pdf_links: List of PDF URLs from arXiv

        Returns:
            List of uploaded file objects
        """
        uploaded_files = []

        for idx, pdf_url in enumerate(pdf_links, 1):
            try:
                # Download PDF
                response = requests.get(pdf_url, timeout=60)
                response.raise_for_status()
                pdf_data = io.BytesIO(response.content)

                # Upload to Gemini Files API
                uploaded_file = self.gemini_client.files.upload(
                    file=pdf_data,
                    config=dict(mime_type='application/pdf')
                )

                # Wait for file to be processed
                max_wait = 60  # Maximum wait time per file
                wait_time = 0
                while wait_time < max_wait:
                    file_status = self.gemini_client.files.get(name=uploaded_file.name)
                    if file_status.state == 'ACTIVE':
                        break
                    elif file_status.state == 'FAILED':
                        raise Exception(f'File processing failed for {pdf_url}')
                    else:
                        time.sleep(2)
                        wait_time += 2

                uploaded_files.append(uploaded_file)

            except Exception as error:
                raise Exception(f'Error with {pdf_url}: {error}')

        return uploaded_files

    async def create_podcast(
        self,
        pdf_links: List[str],
        topic: str,
        difficulty_level: str,
        user_id: str
    ) -> dict:
        """Create a new podcast record and start generation."""
        # Auto-ingest papers from PDF links and get their UUIDs
        paper_ids = await arxiv_service.auto_ingest_from_pdf_links(pdf_links, user_id)
        
        # Store pdf_links, topic, and difficulty_level in script_json 
        # for easy retrieval during generation
        initial_config = {
            "pdf_links": pdf_links,
            "topic": topic,
            "difficulty_level": difficulty_level,
            "status": "config"
        }
        
        # Create podcast record with pending status
        podcast_data = {
            "title": f"Podcast: {topic}",
            "summary": topic,  # Use summary to store topic temporarily
            "status": "pending",
            "user_id": user_id,
            "script_json": initial_config,
            "paper_ids": paper_ids  # Now populated with actual paper UUIDs
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
            # Get pdf_links and topic from script_json (initial config)
            config = podcast.get("script_json", {})
            pdf_links = config.get("pdf_links", [])
            topic = config.get("topic", podcast.get("summary", "Research Paper"))

            # Step 1: Download and upload PDFs to Gemini Files API
            uploaded_files = self.download_and_upload_pdfs(pdf_links)

            # Step 2: Generate script with Gemini using uploaded PDF files
            script = await gemini_service.generate_podcast_script_from_pdfs(
                uploaded_files=uploaded_files,
                topic=topic,
                difficulty_level=config.get("difficulty_level", "intermediate")
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
