from __future__ import annotations
import base64
import httpx
from pathlib import Path
from typing import Optional
from app.config import get_settings


class MinimaxService:
    """Service for generating podcast thumbnails using Minimax AI."""
    
    API_URL = "https://api.minimax.io/v1/image_generation"
    
    async def generate_thumbnail(
        self,
        topic: str,
        filename: str = "thumbnail.jpeg",
        user_id: Optional[str] = None,
        podcast_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a podcast thumbnail image based on the topic.
        
        Args:
            topic: The podcast topic to generate an image for
            filename: Output filename (default: thumbnail.jpeg)
            user_id: User ID for folder structure
            podcast_id: Podcast ID for folder structure
            
        Returns:
            Path to the saved thumbnail image, or None if generation fails
        """
        settings = get_settings()
        
        if not settings.minimax_api_key:
            print("Warning: MINIMAX_API_KEY not configured, skipping thumbnail generation")
            return None
        
        # Build the image save path
        image_path = self._get_image_path(filename, user_id, podcast_id)
        
        # Create prompt for podcast thumbnail
        prompt = self._create_thumbnail_prompt(topic)
        
        headers = {"Authorization": f"Bearer {settings.minimax_api_key}"}
        payload = {
            "model": "image-01",
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "response_format": "base64",
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                images = data.get("data", {}).get("image_base64", [])
                
                if not images:
                    print("Warning: No images returned from Minimax API")
                    return None
                
                # Save the first image
                with open(image_path, "wb") as f:
                    f.write(base64.b64decode(images[0]))
                
                return str(image_path)
                
        except httpx.HTTPStatusError as e:
            print(f"Minimax API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")
            return None
    
    def _get_image_path(
        self,
        filename: str,
        user_id: Optional[str] = None,
        podcast_id: Optional[str] = None
    ) -> Path:
        """Get full path for image file with user/podcast folder structure."""
        settings = get_settings()
        image_dir = Path(settings.audio_storage_path)
        
        if user_id:
            image_dir = image_dir / user_id
        if podcast_id:
            image_dir = image_dir / podcast_id
        
        image_dir.mkdir(parents=True, exist_ok=True)
        return image_dir / filename
    
    def _create_thumbnail_prompt(self, topic: str) -> str:
        """Create an optimized prompt for podcast thumbnail generation."""
        return (
            f"Professional podcast cover art about: {topic}. "
            "NO TEXT, NO WORDS, NO LETTERS, NO WRITING. "
            "Abstract symbolic illustration, modern clean design, "
            "vibrant colors, scientific elements, "
            "high quality digital art, visually striking, "
            "pure visual imagery only"
        )


minimax_service = MinimaxService()
