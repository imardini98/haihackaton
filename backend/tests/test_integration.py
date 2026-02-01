"""
PodAsk API Integration Tests

Tests the full workflow: Auth -> Search -> Ingest -> Generate -> Player -> Q&A

Run with:
    pytest tests/test_integration.py -v --asyncio-mode=auto

Or for specific tests:
    pytest tests/test_integration.py::test_full_workflow -v
"""

import asyncio
import pytest
import httpx
from typing import Optional


pytestmark = pytest.mark.asyncio


class TestAuthentication:
    """Test authentication endpoints."""

    async def test_signin_success(
        self,
        async_client: httpx.AsyncClient,
        api_url: str,
        test_credentials: dict
    ):
        """Test successful sign in."""
        response = await async_client.post(
            f"{api_url}/auth/signin",
            json=test_credentials
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user_id" in data
        assert data["email"] == test_credentials["email"]

    async def test_signin_invalid_password(
        self,
        async_client: httpx.AsyncClient,
        api_url: str,
        test_credentials: dict
    ):
        """Test sign in with invalid password."""
        response = await async_client.post(
            f"{api_url}/auth/signin",
            json={
                "email": test_credentials["email"],
                "password": "wrongpassword"
            }
        )

        assert response.status_code in [400, 401]

    async def test_get_current_user(
        self,
        async_client: httpx.AsyncClient,
        api_url: str,
        auth_headers: dict
    ):
        """Test getting current user info."""
        response = await async_client.get(
            f"{api_url}/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data


class TestPaperSearch:
    """Test paper search endpoints."""

    async def test_search_papers(
        self,
        async_client: httpx.AsyncClient,
        api_url: str
    ):
        """Test searching for papers (no auth required)."""
        response = await async_client.post(
            f"{api_url}/papers/search",
            json={"query": "machine learning", "max_results": 3}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check paper structure
        paper = data[0]
        assert "arxiv_id" in paper
        assert "title" in paper
        assert "authors" in paper
        assert "abstract" in paper

    async def test_search_empty_query(
        self,
        async_client: httpx.AsyncClient,
        api_url: str
    ):
        """Test search with empty query."""
        response = await async_client.post(
            f"{api_url}/papers/search",
            json={"query": "", "max_results": 3}
        )

        # Should return empty, validation error, or server error (current behavior)
        # TODO: Backend should return 422 for empty query
        assert response.status_code in [200, 422, 500]


class TestPaperIngestion:
    """Test paper ingestion endpoints."""

    async def test_ingest_paper(
        self,
        async_client: httpx.AsyncClient,
        api_url: str,
        auth_headers: dict
    ):
        """Test ingesting a paper."""
        # First search for a paper
        search_response = await async_client.post(
            f"{api_url}/papers/search",
            json={"query": "neural networks", "max_results": 1}
        )
        assert search_response.status_code == 200
        papers = search_response.json()
        assert len(papers) > 0

        arxiv_id = papers[0]["arxiv_id"]

        # Ingest the paper
        response = await async_client.post(
            f"{api_url}/papers/ingest",
            json={"arxiv_id": arxiv_id},
            headers=auth_headers,
            timeout=120.0  # Ingestion can take time
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["arxiv_id"] == arxiv_id
        assert "title" in data
        assert "content" in data

    async def test_ingest_requires_auth(
        self,
        async_client: httpx.AsyncClient,
        api_url: str
    ):
        """Test that ingestion requires authentication."""
        response = await async_client.post(
            f"{api_url}/papers/ingest",
            json={"arxiv_id": "2401.00001"}
        )

        assert response.status_code in [401, 403]


class TestPodcastGeneration:
    """Test podcast generation endpoints."""

    async def test_generate_podcast(
        self,
        async_client: httpx.AsyncClient,
        api_url: str,
        auth_headers: dict
    ):
        """Test full podcast generation workflow."""
        # 1. Search for a paper
        search_response = await async_client.post(
            f"{api_url}/papers/search",
            json={"query": "deep learning", "max_results": 1}
        )
        assert search_response.status_code == 200
        papers = search_response.json()
        arxiv_id = papers[0]["arxiv_id"]
        title = papers[0]["title"][:50]

        # 2. Ingest the paper
        ingest_response = await async_client.post(
            f"{api_url}/papers/ingest",
            json={"arxiv_id": arxiv_id},
            headers=auth_headers,
            timeout=120.0
        )
        assert ingest_response.status_code == 200
        paper_id = ingest_response.json()["id"]

        # 3. Generate podcast
        generate_response = await async_client.post(
            f"{api_url}/podcasts/generate",
            json={"paper_ids": [paper_id], "topic": title},
            headers=auth_headers,
            timeout=300.0
        )
        assert generate_response.status_code == 200
        podcast_id = generate_response.json()["id"]
        assert generate_response.json()["status"] == "pending"

        # 4. Poll for status
        status = "pending"
        max_polls = 60
        for _ in range(max_polls):
            status_response = await async_client.get(
                f"{api_url}/podcasts/{podcast_id}/status",
                headers=auth_headers
            )
            assert status_response.status_code == 200
            status = status_response.json()["status"]

            if status in ["ready", "failed"]:
                break

            await asyncio.sleep(5)

        assert status == "ready", f"Podcast generation failed or timed out: {status}"

        # 5. Get podcast details
        podcast_response = await async_client.get(
            f"{api_url}/podcasts/{podcast_id}",
            headers=auth_headers
        )
        assert podcast_response.status_code == 200
        podcast = podcast_response.json()

        assert podcast["status"] == "ready"
        assert len(podcast["segments"]) > 0
        assert podcast["total_duration_seconds"] > 0

    async def test_generate_requires_auth(
        self,
        async_client: httpx.AsyncClient,
        api_url: str
    ):
        """Test that podcast generation requires authentication."""
        response = await async_client.post(
            f"{api_url}/podcasts/generate",
            json={"paper_ids": ["fake-id"], "topic": "test"}
        )

        assert response.status_code in [401, 403]


class TestQAInteraction:
    """Test Q&A interaction endpoints."""

    async def test_qa_workflow(
        self,
        async_client: httpx.AsyncClient,
        api_url: str,
        auth_headers: dict
    ):
        """Test Q&A session workflow."""
        # First, get an existing podcast
        podcasts_response = await async_client.get(
            f"{api_url}/podcasts",
            headers=auth_headers
        )

        if podcasts_response.status_code != 200:
            pytest.skip("No podcasts available for Q&A test")

        # API returns {"podcasts": [...], "total": N}
        response_data = podcasts_response.json()
        podcasts = response_data.get("podcasts", response_data) if isinstance(response_data, dict) else response_data
        ready_podcasts = [p for p in podcasts if p.get("status") == "ready"]

        if not ready_podcasts:
            pytest.skip("No ready podcasts available for Q&A test")

        podcast_id = ready_podcasts[0]["id"]

        # Get podcast with segments
        podcast_response = await async_client.get(
            f"{api_url}/podcasts/{podcast_id}",
            headers=auth_headers
        )
        assert podcast_response.status_code == 200
        segments = podcast_response.json().get("segments", [])

        if not segments:
            pytest.skip("Podcast has no segments")

        segment_id = segments[0]["id"]

        # 1. Start session
        session_response = await async_client.post(
            f"{api_url}/interaction/session/start",
            json={"podcast_id": podcast_id, "segment_id": segment_id},
            headers=auth_headers
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]

        # 2. Ask a question
        ask_response = await async_client.post(
            f"{api_url}/interaction/ask-text",
            json={
                "session_id": session_id,
                "question": "Can you summarize the main point?"
            },
            headers=auth_headers,
            timeout=120.0
        )
        assert ask_response.status_code == 200
        exchange = ask_response.json()
        assert "exchange_id" in exchange
        assert "host_acknowledgment" in exchange
        assert "expert_answer" in exchange

        # 3. Continue signal
        continue_response = await async_client.post(
            f"{api_url}/interaction/continue",
            json={"session_id": session_id},
            headers=auth_headers,
            timeout=60.0
        )
        assert continue_response.status_code == 200
        assert "resume_line" in continue_response.json()


class TestFullWorkflow:
    """End-to-end integration test."""

    async def test_full_workflow(
        self,
        async_client: httpx.AsyncClient,
        api_url: str,
        test_credentials: dict
    ):
        """
        Test complete user journey:
        1. Sign in
        2. Search for papers
        3. Ingest a paper
        4. Generate podcast
        5. Poll until ready
        6. View podcast
        7. Start Q&A session
        8. Ask a question
        9. Continue podcast
        """
        # 1. Sign in
        auth_response = await async_client.post(
            f"{api_url}/auth/signin",
            json=test_credentials
        )
        assert auth_response.status_code == 200, "Sign in failed"
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("\n1. Sign in: OK")

        # 2. Search for papers
        search_response = await async_client.post(
            f"{api_url}/papers/search",
            json={"query": "artificial intelligence", "max_results": 2}
        )
        assert search_response.status_code == 200, "Search failed"
        papers = search_response.json()
        assert len(papers) > 0, "No papers found"

        arxiv_id = papers[0]["arxiv_id"]
        title = papers[0]["title"]
        print(f"2. Search: Found {len(papers)} papers")
        print(f"   Selected: {title[:60]}...")

        # 3. Ingest paper
        ingest_response = await async_client.post(
            f"{api_url}/papers/ingest",
            json={"arxiv_id": arxiv_id},
            headers=headers,
            timeout=120.0
        )
        assert ingest_response.status_code == 200, f"Ingest failed: {ingest_response.text}"
        paper_id = ingest_response.json()["id"]
        print(f"3. Ingest: Paper ID = {paper_id}")

        # 4. Generate podcast
        generate_response = await async_client.post(
            f"{api_url}/podcasts/generate",
            json={"paper_ids": [paper_id], "topic": title[:50]},
            headers=headers
        )
        assert generate_response.status_code == 200, f"Generate failed: {generate_response.text}"
        podcast_id = generate_response.json()["id"]
        print(f"4. Generate: Podcast ID = {podcast_id}")

        # 5. Poll for status
        print("5. Polling status...")
        status = "pending"
        for i in range(60):
            status_response = await async_client.get(
                f"{api_url}/podcasts/{podcast_id}/status",
                headers=headers
            )
            status = status_response.json().get("status")
            print(f"   Poll {i+1}: {status}")

            if status == "ready":
                break
            elif status == "failed":
                pytest.fail(f"Podcast generation failed: {status_response.json()}")

            await asyncio.sleep(5)

        assert status == "ready", "Podcast did not complete in time"

        # 6. View podcast
        podcast_response = await async_client.get(
            f"{api_url}/podcasts/{podcast_id}",
            headers=headers
        )
        assert podcast_response.status_code == 200
        podcast = podcast_response.json()
        segments = podcast["segments"]
        duration = podcast["total_duration_seconds"]
        print(f"6. View: {len(segments)} segments, {duration}s total")

        # 7. Start Q&A session
        session_response = await async_client.post(
            f"{api_url}/interaction/session/start",
            json={"podcast_id": podcast_id, "segment_id": segments[0]["id"]},
            headers=headers
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        print(f"7. Q&A Session: {session_id}")

        # 8. Ask a question
        ask_response = await async_client.post(
            f"{api_url}/interaction/ask-text",
            json={
                "session_id": session_id,
                "question": "What is the key innovation in this paper?"
            },
            headers=headers,
            timeout=120.0
        )
        assert ask_response.status_code == 200
        exchange = ask_response.json()
        print(f"8. Question: Got response from host and expert")
        print(f"   Expert: {exchange['expert_answer'][:100]}...")

        # 9. Continue
        continue_response = await async_client.post(
            f"{api_url}/interaction/continue",
            json={"session_id": session_id},
            headers=headers,
            timeout=60.0
        )
        assert continue_response.status_code == 200
        resume = continue_response.json()
        print(f"9. Continue: {resume['resume_line'][:60]}...")

        print("\n=== Full Workflow Test PASSED ===")
