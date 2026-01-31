from __future__ import annotations
import arxiv
from typing import Optional
from dataclasses import dataclass


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    pdf_url: str
    published_date: str
    categories: list[str]


class ArxivService:
    """Service for searching and fetching papers from ArXiv."""

    def __init__(self):
        self.client = arxiv.Client()

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "submitted"
    ) -> list[ArxivPaper]:
        """Search ArXiv for papers matching the query. Defaults to newest first."""
        sort_criterion = arxiv.SortCriterion.SubmittedDate
        if sort_by == "relevance":
            sort_criterion = arxiv.SortCriterion.Relevance
        elif sort_by == "updated":
            sort_criterion = arxiv.SortCriterion.LastUpdatedDate

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        for result in self.client.results(search):
            paper = ArxivPaper(
                arxiv_id=result.entry_id.split("/")[-1],
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                pdf_url=result.pdf_url,
                published_date=result.published.isoformat(),
                categories=result.categories
            )
            papers.append(paper)

        return papers

    async def get_by_id(self, arxiv_id: str) -> Optional[ArxivPaper]:
        """Fetch a specific paper by ArXiv ID."""
        # Clean the ID (remove version if present, or handle full URL)
        clean_id = arxiv_id.replace("https://arxiv.org/abs/", "").split("v")[0]

        search = arxiv.Search(id_list=[clean_id])

        results = list(self.client.results(search))
        if not results:
            return None

        result = results[0]
        return ArxivPaper(
            arxiv_id=result.entry_id.split("/")[-1],
            title=result.title,
            authors=[author.name for author in result.authors],
            abstract=result.summary,
            pdf_url=result.pdf_url,
            published_date=result.published.isoformat(),
            categories=result.categories
        )

    async def get_paper_content(self, arxiv_id: str) -> Optional[str]:
        """
        Get the full text content of a paper.
        Note: ArXiv doesn't provide full text via API, only PDF.
        For MVP, we'll use the abstract. Full PDF parsing can be added later.
        """
        paper = await self.get_by_id(arxiv_id)
        if not paper:
            return None

        # For MVP, return abstract as content
        # TODO: Add PDF download and text extraction for full content
        return paper.abstract


arxiv_service = ArxivService()
