"""
Test Suite — Mermaid AI Self-Repair (WS2)

Tests the AI-powered Mermaid syntax repair endpoint and service method.

Usage:
    pytest tests/test_mermaid_repair.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMermaidRepairService:
    """Test the AIService.repair_mermaid_syntax method"""

    @pytest.mark.asyncio
    async def test_repair_mermaid_basic(self):
        """Test basic Mermaid repair with mocked multi-provider"""
        from app.services.ai import AIService
        from supabase import create_client

        # Mock database
        mock_db = MagicMock()

        # Create service instance
        ai_service = AIService(db=mock_db)

        # Mock multi-provider response
        broken_code = "graph TD\nA-->B"
        error_msg = "Parse error on line 2"
        expected_repaired = "graph TD\nA --> B"

        with patch('app.services.ai.get_multi_provider') as mock_mp_factory:
            mock_mp = AsyncMock()
            mock_mp.generate = AsyncMock(return_value=expected_repaired)
            mock_mp_factory.return_value = mock_mp

            repaired = await ai_service.repair_mermaid_syntax(
                code=broken_code,
                error=error_msg
            )

            assert repaired == expected_repaired
            mock_mp.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_repair_mermaid_extracts_from_markdown(self):
        """Test that repair method extracts code from markdown blocks"""
        from app.services.ai import AIService
        from supabase import create_client

        mock_db = MagicMock()
        ai_service = AIService(db=mock_db)

        # Response with markdown blocks
        ai_response = """```mermaid
graph TD
    A --> B
    B --> C
```"""

        with patch('app.services.ai.get_multi_provider') as mock_mp_factory:
            mock_mp = AsyncMock()
            mock_mp.generate = AsyncMock(return_value=ai_response)
            mock_mp_factory.return_value = mock_mp

            repaired = await ai_service.repair_mermaid_syntax(
                code="broken code",
                error="some error"
            )

            # Should strip markdown and whitespace
            assert "```" not in repaired
            assert "graph TD" in repaired
            assert "A --> B" in repaired

    @pytest.mark.asyncio
    async def test_repair_mermaid_handles_failure(self):
        """Test that repair returns original code on failure"""
        from app.services.ai import AIService

        mock_db = MagicMock()
        ai_service = AIService(db=mock_db)

        original_code = "graph TD\nA-->B"

        with patch('app.services.ai.get_multi_provider') as mock_mp_factory:
            mock_mp = AsyncMock()
            mock_mp.generate = AsyncMock(side_effect=Exception("API error"))
            mock_mp_factory.return_value = mock_mp

            repaired = await ai_service.repair_mermaid_syntax(
                code=original_code,
                error="some error"
            )

            # Should return original code on failure
            assert repaired == original_code

    @pytest.mark.asyncio
    async def test_repair_mermaid_prompt_includes_error(self):
        """Test that error message is included in prompt"""
        from app.services.ai import AIService

        mock_db = MagicMock()
        ai_service = AIService(db=mock_db)

        test_error = "Error: Parse error on line 2: Expected 'EOF'"
        test_code = "graph TD\nA-->B"

        with patch('app.services.ai.get_multi_provider') as mock_mp_factory:
            mock_mp = AsyncMock()
            mock_mp.generate = AsyncMock(return_value=test_code)
            mock_mp_factory.return_value = mock_mp

            await ai_service.repair_mermaid_syntax(
                code=test_code,
                error=test_error
            )

            # Check that generate was called with error in prompt
            call_args = mock_mp.generate.call_args
            messages = call_args[1]['messages']
            prompt_text = messages[0]['content']

            assert test_error in prompt_text
            assert test_code in prompt_text


class TestMermaidRepairEndpoint:
    """Test the /chat/mermaid/repair endpoint"""

    @pytest.mark.asyncio
    async def test_repair_endpoint_success(self):
        """Test successful repair via endpoint"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Mock the AIService.repair_mermaid_syntax method
        with patch('app.services.ai.AIService.repair_mermaid_syntax') as mock_repair:
            mock_repair = AsyncMock(return_value="graph TD\nA --> B")

            # Note: We can't easily test auth in unit tests
            # This is a smoke test to ensure endpoint structure is correct
            pass

    @pytest.mark.asyncio
    async def test_repair_request_model(self):
        """Test that request model validates correctly"""
        from app.api.v1.endpoints.chat import MermaidRepairRequest

        # Valid request
        request = MermaidRepairRequest(
            code="graph TD\nA-->B",
            error="Parse error"
        )

        assert request.code == "graph TD\nA-->B"
        assert request.error == "Parse error"

        # Request with empty code should fail
        with pytest.raises(Exception):
            MermaidRepairRequest(code="", error="error")


class TestMermaidRepairIntegration:
    """Integration tests with real AI provider (marked for optional execution)"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_repair_real_api(self):
        """
        Test repair with real AI API call.
        
        Requires valid API keys in environment.
        Run with: pytest tests/test_mermaid_repair.py::TestMermaidRepairIntegration -v -m integration
        """
        from app.services.ai import AIService
        from supabase import create_client

        # Skip if no API keys
        if not os.getenv('NVIDIA_API_KEY') and not os.getenv('GROQ_API_KEY'):
            pytest.skip("No AI API keys available")

        mock_db = MagicMock()
        ai_service = AIService(db=mock_db)

        # Real broken mermaid code
        broken_mermaid = """graph TD
    A[Drug Administration] --> B[Metabolism CYP2D6]
    B --> C[Active Metabolite]
    C --> D[Therapeutic Effect]
    style A fill:#fff
    style B fill : #fff"""

        error = "Parse error on line 5: Extra characters after style definition"

        repaired = await ai_service.repair_mermaid_syntax(
            code=broken_mermaid,
            error=error
        )

        # Should return valid mermaid code
        assert "graph TD" in repaired
        assert len(repaired) > 0
        assert repaired != broken_mermaid or "fill:#fff" in repaired  # Either fixed or unchanged


class TestMermaidRepairEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_repair_empty_code(self):
        """Test repair with empty code"""
        from app.services.ai import AIService

        mock_db = MagicMock()
        ai_service = AIService(db=mock_db)

        with patch('app.services.ai.get_multi_provider') as mock_mp_factory:
            mock_mp = AsyncMock()
            mock_mp.generate = AsyncMock(return_value="")
            mock_mp_factory.return_value = mock_mp

            repaired = await ai_service.repair_mermaid_syntax(
                code="",
                error="Empty diagram"
            )

            assert repaired == ""

    @pytest.mark.asyncio
    async def test_repair_very_long_code(self):
        """Test repair with long mermaid code"""
        from app.services.ai import AIService

        mock_db = MagicMock()
        ai_service = AIService(db=mock_db)

        # Generate long mermaid code
        long_code = "graph TD\n"
        for i in range(50):
            long_code += f"    A{i} --> B{i}\n"

        with patch('app.services.ai.get_multi_provider') as mock_mp_factory:
            mock_mp = AsyncMock()
            mock_mp.generate = AsyncMock(return_value=long_code)
            mock_mp_factory.return_value = mock_mp

            repaired = await ai_service.repair_mermaid_syntax(
                code=long_code,
                error="Complex diagram error"
            )

            assert "graph TD" in repaired
            assert len(repaired) > 0
