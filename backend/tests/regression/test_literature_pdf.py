import pytest
import httpx
from unittest.mock import patch, MagicMock
from app.services.literature_service import LiteratureService

@pytest.mark.asyncio
async def test_fetch_pdf_bytes_restricted():
    service = LiteratureService()
    
    # Mock httpx to return 403 Forbidden
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden access"
        mock_get.return_value = mock_resp
        
        with pytest.raises(Exception) as excinfo:
            await service.fetch_pdf_bytes("https://restricted-publisher.com/pdf")
        
        assert "403" in str(excinfo.value)
        assert "restricted" in str(excinfo.value)

@pytest.mark.asyncio
async def test_fetch_pdf_bytes_not_found():
    service = LiteratureService()
    
    # Mock httpx to return 404 Not Found
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not found"
        mock_get.return_value = mock_resp
        
        with pytest.raises(Exception) as excinfo:
            await service.fetch_pdf_bytes("https://missing-site.com/pdf")
        
        assert "404" in str(excinfo.value)

@pytest.mark.asyncio
async def test_fetch_pdf_bytes_success():
    service = LiteratureService()
    
    # Mock httpx to return 200 OK and PDF content
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"%PDF-1.4"
        mock_resp.headers = {"Content-Type": "application/pdf"}
        mock_get.return_value = mock_resp
        
        content = await service.fetch_pdf_bytes("https://open-access.com/pdf")
        assert content == b"%PDF-1.4"
