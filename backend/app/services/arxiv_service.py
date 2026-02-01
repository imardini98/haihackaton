"""
arXiv Semantic Search Service
Powered by arXiv API + Google Gemini
"""

import json
import time
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import requests
import pikepdf
from google import genai

from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
settings = get_settings()
ARXIV_API_BASE = 'http://export.arxiv.org/api/query'
GEMINI_MODEL = 'gemini-2.5-flash'
PAGE_CHECK_WORKERS = 5


@dataclass
class ArxivPaper:
    """Data class for arXiv paper"""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    pdf_url: str
    published_date: str
    categories: List[str]


class ArxivSemanticSearchService:
    """Service for semantic search on arXiv papers"""

    def __init__(self):
        self.gemini_client = genai.Client(api_key=settings.gemini_api_key)

    def _parse_arxiv_entry(self, entry: ET.Element, namespaces: Dict[str, str]) -> Optional[ArxivPaper]:
        """Parse a single arXiv entry into an ArxivPaper object"""
        try:
            entry_id = entry.find('atom:id', namespaces).text
            if 'api/errors' in entry_id:
                return None

            arxiv_id = entry_id.split('/abs/')[-1]
            
            title = entry.find('atom:title', namespaces).text.strip().replace('\n', ' ')
            
            authors = entry.findall('atom:author', namespaces)
            author_list = [a.find('atom:name', namespaces).text for a in authors]
            
            abstract = entry.find('atom:summary', namespaces).text.strip().replace('\n', ' ')
            
            published = entry.find('atom:published', namespaces).text
            
            categories = [cat.get('term') for cat in entry.findall('atom:category', namespaces)]
            
            return ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=author_list,
                abstract=abstract,
                pdf_url=f'http://arxiv.org/pdf/{arxiv_id}',
                published_date=published,
                categories=categories
            )
        except Exception:
            return None

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "submitted"
    ) -> List[ArxivPaper]:
        """
        Search arXiv for papers
        
        Args:
            query: Search query (can be simple text or arXiv query syntax)
            max_results: Maximum number of results
            sort_by: Sort order (submitted, relevance, updated)
            
        Returns:
            List of ArxivPaper objects
        """
        sort_by_map = {
            "submitted": "submittedDate",
            "relevance": "relevance",
            "updated": "lastUpdatedDate"
        }
        
        # Check if query already contains arXiv operators
        arxiv_operators = ['ti:', 'abs:', 'au:', 'cat:', 'all:', 'AND', 'OR', 'ANDNOT']
        has_operators = any(op in query for op in arxiv_operators)
        
        # Only add 'all:' prefix if query doesn't have operators
        search_query = query if has_operators else f'all:{query}'
        
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': sort_by_map.get(sort_by, "submittedDate"),
            'sortOrder': 'descending'
        }

        try:
            response = requests.get(ARXIV_API_BASE, params=params, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            entries = root.findall('atom:entry', namespaces)
            
            papers = []
            for entry in entries:
                paper = self._parse_arxiv_entry(entry, namespaces)
                if paper:
                    papers.append(paper)
                    
            return papers

        except Exception as error:
            raise Exception(f'Error searching arXiv: {error}')

    async def get_by_id(self, arxiv_id: str) -> Optional[ArxivPaper]:
        """
        Get a single paper by arXiv ID
        
        Args:
            arxiv_id: The arXiv ID (e.g., "2301.07041")
            
        Returns:
            ArxivPaper object or None if not found
        """
        params = {
            'id_list': arxiv_id,
            'max_results': 1
        }

        try:
            response = requests.get(ARXIV_API_BASE, params=params, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            entries = root.findall('atom:entry', namespaces)
            if not entries:
                return None
                
            return self._parse_arxiv_entry(entries[0], namespaces)

        except Exception as error:
            raise Exception(f'Error fetching paper {arxiv_id}: {error}')

    async def get_paper_content(self, arxiv_id: str) -> str:
        """
        Get the content/abstract of a paper by arXiv ID
        
        For now, this returns the abstract. In the future, this could be enhanced
        to fetch and parse the full PDF content.
        
        Args:
            arxiv_id: The arXiv ID
            
        Returns:
            Paper content (currently just the abstract)
        """
        paper = await self.get_by_id(arxiv_id)
        if paper:
            return paper.abstract
        return ""

    def refine_user_query(self, user_query: str, user_context: str = '') -> Dict[str, Any]:
        """
        Step 1: Refine user query using Gemini
        """
        logger.info(f"Step 1: Refining query - '{user_query}'")

        prompt = f"""Refine this arXiv search query.

Query: "{user_query}"
{f'Context: {user_context}' if user_context else ''}

Create optimized arXiv query with operators (ti:, abs:, cat:, all:).
Identify 3-5 key concepts and brief focus statement.

Output JSON: {{"refined_query": "...", "key_concepts": ["..."], "search_focus": "...", "additional_filters": {{"categories": ["..."], "date_range": "..."}}}}"""

        try:
            response_schema = {
                "type": "object",
                "properties": {
                    "refined_query": {"type": "string"},
                    "key_concepts": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "search_focus": {"type": "string"},
                    "additional_filters": {
                        "type": "object",
                        "properties": {
                            "categories": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "date_range": {"type": "string"}
                        }
                    }
                },
                "required": ["refined_query", "key_concepts", "search_focus"]
            }

            response = self.gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": response_schema
                }
            )

            refined_data = json.loads(response.text)
            logger.info(f"Query refined successfully: '{refined_data['refined_query']}'")
            logger.info(f"Key concepts: {refined_data['key_concepts']}")
            return refined_data

        except Exception as error:
            logger.warning(f"Failed to refine query with Gemini: {error}, using fallback")
            # Fallback to original query
            return {
                'refined_query': f'all:{user_query}',
                'key_concepts': [user_query],
                'search_focus': 'General search',
                'additional_filters': {}
            }

    def check_pdf_page_count(self, pdf_url: str, timeout: int = 15) -> Optional[int]:
        """
        Check the number of pages in a PDF

        Args:
            pdf_url: URL to the PDF
            timeout: Request timeout in seconds

        Returns:
            Number of pages, or None if error
        """
        try:
            response = requests.get(pdf_url, timeout=timeout)
            response.raise_for_status()

            pdf_buffer = io.BytesIO(response.content)

            with pikepdf.open(pdf_buffer) as pdf:
                num_pages = len(pdf.pages)
                return num_pages

        except Exception:
            return None

    def check_single_paper(self, paper: Dict[str, Any], max_pages: int) -> Dict[str, Any]:
        """
        Check a single paper's page count and return result

        Args:
            paper: Paper dictionary
            max_pages: Maximum allowed pages

        Returns:
            Dict with paper and status info
        """
        pdf_url = paper['pdf_link']
        arxiv_id = paper['arxiv_id']

        page_count = self.check_pdf_page_count(pdf_url)

        result = {
            'paper': paper,
            'arxiv_id': arxiv_id,
            'page_count': page_count,
            'included': False,
            'reason': ''
        }

        if page_count is None:
            paper['page_count'] = None
            result['included'] = True
            result['reason'] = 'Unknown (included)'
        elif page_count <= max_pages:
            paper['page_count'] = page_count
            result['included'] = True
            result['reason'] = f'{page_count} pages'
        else:
            paper['page_count'] = page_count
            result['included'] = False
            result['reason'] = f'{page_count} pages (excluded)'

        return result

    def filter_papers_by_page_count(
        self,
        papers: List[Dict[str, Any]],
        max_pages: int,
        max_workers: int = PAGE_CHECK_WORKERS
    ) -> tuple:
        """
        Filter papers to only include those with <= max_pages (parallel processing)

        Args:
            papers: List of paper dictionaries
            max_pages: Maximum allowed pages
            max_workers: Number of concurrent threads

        Returns:
            Tuple of (filtered_papers, excluded_papers)
        """
        logger.info(f"Step 3: Checking PDF page counts (max: {max_pages} pages, {len(papers)} papers)")

        filtered_papers = []
        excluded_papers = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_paper = {
                executor.submit(self.check_single_paper, paper, max_pages): paper
                for paper in papers
            }

            for future in as_completed(future_to_paper):
                try:
                    result = future.result()

                    if result['included']:
                        filtered_papers.append(result['paper'])
                    else:
                        excluded_papers.append(result['paper'])

                except Exception:
                    paper = future_to_paper[future]
                    # Include on error (benefit of doubt)
                    paper['page_count'] = None
                    filtered_papers.append(paper)

        logger.info(f"Page filter complete: {len(filtered_papers)} kept, {len(excluded_papers)} excluded")
        return filtered_papers, excluded_papers

    def search_arxiv(
        self,
        refined_query: Dict[str, Any],
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Step 2: Search arXiv API with refined query
        """
        logger.info(f"Step 2: Searching arXiv with query '{refined_query['refined_query']}' (max_results={max_results})")

        params = {
            'search_query': refined_query['refined_query'],
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }

        try:
            response = requests.get(ARXIV_API_BASE, params=params)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            entries = root.findall('atom:entry', namespaces)

            papers = []
            for index, entry in enumerate(entries, 1):
                entry_id = entry.find('atom:id', namespaces).text

                if 'api/errors' in entry_id:
                    continue

                arxiv_id = entry_id.split('/abs/')[-1]

                authors = entry.findall('atom:author', namespaces)
                author_names = ', '.join([a.find('atom:name', namespaces).text for a in authors])

                categories = [cat.get('term') for cat in entry.findall('atom:category', namespaces)]

                primary_cat = entry.find('arxiv:primary_category', namespaces)
                primary_category = primary_cat.get('term') if primary_cat is not None else (categories[0] if categories else '')

                title = entry.find('atom:title', namespaces).text.strip().replace('\n', ' ')
                summary = entry.find('atom:summary', namespaces).text.strip().replace('\n', ' ')
                published = entry.find('atom:published', namespaces).text
                updated = entry.find('atom:updated', namespaces).text

                paper = {
                    'index': index,
                    'title': title,
                    'authors': author_names,
                    'arxiv_id': arxiv_id,
                    'summary': summary,
                    'published': published,
                    'updated': updated,
                    'categories': categories,
                    'primary_category': primary_category,
                    'pdf_link': f'http://arxiv.org/pdf/{arxiv_id}',
                    'abstract_link': f'http://arxiv.org/abs/{arxiv_id}'
                }

                papers.append(paper)

            logger.info(f"Found {len(papers)} papers from arXiv")
            return papers

        except Exception as error:
            logger.error(f"Error searching arXiv: {error}")
            raise Exception(f'Error searching arXiv: {error}')

    def rank_papers_with_gemini(
        self,
        papers: List[Dict[str, Any]],
        original_query: str,
        refined_query: Dict[str, Any],
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Step 3: Use Gemini to classify and rank the papers
        """
        logger.info(f"Step 4: Ranking {len(papers)} papers with Gemini (selecting top {top_n})")

        paper_summaries = [
            {
                'index': paper['index'],
                'title': paper['title'],
                'abstract': paper['summary'][:300] + '...',
                'arxiv_id': paper['arxiv_id']
            }
            for paper in papers
        ]

        prompt = f"""Evaluate and rank these {len(papers)} arXiv papers for relevance.

Query: "{original_query}"
Focus: {refined_query['search_focus']}
Concepts: {', '.join(refined_query['key_concepts'][:3])}

Papers:
{json.dumps(paper_summaries, indent=1)}

Select TOP {top_n} by relevance. For each: index, score (0-100), reason (1 sentence), contributions (1 sentence).
Output JSON: {{"top_papers": [{{"index": 1, "relevance_score": 95, "relevance_reason": "...", "key_contributions": "..."}}], "overall_analysis": "..."}}"""

        try:
            response_schema = {
                "type": "object",
                "properties": {
                    "top_papers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "index": {"type": "integer"},
                                "relevance_score": {"type": "integer"},
                                "relevance_reason": {"type": "string"},
                                "key_contributions": {"type": "string"}
                            },
                            "required": ["index", "relevance_score", "relevance_reason", "key_contributions"]
                        }
                    },
                    "overall_analysis": {"type": "string"}
                },
                "required": ["top_papers", "overall_analysis"]
            }

            response = self.gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": response_schema
                }
            )

            ranking_data = json.loads(response.text)

            # Merge ranking data with original papers
            top_papers = []
            for ranked_paper in ranking_data['top_papers']:
                original_paper = next((p for p in papers if p['index'] == ranked_paper['index']), None)
                if original_paper:
                    merged_paper = {
                        **original_paper,
                        'relevance_score': ranked_paper['relevance_score'],
                        'relevance_reason': ranked_paper['relevance_reason'],
                        'key_contributions': ranked_paper['key_contributions']
                    }
                    top_papers.append(merged_paper)

            logger.info(f"Ranked {len(top_papers)} papers successfully")
            logger.info(f"Overall analysis: {ranking_data['overall_analysis'][:100]}...")
            return {
                'top_papers': top_papers,
                'overall_analysis': ranking_data['overall_analysis']
            }

        except Exception as error:
            logger.warning(f"Failed to rank papers with Gemini: {error}, using arXiv order")
            # Fallback: return top N papers by order
            return {
                'top_papers': papers[:top_n],
                'overall_analysis': 'Papers returned in relevance order from arXiv (Gemini ranking unavailable)'
            }

    def semantic_search(
        self,
        user_query: str,
        user_context: str = '',
        max_results: int = 20,
        top_n: int = 5,
        max_pdf_pages: int = 50
    ) -> Dict[str, Any]:
        """
        Main function to orchestrate the semantic search
        """
        logger.info("=" * 60)
        logger.info(f"Starting semantic search for: '{user_query}'")
        logger.info(f"Parameters: max_results={max_results}, top_n={top_n}, max_pdf_pages={max_pdf_pages}")
        logger.info("=" * 60)

        try:
            # Step 1: Refine the query
            refined_query = self.refine_user_query(user_query, user_context)

            time.sleep(1)

            # Step 2: Search arXiv
            papers = self.search_arxiv(refined_query, max_results)

            if len(papers) == 0:
                logger.warning("No papers found on arXiv for this query")
                return {
                    'error': 'No papers found',
                    'message': 'No papers found on arXiv for this query'
                }

            time.sleep(1)

            # Step 3: Filter papers by page count
            filtered_papers, excluded_papers = self.filter_papers_by_page_count(papers, max_pdf_pages)

            if len(filtered_papers) == 0:
                logger.warning("All papers exceeded the page limit")
                return {
                    'error': 'No papers after filtering',
                    'message': 'All papers exceed the page limit'
                }

            time.sleep(1)

            # Step 4: Rank papers with Gemini
            results = self.rank_papers_with_gemini(filtered_papers, user_query, refined_query, top_n)

            # Create array of top 5 PDF links
            top_5_links = [paper['pdf_link'] for paper in results['top_papers']]

            logger.info(f"Search complete! Returning {len(results['top_papers'])} top papers")
            logger.info("=" * 60)
            return {
                'query': user_query,
                'timestamp': datetime.now().isoformat(),
                'total_papers_found': len(papers),
                'papers_excluded_by_page_limit': len(excluded_papers),
                'papers_after_filtering': len(filtered_papers),
                'top_papers_count': len(results['top_papers']),
                'refined_query': refined_query,
                'overall_analysis': results['overall_analysis'],
                'top_papers': results['top_papers'],
                'top_5_links': top_5_links,
                'excluded_papers': excluded_papers
            }

        except Exception as error:
            logger.error(f"Search failed with exception: {error}", exc_info=True)
            return {
                'error': 'Search failed',
                'message': str(error)
            }


# Create singleton instance
arxiv_service = ArxivSemanticSearchService()
