"""
Tests for backend.openrouter_client (Module 03)
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from backend.openrouter_client import OpenRouterClient, LLMError, LLMEmptyResponseError


@pytest.fixture
def mock_client():
    return OpenRouterClient(api_key="test-key", base_url="https://test", model="test-model")


@pytest.mark.asyncio
async def test_chat_completion_success(mock_client):
    # Mock the return value of AsyncClient.post
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello world!"}}]
    }
    mock_post.return_value = mock_response
    
    with patch("httpx.AsyncClient") as mock_httpx_client:
        mock_instance = AsyncMock()
        mock_instance.post = mock_post
        mock_httpx_client.return_value.__aenter__.return_value = mock_instance
        
        result = await mock_client.chat_completion([{"role": "user", "content": "Hi"}])
        
        assert result == "Hello world!"
        assert mock_post.called


@pytest.mark.asyncio
async def test_chat_completion_empty_response(mock_client):
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "   \n "}}]
    }
    mock_post.return_value = mock_response
    
    with patch("httpx.AsyncClient") as mock_httpx_client:
        mock_instance = AsyncMock()
        mock_instance.post = mock_post
        mock_httpx_client.return_value.__aenter__.return_value = mock_instance
        
        with pytest.raises(LLMEmptyResponseError, match="empty content"):
            await mock_client.chat_completion([{"role": "user", "content": "Hi"}])


@pytest.mark.asyncio
async def test_chat_completion_http_error(mock_client):
    mock_post = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPError("Network Error")
    mock_post.return_value = mock_response
    
    with patch("httpx.AsyncClient") as mock_httpx_client:
        mock_instance = AsyncMock()
        mock_instance.post = mock_post
        mock_httpx_client.return_value.__aenter__.return_value = mock_instance
        
        with pytest.raises(LLMError, match="Network Error"):
            await mock_client.chat_completion([{"role": "user", "content": "Hi"}])
