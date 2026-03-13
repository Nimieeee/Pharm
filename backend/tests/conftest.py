"""
Pytest configuration and shared fixtures for multi-provider tests.

This module provides mock provider fixtures, SSE streaming generators,
and HTTP response mocking utilities for testing the multi-provider system.
"""

import pytest
import json
import asyncio
import os
from typing import List, Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch


# Set up environment variables before any imports
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run."""
    os.environ.setdefault("SUPABASE_URL", "http://test-supabase.com")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("NVIDIA_API_KEY", "")
    os.environ.setdefault("GROQ_API_KEY", "")
    os.environ.setdefault("MISTRAL_API_KEY", "")
    yield
    # Cleanup not needed as these are test values


@pytest.fixture(autouse=True)
def event_loop():
    """Create an event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings object for tests."""
    from unittest.mock import MagicMock
    mock_settings_obj = MagicMock()
    mock_settings_obj.SUPABASE_URL = "http://test-supabase.com"
    mock_settings_obj.SUPABASE_ANON_KEY = "test-anon-key"
    mock_settings_obj.NVIDIA_API_KEY = None
    mock_settings_obj.GROQ_API_KEY = None
    mock_settings_obj.MISTRAL_API_KEY = None
    
    with patch('app.services.multi_provider.settings', mock_settings_obj):
        yield mock_settings_obj


# Mock SSE streaming response generator
class MockSSEResponse:
    """Mock Server-Sent Events (SSE) streaming response."""
    
    def __init__(self, chunks: List[str], status_code: int = 200, include_done: bool = True):
        """
        Initialize mock SSE response.
        
        Args:
            chunks: List of content chunks to stream
            status_code: HTTP status code (200, 429, 500, etc.)
            include_done: Whether to include [DONE] marker at end
        """
        self.chunks = chunks
        self.status_code = status_code
        self.include_done = include_done
        self.headers = {"content-type": "text/event-stream"}
    
    async def aiter_lines(self) -> AsyncGenerator[str, None]:
        """Async generator that yields SSE formatted lines."""
        for chunk in self.chunks:
            # Format as SSE with proper JSON structure
            data = {
                "id": "chatcmpl-test",
                "object": "chat.completion.chunk",
                "created": 1704067200,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(data)}"
        
        if self.include_done:
            yield "data: [DONE]"
    
    def raise_for_status(self):
        """Raise exception for non-200 status codes."""
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")


# Mock non-streaming JSON response
class MockJSONResponse:
    """Mock JSON response for non-streaming requests."""
    
    def __init__(self, content: str, status_code: int = 200):
        """
        Initialize mock JSON response.
        
        Args:
            content: Complete response content
            status_code: HTTP status code (200, 429, 500, etc.)
        """
        self.content = content
        self.status_code = status_code
        self.headers = {"content-type": "application/json"}
        self._json_data = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1704067200,
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ]
        }
    
    def json(self) -> Dict[str, Any]:
        """Return JSON response data."""
        return self._json_data
    
    def raise_for_status(self):
        """Raise exception for non-200 status codes."""
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")


# Fixtures for mock providers
@pytest.fixture
def mock_nvidia_config():
    """Mock NVIDIA provider configuration."""
    return {
        "api_key": "nvapi-test-key",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "models": {
            "fast": "nvidia/llama-3.1-nemotron-70b-instruct",
            "detailed": "qwen/qwen3.5-397b-a17b",
            "deep_research": "qwen/qwen3.5-397b-a17b"
        },
        "weight": 0.80,
        "rpm_limit": 40
    }


@pytest.fixture
def mock_groq_config():
    """Mock Groq provider configuration."""
    return {
        "api_key": "gsk-test-key",
        "base_url": "https://api.groq.com/openai/v1",
        "models": {
            "fast": "llama-3.1-8b-instant",
            "detailed": "llama-3.3-70b-versatile",
            "deep_research": "llama-3.3-70b-versatile"
        },
        "weight": 0.15,
        "rpm_limit": 30
    }


@pytest.fixture
def mock_mistral_config():
    """Mock Mistral provider configuration."""
    return {
        "api_key": "mistral-test-key",
        "base_url": "https://api.mistral.ai/v1",
        "models": {
            "fast": "mistral-small-latest",
            "detailed": "mistral-large-latest",
            "deep_research": "mistral-large-latest"
        },
        "weight": 0.05,
        "rpm_limit": 2
    }


@pytest.fixture
def mock_sse_success_response():
    """Mock successful SSE streaming response."""
    chunks = ["Hello", " ", "world", "!"]
    return MockSSEResponse(chunks, status_code=200)


@pytest.fixture
def mock_sse_rate_limit_response():
    """Mock SSE response with 429 rate limit error."""
    return MockSSEResponse([], status_code=429, include_done=False)


@pytest.fixture
def mock_sse_server_error_response():
    """Mock SSE response with 500 server error."""
    return MockSSEResponse([], status_code=500, include_done=False)


@pytest.fixture
def mock_json_success_response():
    """Mock successful JSON response."""
    return MockJSONResponse("This is a complete response.", status_code=200)


@pytest.fixture
def mock_json_rate_limit_response():
    """Mock JSON response with 429 rate limit error."""
    return MockJSONResponse("", status_code=429)


@pytest.fixture
def mock_json_server_error_response():
    """Mock JSON response with 500 server error."""
    return MockJSONResponse("", status_code=500)


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for HTTP request mocking."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Mock environment variables for API keys."""
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-test-key")


@pytest.fixture
def mock_empty_environment(monkeypatch):
    """Mock empty environment (no API keys configured)."""
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)


# Helper function to create mock HTTP responses
def create_mock_http_response(
    content: str = "",
    status_code: int = 200,
    is_streaming: bool = False,
    chunks: List[str] = None
) -> Mock:
    """
    Create a mock HTTP response for testing.
    
    Args:
        content: Response content (for non-streaming)
        status_code: HTTP status code
        is_streaming: Whether this is a streaming response
        chunks: List of content chunks (for streaming)
    
    Returns:
        Mock response object
    """
    if is_streaming:
        chunks = chunks or ["test", " ", "response"]
        return MockSSEResponse(chunks, status_code)
    else:
        return MockJSONResponse(content, status_code)


# Helper function to create malformed SSE responses for testing robustness
def create_malformed_sse_response(malformed_type: str = "invalid_json") -> MockSSEResponse:
    """
    Create malformed SSE response for testing error handling.
    
    Args:
        malformed_type: Type of malformation (invalid_json, missing_content, etc.)
    
    Returns:
        MockSSEResponse with malformed data
    """
    class MalformedSSEResponse(MockSSEResponse):
        def __init__(self, malformed_type: str):
            super().__init__([], status_code=200)
            self.malformed_type = malformed_type
        
        async def aiter_lines(self) -> AsyncGenerator[str, None]:
            if self.malformed_type == "invalid_json":
                yield "data: {invalid json"
            elif self.malformed_type == "missing_content":
                yield 'data: {"choices": [{"delta": {}}]}'
            elif self.malformed_type == "empty_choices":
                yield 'data: {"choices": []}'
            yield "data: [DONE]"
    
    return MalformedSSEResponse(malformed_type)
