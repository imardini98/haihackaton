"""
Pytest configuration and fixtures for PodAsk integration tests.
"""

import os
import pytest
import httpx
from typing import AsyncGenerator

# Test configuration
API_URL = os.getenv("PODASK_API_URL", "https://amusing-luck-production-4d58.up.railway.app/api/v1")
TEST_EMAIL = os.getenv("PODASK_TEST_EMAIL", "imardinig@gmail.com")
TEST_PASSWORD = os.getenv("PODASK_TEST_PASSWORD", "password2026")


@pytest.fixture(scope="session")
def api_url() -> str:
    """API base URL."""
    return API_URL


@pytest.fixture(scope="session")
def test_credentials() -> dict:
    """Test user credentials."""
    return {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for API requests."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        yield client


@pytest.fixture
async def auth_token(async_client: httpx.AsyncClient, api_url: str, test_credentials: dict) -> str:
    """Get authentication token for test user."""
    response = await async_client.post(
        f"{api_url}/auth/signin",
        json=test_credentials
    )
    assert response.status_code == 200, f"Auth failed: {response.text}"
    data = response.json()
    return data["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Authorization headers with bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}
