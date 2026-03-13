"""
Test enhanced content validation with specific error messages
Tests for task 2.1: Improve content validation with specific error messages
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.documents import Document


# Mock the settings to avoid pydantic import issues
class MockSettings:
    pass


# Patch the imports before importing document_loaders
import unittest.mock as mock
sys.modules['app.core.config'] = mock.MagicMock(settings=MockSettings())

from app.services.document_loaders import EnhancedDocumentLoader


@pytest.fixture
def loader():
    """Create document loader instance"""
    return EnhancedDocumentLoader()


def test_validation_empty_documents(loader):
    """Test validation with empty documents list"""
    import asyncio
    result = asyncio.run(loader.validate_document_content(
        documents=[],
        filename="empty.pdf",
        file_type=".pdf"
    ))
    
    assert result["valid"] is False
    assert result["failure_reason"] == "no_documents"
    assert "empty.pdf" in result["error"]
    assert "stats" in result
    assert result["stats"]["document_count"] == 0


def test_validation_whitespace_only(loader):
    """Test validation with whitespace-only content"""
    import asyncio
    docs = [Document(page_content="   \n\n   \t\t   ", metadata={})]
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="whitespace.txt",
        file_type=".txt"
    ))
    
    assert result["valid"] is False
    # After stripping, whitespace-only content is treated as empty
    assert result["failure_reason"] in ["whitespace_only", "empty_content"]
    assert result["stats"]["non_whitespace_chars"] == 0


def test_validation_insufficient_content(loader):
    """Test validation with content below 10 character threshold"""
    import asyncio
    docs = [Document(page_content="Hi there", metadata={})]  # 8 characters
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="short.txt",
        file_type=".txt"
    ))
    
    assert result["valid"] is False
    assert result["failure_reason"] == "insufficient_content"
    assert "8 characters" in result["error"]
    assert "minimum required is 10" in result["error"]


def test_validation_minimum_threshold_pass(loader):
    """Test validation passes with exactly 10 characters"""
    import asyncio
    docs = [Document(page_content="Ten chars!", metadata={})]  # Exactly 10 characters
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="minimum.txt",
        file_type=".txt"
    ))
    
    assert result["valid"] is True
    assert "failure_reason" not in result
    assert result["stats"]["total_characters"] == 10


def test_validation_low_content_warning(loader):
    """Test warning for content between 10-50 characters"""
    import asyncio
    docs = [Document(page_content="This has twenty chars", metadata={})]  # 21 characters
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="low.txt",
        file_type=".txt"
    ))
    
    assert result["valid"] is True
    assert len(result["warnings"]) > 0
    assert "very little text content" in result["warnings"][0]
    assert "21 characters" in result["warnings"][0]


def test_validation_sufficient_content(loader):
    """Test validation passes with sufficient content"""
    import asyncio
    docs = [Document(
        page_content="This is a document with plenty of content to pass validation checks.",
        metadata={}
    )]
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="good.txt",
        file_type=".txt"
    ))
    
    assert result["valid"] is True
    assert result["stats"]["total_characters"] > 50
    assert result["stats"]["total_words"] > 10
    assert len(result["warnings"]) == 0


def test_validation_pdf_specific(loader):
    """Test PDF-specific validation warnings"""
    import asyncio
    # Use content with at least 10 characters but few words
    docs = [Document(page_content="PDF document test", metadata={})]  # 17 chars, 3 words
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="test.pdf",
        file_type=".pdf"
    ))
    
    assert result["valid"] is True  # Passes basic validation (>10 chars)
    assert result["content_type"] == "PDF document"
    # Should have warning about few words (less than 5)
    assert any("fewer than 5 words" in w or "words" in w for w in result["warnings"])


def test_validation_csv_specific(loader):
    """Test CSV-specific validation warnings"""
    import asyncio
    docs = [Document(page_content="A,B,C,D,E,F", metadata={})]  # Minimal data
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="data.csv",
        file_type=".csv"
    ))
    
    assert result["valid"] is True  # Passes basic validation
    assert result["content_type"] == "CSV data file"


def test_validation_sdf_specific(loader):
    """Test SDF-specific validation warnings"""
    import asyncio
    docs = [Document(
        page_content="Compound: Aspirin\nMolecular Formula: C9H8O4",
        metadata={}
    )]
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="molecule.sdf",
        file_type=".sdf"
    ))
    
    assert result["valid"] is True
    assert result["content_type"] == "chemical structure file"
    # Should not have warning about missing molecular data
    assert not any("molecular structure data" in w for w in result["warnings"])


def test_validation_sdf_missing_data(loader):
    """Test SDF validation warning when molecular data is missing"""
    import asyncio
    docs = [Document(page_content="Some random text without molecular data", metadata={})]
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="invalid.sdf",
        file_type=".sdf"
    ))
    
    assert result["valid"] is True  # Passes basic validation
    # Should have warning about missing molecular data
    assert any("molecular structure data" in w for w in result["warnings"])


def test_validation_stats_comprehensive(loader):
    """Test that validation returns comprehensive statistics"""
    import asyncio
    docs = [
        Document(page_content="Page one with some content here.", metadata={}),
        Document(page_content="Page two has different content.", metadata={}),
        Document(page_content="", metadata={}),  # Empty page
    ]
    result = asyncio.run(loader.validate_document_content(
        documents=docs,
        filename="multi.pdf",
        file_type=".pdf"
    ))
    
    assert result["valid"] is True
    stats = result["stats"]
    assert stats["document_count"] == 3
    assert stats["pages_with_content"] == 2
    assert stats["empty_pages"] == 1
    assert stats["total_characters"] > 0
    assert stats["total_words"] > 0
    assert stats["average_page_length"] > 0
    assert "content_type" in stats


def test_validation_content_type_detection(loader):
    """Test content type detection for different file types"""
    import asyncio
    test_cases = [
        (".pdf", "PDF document"),
        (".docx", "Word document"),
        (".txt", "text file"),
        (".csv", "CSV data file"),
        (".sdf", "chemical structure file"),
        (".xlsx", "Excel spreadsheet"),
        (".pptx", "PowerPoint presentation"),
    ]
    
    for file_type, expected_type in test_cases:
        docs = [Document(page_content="Test content for validation", metadata={})]
        result = asyncio.run(loader.validate_document_content(
            documents=docs,
            filename=f"test{file_type}",
            file_type=file_type
        ))
        assert result["content_type"] == expected_type, f"Failed for {file_type}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
