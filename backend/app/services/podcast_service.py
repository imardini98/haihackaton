"""
Podcast Synthesis Service
Convert arXiv Papers to Podcast Script using Gemini PDF processing
"""

import io
import time
from typing import List, Dict, Any
from datetime import datetime

import requests
from google import genai

from app.config import get_settings

# Configuration
settings = get_settings()
GEMINI_MODEL = 'gemini-2.5-flash'


class PodcastSynthesisService:
    """Service for synthesizing research papers into podcast scripts"""

    def __init__(self):
        self.gemini_client = genai.Client(api_key=settings.gemini_api_key)

    def download_and_upload_pdfs(self, pdf_links: List[str]) -> List[Any]:
        """
        Download PDFs from arXiv and upload them to Gemini Files API

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

    def synthesize_papers_to_podcast(
        self,
        pdf_links: List[str],
        topic: str = ""
    ) -> Dict[str, Any]:
        """
        Synthesize multiple arXiv papers into a podcast script using Gemini PDF processing

        Args:
            pdf_links: List of PDF URLs from arXiv
            topic: Optional topic/context for the synthesis

        Returns:
            dict with podcast_script and metadata
        """
        try:
            # Step 1: Download and upload PDFs to Gemini
            uploaded_files = self.download_and_upload_pdfs(pdf_links)

            # Step 2: Create the synthesis prompt
            prompt = f"""You are an expert science communicator creating a podcast script that makes research accessible to everyone.

I have provided {len(pdf_links)} research papers from arXiv as PDF documents.

{f'Topic: {topic}' if topic else ''}

Your task is to:
1. Read and understand all {len(pdf_links)} papers thoroughly
2. Identify the common themes and key insights
3. **Find the connections and relationships between the papers**
4. Synthesize the information into a cohesive, interconnected narrative
5. Create an engaging podcast script (10-15 minutes when spoken)

CRITICAL GUIDELINES FOR ACCESSIBILITY:
- Use simple, everyday language - write as if explaining to a curious friend
- Replace technical jargon with plain language (e.g., "neural network" → "a computer system that learns like a brain")
- When technical terms are necessary, immediately explain them in simple words
- Break down complex ideas into smaller, easy-to-grasp concepts
- Use analogies and real-world examples that everyone can relate to
- Keep sentences short and clear
- Include all important details, but explain them simply
- Focus on what things DO rather than what they ARE

The podcast script should:
- Start with a compelling hook that explains why this research matters in everyday terms
- Explain the key concepts using simple, accessible language (imagine explaining to someone with no technical background)
- **STRONGLY EMPHASIZE THE CONNECTIONS between papers:**
  * Show how papers build on each other's ideas
  * Highlight where papers agree or provide complementary perspectives
  * Point out contrasting approaches or findings between papers
  * Explain how together they tell a bigger story than individually
  * Use explicit transition phrases: "This builds on...", "While the first paper showed X, the second paper takes it further...", "Interestingly, this contrasts with..."
  * Weave papers together rather than presenting them sequentially
- Highlight the most important findings with clear explanations and real-world examples
- Create a narrative arc that shows the evolution or progression of ideas across papers
- Use storytelling techniques (analogies, metaphors, everyday examples)
- Include specific details and numbers, but explain what they mean in practical terms
- Reference specific papers by author/institution to show connections: "The Stanford team found X, which the MIT researchers then used to..."
- End with implications and future directions that listeners can easily understand
- Be conversational and friendly (written for speaking, not reading)
- Avoid academic or overly complex vocabulary

Format the output as:
# Podcast Script: [Catchy, Easy-to-Understand Title]

## Opening Hook (30 seconds)
[Engaging introduction that immediately connects to everyday life]

## Context & Background (2-3 minutes)
[Explain the research area using simple language and relatable examples. Introduce how these papers connect to each other.]

## Key Findings (5-8 minutes)
[Main insights explained simply with clear examples and analogies. WEAVE THE PAPERS TOGETHER:
- Show how findings from different papers relate
- Highlight agreements, disagreements, or complementary approaches
- Use explicit connecting phrases between papers
- Create a narrative that shows progression or evolution of ideas
- Reference papers by author/institution to clarify connections]

## Real-World Impact (2-3 minutes)
[Practical applications explained in terms everyone can understand]

## Closing & Future Outlook (1-2 minutes)
[Wrap up with exciting future possibilities in accessible language]

---
## Technical Notes for Host
[Brief notes on pronunciation, key terms simplified, paper references]
"""

            # Build content with all PDFs + prompt
            contents = uploaded_files + [prompt]

            # Generate the synthesis
            response = self.gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents
            )

            # Extract the podcast script
            podcast_script = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    podcast_script += part.text

            # Check token usage
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata

            # Get uploaded file names
            uploaded_file_names = [f.name for f in uploaded_files]

            return {
                'podcast_script': podcast_script,
                'pdf_links': pdf_links,
                'topic': topic,
                'uploaded_files': uploaded_file_names,
                'usage': str(usage) if usage else None,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as error:
            raise Exception(f'Error synthesizing papers: {error}')
