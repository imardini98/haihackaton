"""
Semantic Scholar API Service
Alternative to ArXiv for academic paper search
API Docs: https://api.semanticscholar.org/
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import httpx

from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
settings = get_settings()
SEMANTIC_SCHOLAR_API_BASE = 'https://api.semanticscholar.org/graph/v1'
SEARCH_FIELDS = 'paperId,title,abstract,authors,year,venue,openAccessPdf,citationCount,fieldsOfStudy,publicationDate'

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds


@dataclass
class SemanticScholarPaper:
    """Data class for Semantic Scholar paper"""
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: Optional[str]
    year: Optional[int]
    venue: Optional[str]
    citation_count: int
    fields_of_study: List[str]
    publication_date: Optional[str]


class SemanticScholarService:
    """Service for searching and fetching papers from Semantic Scholar"""

    def __init__(self):
        self.base_url = SEMANTIC_SCHOLAR_API_BASE
        self.timeout = 30.0
        self.max_retries = MAX_RETRIES
        self.initial_backoff = INITIAL_BACKOFF

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        retries: int = 0
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry for rate limiting."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, params=params)

                # Handle rate limiting with retry
                if response.status_code == 429 and retries < self.max_retries:
                    backoff = self.initial_backoff * (2 ** retries)
                    logger.warning(f"Rate limited (429), retrying in {backoff}s (attempt {retries + 1}/{self.max_retries})")
                    await asyncio.sleep(backoff)
                    return await self._request_with_retry(method, url, params, retries + 1)

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError:
                raise
            except Exception as e:
                if retries < self.max_retries:
                    backoff = self.initial_backoff * (2 ** retries)
                    logger.warning(f"Request failed, retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                    return await self._request_with_retry(method, url, params, retries + 1)
                raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        year_range: Optional[str] = None,
        fields_of_study: Optional[List[str]] = None,
        open_access_only: bool = False
    ) -> Dict[str, Any]:
        """
        Search for papers on Semantic Scholar.

        Args:
            query: Search query string
            limit: Maximum number of results (max 100)
            offset: Offset for pagination
            year_range: Filter by year range (e.g., "2020-2024")
            fields_of_study: Filter by fields (e.g., ["Computer Science"])
            open_access_only: Only return papers with open access PDFs

        Returns:
            Dict with search results and metadata
        """
        logger.info(f"Searching Semantic Scholar for: '{query}' (limit={limit})")

        params = {
            'query': query,
            'limit': min(limit, 100),
            'offset': offset,
            'fields': SEARCH_FIELDS
        }

        if year_range:
            params['year'] = year_range

        if fields_of_study:
            params['fieldsOfStudy'] = ','.join(fields_of_study)

        if open_access_only:
            params['openAccessPdf'] = ''

        try:
            response = await self._request_with_retry(
                "GET",
                f"{self.base_url}/paper/search",
                params=params
            )
            data = response.json()

            papers = []
            for item in data.get('data', []):
                paper = self._parse_paper(item)
                if paper:
                    papers.append(paper)

            # Filter open access if requested
            if open_access_only:
                papers = [p for p in papers if p.get('pdf_url')]

            logger.info(f"Found {len(papers)} papers from Semantic Scholar")

            return {
                'query': query,
                'total': data.get('total', len(papers)),
                'offset': offset,
                'limit': limit,
                'papers': papers,
                'timestamp': datetime.utcnow().isoformat()
            }

        except httpx.TimeoutException:
            logger.error(f"Timeout searching Semantic Scholar for: {query}")
            raise Exception("Semantic Scholar API timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Semantic Scholar: {e.response.status_code}")
            raise Exception(f"Semantic Scholar API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {e}")
            raise Exception(f"Error searching Semantic Scholar: {str(e)}")

    async def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by its Semantic Scholar ID.

        Args:
            paper_id: Semantic Scholar paper ID

        Returns:
            Paper data or None if not found
        """
        logger.info(f"Fetching paper from Semantic Scholar: {paper_id}")

        try:
            response = await self._request_with_retry(
                "GET",
                f"{self.base_url}/paper/{paper_id}",
                params={'fields': SEARCH_FIELDS}
            )
            data = response.json()
            return self._parse_paper(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Paper not found: {paper_id}")
                return None
            raise Exception(f"Semantic Scholar API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching paper {paper_id}: {e}")
            raise Exception(f"Error fetching paper: {str(e)}")

    async def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a paper by its ArXiv ID.

        Args:
            arxiv_id: ArXiv paper ID (e.g., "2301.00001")

        Returns:
            Paper data or None if not found
        """
        # Semantic Scholar accepts ArXiv IDs with ARXIV: prefix
        return await self.get_paper(f"ARXIV:{arxiv_id}")

    async def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get a paper by its DOI.

        Args:
            doi: DOI (e.g., "10.1000/xyz123")

        Returns:
            Paper data or None if not found
        """
        return await self.get_paper(f"DOI:{doi}")

    def _parse_paper(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw API response into standardized paper format."""
        if not data or not data.get('title'):
            return None

        # Extract authors
        authors = []
        for author in data.get('authors', []):
            name = author.get('name')
            if name:
                authors.append(name)

        # Extract PDF URL
        pdf_url = None
        open_access = data.get('openAccessPdf')
        if open_access and isinstance(open_access, dict):
            pdf_url = open_access.get('url')

        # Build paper object
        return {
            'paper_id': data.get('paperId'),
            'title': data.get('title', '').strip(),
            'authors': authors,
            'abstract': data.get('abstract', '').strip() if data.get('abstract') else '',
            'pdf_url': pdf_url,
            'year': data.get('year'),
            'venue': data.get('venue'),
            'citation_count': data.get('citationCount', 0),
            'fields_of_study': data.get('fieldsOfStudy', []),
            'publication_date': data.get('publicationDate'),
            'source': 'semantic_scholar'
        }

    async def search_similar(self, paper_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find papers similar to a given paper.

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of similar papers

        Returns:
            List of similar papers
        """
        logger.info(f"Finding papers similar to: {paper_id}")

        try:
            response = await self._request_with_retry(
                "GET",
                f"{self.base_url}/paper/{paper_id}/recommendations",
                params={
                    'fields': SEARCH_FIELDS,
                    'limit': limit
                }
            )
            data = response.json()

            papers = []
            for item in data.get('recommendedPapers', []):
                paper = self._parse_paper(item)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            logger.error(f"Error finding similar papers: {e}")
            return []


# Singleton instance
semantic_scholar_service = SemanticScholarService()
