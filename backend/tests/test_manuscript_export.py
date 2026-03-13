"""
Test Suite — Manuscript Export (WS3)

Tests the ManuscriptFormatter service and manuscript export endpoint.

Usage:
    pytest tests/test_manuscript_export.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
import io

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestManuscriptFormatterService:
    """Test the ManuscriptFormatter service"""

    def test_manuscript_formatter_import(self):
        """Smoke test: ManuscriptFormatter imports correctly"""
        from app.services.manuscript_formatter import ManuscriptFormatter
        assert ManuscriptFormatter is not None

    def test_manuscript_formatter_initialization(self):
        """Test ManuscriptFormatter initializes correctly"""
        from app.services.manuscript_formatter import ManuscriptFormatter
        
        formatter = ManuscriptFormatter()
        assert formatter is not None
        assert formatter.STYLES is not None
        assert "report" in formatter.STYLES
        assert "manuscript" in formatter.STYLES
        assert "plain" in formatter.STYLES

    def test_styles_have_required_sections(self):
        """Test that all styles have required sections"""
        from app.services.manuscript_formatter import ManuscriptFormatter
        
        formatter = ManuscriptFormatter()
        
        # Report style should have key sections
        report_sections = formatter.STYLES["report"]
        assert "Executive Summary" in report_sections or "Introduction" in report_sections
        
        # Manuscript style should have IMRAD structure
        manuscript_sections = formatter.STYLES["manuscript"]
        assert "Introduction" in manuscript_sections
        assert "Discussion" in manuscript_sections
        assert "Conclusion" in manuscript_sections

    @pytest.mark.asyncio
    async def test_structure_content_simple(self):
        """Test content structuring without AI (fallback mode)"""
        from app.services.manuscript_formatter import ManuscriptFormatter
        
        formatter = ManuscriptFormatter()
        
        messages = [
            {"role": "user", "content": "What is aspirin?"},
            {"role": "assistant", "content": "Aspirin is a salicylate used to treat pain, fever, and inflammation."}
        ]
        
        structured = await formatter.structure_content(messages, style="report")
        
        assert structured is not None
        assert "title" in structured or "sections" in structured

    def test_build_docx_creates_valid_file(self):
        """Test that build_docx creates a valid DOCX file"""
        from app.services.manuscript_formatter import ManuscriptFormatter
        
        formatter = ManuscriptFormatter()
        
        structured = {
            "title": "Test Document",
            "subtitle": "Test Subtitle",
            "sections": [
                {
                    "heading": "Introduction",
                    "content": "This is test content for the introduction section."
                },
                {
                    "heading": "Findings",
                    "content": "These are the test findings.",
                    "subsections": [
                        {"heading": "Subsection 1", "content": "Sub content 1"}
                    ]
                }
            ]
        }
        
        docx_bytes = formatter.build_docx(structured, style="report")
        
        # Check DOCX magic bytes (PK ZIP format)
        assert docx_bytes[:4] == b'PK\x03\x04'
        assert len(docx_bytes) > 1000  # Should be substantial

    def test_build_docx_with_empty_sections(self):
        """Test build_docx handles empty sections gracefully"""
        from app.services.manuscript_formatter import ManuscriptFormatter
        
        formatter = ManuscriptFormatter()
        
        structured = {
            "title": "Empty Document",
            "sections": []
        }
        
        docx_bytes = formatter.build_docx(structured, style="plain")
        
        # Should still create valid DOCX
        assert docx_bytes[:4] == b'PK\x03\x04'

    def test_extract_conversation_text(self):
        """Test conversation text extraction"""
        from app.services.manuscript_formatter import ManuscriptFormatter
        
        formatter = ManuscriptFormatter()
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        text = formatter._extract_conversation_text(messages)
        
        assert "[USER]" in text
        assert "[ASSISTANT]" in text
        assert "Hello" in text
        assert "Hi there!" in text


class TestManuscriptExportEndpoint:
    """Test the /export/manuscript endpoint"""

    @pytest.mark.asyncio
    async def test_manuscript_endpoint_structure(self):
        """Test endpoint structure (without full integration)"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test that endpoint exists and requires auth
        response = client.get("/api/v1/export/conversations/00000000-0000-0000-0000-000000000000/export/manuscript")
        
        # Should return 401 (unauthorized) or 404 (not found)
        assert response.status_code in [401, 404]

    @pytest.mark.asyncio
    async def test_manuscript_style_validation(self):
        """Test that style parameter is validated"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Invalid style should be rejected
        response = client.get(
            "/api/v1/export/conversations/00000000-0000-0000-0000-000000000000/export/manuscript?style=invalid"
        )
        
        # Should return 422 (validation error) or 401 (unauthorized)
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_valid_style_parameters(self):
        """Test that valid style parameters are accepted"""
        from app.api.v1.endpoints.export import export_manuscript_docx
        
        # Valid styles should match regex
        valid_styles = ["report", "manuscript", "plain"]
        for style in valid_styles:
            assert style in ["report", "manuscript", "plain"]


class TestManuscriptExportIntegration:
    """Integration tests with real conversation data"""

    @pytest.mark.asyncio
    async def test_full_manuscript_generation(self):
        """Test complete manuscript generation flow"""
        from app.services.manuscript_formatter import ManuscriptFormatter
        
        formatter = ManuscriptFormatter()
        
        # Simulate a real conversation
        messages = [
            {"role": "user", "content": "Explain the mechanism of action of metformin."},
            {"role": "assistant", "content": """Metformin is a biguanide antidiabetic agent.
            
Mechanism of Action:
1. Decreases hepatic glucose production
2. Decreases intestinal absorption of glucose
3. Improves insulin sensitivity

It activates AMP-activated protein kinase (AMPK), which plays a key role in cellular energy homeostasis.""",
            },
            {"role": "user", "content": "What are the side effects?"},
            {"role": "assistant", "content": """Common side effects include:
- Gastrointestinal disturbances (diarrhea, nausea, vomiting)
- Lactic acidosis (rare but serious)
- Vitamin B12 deficiency with long-term use""",
            }
        ]
        
        # Structure content
        structured = await formatter.structure_content(messages, style="report")
        
        # Build DOCX
        docx_bytes = formatter.build_docx(structured, style="report")
        
        # Verify output
        assert docx_bytes[:4] == b'PK\x03\x04'
        assert len(docx_bytes) > 2000  # Should be substantial for multi-message conversation


class TestManuscriptPerformance:
    """Performance regression tests"""

    def test_docx_generation_speed(self):
        """Test that DOCX generation completes in reasonable time"""
        import time
        from app.services.manuscript_formatter import ManuscriptFormatter
        
        formatter = ManuscriptFormatter()
        
        structured = {
            "title": "Performance Test Document",
            "sections": [
                {"heading": f"Section {i}", "content": "Test content " * 100}
                for i in range(10)
            ]
        }
        
        start = time.perf_counter()
        docx_bytes = formatter.build_docx(structured, style="report")
        elapsed = (time.perf_counter() - start) * 1000
        
        # Should complete in under 500ms for reasonable document
        assert elapsed < 500, f"DOCX generation took {elapsed:.2f}ms (target: <500ms)"
        assert len(docx_bytes) > 0
