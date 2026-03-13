"""
Test error categorization in document processing
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock the settings and dependencies before importing document_loaders
from unittest.mock import MagicMock
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = MagicMock()

from app.services.document_loaders import (
    DocumentProcessingError,
    ErrorCategory,
    ErrorMessageTemplates
)


class TestErrorCategorization:
    """Test error categorization and message templates"""
    
    def test_error_categories_defined(self):
        """Test that all error categories are defined"""
        assert hasattr(ErrorCategory, 'EMPTY_CONTENT')
        assert hasattr(ErrorCategory, 'ENCODING_ERROR')
        assert hasattr(ErrorCategory, 'CORRUPTED_FILE')
        assert hasattr(ErrorCategory, 'UNSUPPORTED_FORMAT')
        assert hasattr(ErrorCategory, 'INSUFFICIENT_CONTENT')
        assert hasattr(ErrorCategory, 'PROCESSING_ERROR')
        assert hasattr(ErrorCategory, 'VALIDATION_ERROR')
        assert hasattr(ErrorCategory, 'FILE_NOT_FOUND')
        assert hasattr(ErrorCategory, 'PERMISSION_ERROR')
    
    def test_unsupported_format_message(self):
        """Test unsupported format error message template"""
        message = ErrorMessageTemplates.unsupported_format(
            "test.xyz",
            ".xyz",
            [".pdf", ".txt", ".docx"]
        )
        assert "test.xyz" in message
        assert ".xyz" in message
        assert ".pdf" in message
        assert "Unsupported file format" in message
    
    def test_empty_content_message(self):
        """Test empty content error message template"""
        message = ErrorMessageTemplates.empty_content("empty.pdf")
        assert "empty.pdf" in message
        assert "No content could be extracted" in message
        assert "empty" in message.lower()
    
    def test_encoding_error_message(self):
        """Test encoding error message template"""
        message = ErrorMessageTemplates.encoding_error(
            "test.txt",
            ["utf-8", "latin-1", "cp1252"]
        )
        assert "test.txt" in message
        assert "utf-8" in message
        assert "latin-1" in message
        assert "decode" in message.lower()
    
    def test_corrupted_file_message(self):
        """Test corrupted file error message template"""
        message = ErrorMessageTemplates.corrupted_file("broken.pdf", "PDF")
        assert "broken.pdf" in message
        assert "corrupted" in message.lower()
        assert "PDF" in message
    
    def test_insufficient_content_message(self):
        """Test insufficient content error message template"""
        message = ErrorMessageTemplates.insufficient_content("short.txt", 5, 10)
        assert "short.txt" in message
        assert "5" in message
        assert "10" in message
        assert "Insufficient content" in message
    
    def test_processing_error_message(self):
        """Test generic processing error message template"""
        message = ErrorMessageTemplates.processing_error("test.pdf", "Unknown error")
        assert "test.pdf" in message
        assert "Unknown error" in message
        assert "Failed to process" in message
    
    def test_validation_error_message(self):
        """Test validation error message template"""
        message = ErrorMessageTemplates.validation_error("test.pdf", "Content too short")
        assert "test.pdf" in message
        assert "Content too short" in message
        assert "Validation failed" in message
    
    def test_file_not_found_message(self):
        """Test file not found error message template"""
        message = ErrorMessageTemplates.file_not_found("missing.pdf")
        assert "missing.pdf" in message
        assert "not found" in message.lower()
    
    def test_permission_error_message(self):
        """Test permission error message template"""
        message = ErrorMessageTemplates.permission_error("locked.pdf")
        assert "locked.pdf" in message
        assert "Permission denied" in message


class TestDocumentProcessingError:
    """Test DocumentProcessingError exception class"""
    
    def test_error_creation_with_defaults(self):
        """Test creating error with default parameters"""
        error = DocumentProcessingError("Test error")
        assert error.message == "Test error"
        assert error.error_category == "processing_error"
        assert error.is_user_error is True
        assert error.details == {}
    
    def test_error_creation_with_category(self):
        """Test creating error with specific category"""
        error = DocumentProcessingError(
            "Empty file",
            error_category=ErrorCategory.EMPTY_CONTENT
        )
        assert error.message == "Empty file"
        assert error.error_category == ErrorCategory.EMPTY_CONTENT
        assert error.is_user_error is True
    
    def test_error_creation_as_system_error(self):
        """Test creating system error (not user error)"""
        error = DocumentProcessingError(
            "Database connection failed",
            error_category=ErrorCategory.PROCESSING_ERROR,
            is_user_error=False
        )
        assert error.is_user_error is False
    
    def test_error_with_details(self):
        """Test creating error with additional details"""
        details = {
            "filename": "test.pdf",
            "file_size": 0,
            "attempted_encodings": ["utf-8", "latin-1"]
        }
        error = DocumentProcessingError(
            "Processing failed",
            error_category=ErrorCategory.ENCODING_ERROR,
            details=details
        )
        assert error.details == details
        assert error.details["filename"] == "test.pdf"
    
    def test_error_to_dict(self):
        """Test converting error to dictionary"""
        error = DocumentProcessingError(
            "Test error",
            error_category=ErrorCategory.CORRUPTED_FILE,
            is_user_error=True,
            details={"filename": "test.pdf"}
        )
        error_dict = error.to_dict()
        
        assert error_dict["error"] == "Test error"
        assert error_dict["error_category"] == ErrorCategory.CORRUPTED_FILE
        assert error_dict["error_type"] == "user_error"
        assert error_dict["details"]["filename"] == "test.pdf"
    
    def test_error_to_dict_system_error(self):
        """Test converting system error to dictionary"""
        error = DocumentProcessingError(
            "System failure",
            is_user_error=False
        )
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "system_error"
    
    def test_error_string_representation(self):
        """Test that error can be converted to string"""
        error = DocumentProcessingError("Test error message")
        assert str(error) == "Test error message"
    
    def test_user_error_vs_system_error_distinction(self):
        """Test distinguishing between user and system errors"""
        user_error = DocumentProcessingError(
            "Invalid file format",
            error_category=ErrorCategory.UNSUPPORTED_FORMAT,
            is_user_error=True
        )
        system_error = DocumentProcessingError(
            "Database connection failed",
            error_category=ErrorCategory.PROCESSING_ERROR,
            is_user_error=False
        )
        
        assert user_error.is_user_error is True
        assert system_error.is_user_error is False
        assert user_error.to_dict()["error_type"] == "user_error"
        assert system_error.to_dict()["error_type"] == "system_error"
