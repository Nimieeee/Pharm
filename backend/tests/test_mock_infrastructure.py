"""
Test to verify mock infrastructure is working correctly.

This test validates that the mock SSE and JSON response generators
work as expected before using them in actual multi-provider tests.
"""

import pytest
import asyncio
from conftest import MockSSEResponse, MockJSONResponse, create_mock_http_response


@pytest.mark.asyncio
async def test_mock_sse_response_success():
    """Test that MockSSEResponse generates correct SSE format."""
    chunks = ["Hello", " ", "world"]
    mock_response = MockSSEResponse(chunks, status_code=200)
    
    collected_chunks = []
    async for line in mock_response.aiter_lines():
        if line.startswith("data: ") and "[DONE]" not in line:
            # Extract the data part
            collected_chunks.append(line)
    
    # Should have 3 data lines (one per chunk)
    assert len(collected_chunks) == 3
    assert all(chunk.startswith("data: {") for chunk in collected_chunks)


@pytest.mark.asyncio
async def test_mock_sse_response_with_done_marker():
    """Test that MockSSEResponse includes [DONE] marker."""
    chunks = ["test"]
    mock_response = MockSSEResponse(chunks, status_code=200, include_done=True)
    
    lines = []
    async for line in mock_response.aiter_lines():
        lines.append(line)
    
    # Should have data line + [DONE] marker
    assert len(lines) == 2
    assert "data: [DONE]" in lines[-1]


def test_mock_sse_response_error_status():
    """Test that MockSSEResponse raises error for non-200 status."""
    mock_response = MockSSEResponse([], status_code=429)
    
    with pytest.raises(Exception, match="HTTP 429"):
        mock_response.raise_for_status()


def test_mock_json_response_success():
    """Test that MockJSONResponse returns correct JSON structure."""
    content = "Test response content"
    mock_response = MockJSONResponse(content, status_code=200)
    
    json_data = mock_response.json()
    
    assert json_data["choices"][0]["message"]["content"] == content
    assert json_data["object"] == "chat.completion"
    assert "id" in json_data


def test_mock_json_response_error_status():
    """Test that MockJSONResponse raises error for non-200 status."""
    mock_response = MockJSONResponse("", status_code=500)
    
    with pytest.raises(Exception, match="HTTP 500"):
        mock_response.raise_for_status()


def test_create_mock_http_response_streaming():
    """Test helper function creates streaming response."""
    response = create_mock_http_response(
        is_streaming=True,
        chunks=["test", "data"],
        status_code=200
    )
    
    assert isinstance(response, MockSSEResponse)
    assert response.status_code == 200


def test_create_mock_http_response_non_streaming():
    """Test helper function creates non-streaming response."""
    response = create_mock_http_response(
        content="test content",
        is_streaming=False,
        status_code=200
    )
    
    assert isinstance(response, MockJSONResponse)
    assert response.status_code == 200
    assert response.content == "test content"


def test_mock_provider_configs(mock_nvidia_config, mock_groq_config, mock_mistral_config):
    """Test that provider config fixtures are properly structured."""
    # Test NVIDIA config
    assert mock_nvidia_config["api_key"] == "nvapi-test-key"
    assert mock_nvidia_config["weight"] == 0.80
    assert mock_nvidia_config["rpm_limit"] == 40
    assert "fast" in mock_nvidia_config["models"]
    
    # Test Groq config
    assert mock_groq_config["api_key"] == "gsk-test-key"
    assert mock_groq_config["weight"] == 0.15
    assert mock_groq_config["rpm_limit"] == 30
    
    # Test Mistral config
    assert mock_mistral_config["api_key"] == "mistral-test-key"
    assert mock_mistral_config["weight"] == 0.05
    assert mock_mistral_config["rpm_limit"] == 2


def test_mock_environment_variables(mock_environment_variables, monkeypatch):
    """Test that environment variable mocking works."""
    import os
    
    assert os.getenv("NVIDIA_API_KEY") == "nvapi-test-key"
    assert os.getenv("GROQ_API_KEY") == "gsk-test-key"
    assert os.getenv("MISTRAL_API_KEY") == "mistral-test-key"


def test_mock_empty_environment(mock_empty_environment):
    """Test that empty environment fixture removes API keys."""
    import os
    
    assert os.getenv("NVIDIA_API_KEY") is None
    assert os.getenv("GROQ_API_KEY") is None
    assert os.getenv("MISTRAL_API_KEY") is None
