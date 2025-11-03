"""
Comprehensive error handling tests for document processing
Tests empty files, unsupported formats, corrupted files, encoding errors, and insufficient content
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock settings
from unittest.mock import MagicMock
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = MagicMock()

from app.services.document_loaders import (
    EnhancedDocumentLoader,
    DocumentProcessingError,
    ErrorCategory,
    ErrorMessageTemplates
)


@pytest.fixture
def loader():
    """Create document loader instance"""
    return EnhancedDocumentLoader()


class TestEmptyFileUpload:
    """Test empty file upload scenarios - Requirement 1.1"""
    
    @pytest.mark.asyncio
    async def test_empty_bytes(self, loader):
        """Test uploading completely empty file (0 bytes)"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'', 'empty.pdf')
        
        error = exc_info.value
        assert error.error_category == ErrorCategory.EMPTY_CONTENT
        assert 'empty.pdf' in error.message
        assert error.is_user_error is True
    
    @pytest.mark.asyncio
    async def test_empty_pdf(self, loader):
        """Test PDF file with no content"""
        # Create minimal PDF structure but with no actual content
        empty_pdf = b'%PDF-1.4\n%%EOF'
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(empty_pdf, 'empty.pdf')
        
        error = exc_info.value
        assert error.error_category in [ErrorCategory.EMPTY_CONTENT, ErrorCategory.CORRUPTED_FILE]
    
    @pytest.mark.asyncio
    async def test_empty_text_file(self, loader):
        """Test text file with no content"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'', 'empty.txt')
        
        error = exc_info.value
        assert error.error_category == ErrorCategory.EMPTY_CONTENT
        assert 'empty' in error.message.lower()
    
    @pytest.mark.asyncio
    async def test_whitespace_only_file(self, loader):
        """Test file containing only whitespace"""
        whitespace_content = b'   \n\n   \t\t   \n'
        
        # This should load but fail validation
        docs = await loader.load_document(whitespace_content, 'whitespace.txt')
        
        # Validate the content
        validation = await loader.validate_document_content(docs, 'whitespace.txt', '.txt')
        assert validation['valid'] is False
        assert validation['failure_reason'] in ['whitespace_only', 'empty_content']


class TestUnsupportedFormat:
    """Test unsupported file format scenarios - Requirement 1.1"""
    
    @pytest.mark.asyncio
    async def test_unsupported_extension(self, loader):
        """Test file with unsupported extension"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'some content', 'file.xyz')
        
        error = exc_info.value
        assert error.error_category == ErrorCategory.UNSUPPORTED_FORMAT
        assert '.xyz' in error.message
        assert 'Supported formats' in error.message
    
    @pytest.mark.asyncio
    async def test_unsupported_format_lists_supported(self, loader):
        """Test that unsupported format error lists all supported formats"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'content', 'file.unknown')
        
        error = exc_info.value
        # Should list common formats
        assert '.pdf' in error.message
        assert '.txt' in error.message
        assert '.docx' in error.message
    
    @pytest.mark.asyncio
    async def test_no_extension(self, loader):
        """Test file with no extension"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'content', 'filename')
        
        error = exc_info.value
        assert error.error_category == ErrorCategory.UNSUPPORTED_FORMAT
    
    @pytest.mark.asyncio
    async def test_wrong_extension(self, loader):
        """Test file with wrong extension (PDF content with .txt extension)"""
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF'
        
        # Should try to load as text and likely fail
        with pytest.raises(DocumentProcessingError):
            await loader.load_document(pdf_content, 'file.xyz')


class TestCorruptedFiles:
    """Test corrupted file scenarios for each format - Requirement 1.2"""
    
    @pytest.mark.asyncio
    async def test_corrupted_pdf(self, loader):
        """Test corrupted PDF file"""
        corrupted_pdf = b'%PDF-1.4\nThis is not a valid PDF structure\n%%EOF'
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(corrupted_pdf, 'corrupted.pdf')
        
        error = exc_info.value
        assert error.error_category in [ErrorCategory.CORRUPTED_FILE, ErrorCategory.EMPTY_CONTENT]
        assert 'corrupted.pdf' in error.message
    
    @pytest.mark.asyncio
    async def test_corrupted_docx(self, loader):
        """Test corrupted DOCX file"""
        # DOCX is a ZIP file, so invalid ZIP data will fail
        corrupted_docx = b'PK\x03\x04This is not a valid DOCX'
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(corrupted_docx, 'corrupted.docx')
        
        error = exc_info.value
        assert error.error_category in [ErrorCategory.CORRUPTED_FILE, ErrorCategory.PROCESSING_ERROR]
    
    @pytest.mark.asyncio
    async def test_corrupted_xlsx(self, loader):
        """Test corrupted XLSX file"""
        corrupted_xlsx = b'PK\x03\x04Invalid Excel data'
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(corrupted_xlsx, 'corrupted.xlsx')
        
        error = exc_info.value
        assert error.error_category in [ErrorCategory.CORRUPTED_FILE, ErrorCategory.PROCESSING_ERROR]
    
    @pytest.mark.asyncio
    async def test_corrupted_csv(self, loader):
        """Test corrupted CSV file with invalid structure"""
        # CSV with mismatched columns
        corrupted_csv = b'Name,Age,City\nJohn,30\nJane,25,LA,Extra'
        
        # CSV is more forgiving, so this might load but with warnings
        try:
            docs = await loader.load_document(corrupted_csv, 'corrupted.csv')
            # If it loads, check that it has some content
            assert len(docs) > 0
        except DocumentProcessingError as e:
            # Or it might fail with corrupted file error
            assert e.error_category in [ErrorCategory.CORRUPTED_FILE, ErrorCategory.PROCESSING_ERROR]
    
    @pytest.mark.asyncio
    async def test_corrupted_pptx(self, loader):
        """Test corrupted PPTX file"""
        corrupted_pptx = b'PK\x03\x04Not a valid PowerPoint'
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(corrupted_pptx, 'corrupted.pptx')
        
        error = exc_info.value
        assert error.error_category in [ErrorCategory.CORRUPTED_FILE, ErrorCategory.PROCESSING_ERROR]


class TestEncodingErrors:
    """Test encoding error scenarios - Requirement 1.2"""
    
    @pytest.mark.asyncio
    async def test_invalid_utf8(self, loader):
        """Test text file with invalid UTF-8 encoding"""
        # Invalid UTF-8 sequence
        invalid_utf8 = b'\xff\xfe\x00\x00Invalid UTF-8'
        
        # Should try multiple encodings and eventually succeed or fail gracefully
        try:
            docs = await loader.load_document(invalid_utf8, 'invalid.txt')
            # If it succeeds, it found a working encoding
            assert len(docs) > 0
        except DocumentProcessingError as e:
            # If it fails, should be encoding error
            assert e.error_category == ErrorCategory.ENCODING_ERROR
            assert 'encoding' in e.message.lower() or 'decode' in e.message.lower()
    
    @pytest.mark.asyncio
    async def test_binary_file_as_text(self, loader):
        """Test binary file uploaded as text"""
        binary_content = bytes(range(256))
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(binary_content, 'binary.txt')
        
        error = exc_info.value
        assert error.error_category in [ErrorCategory.ENCODING_ERROR, ErrorCategory.EMPTY_CONTENT]
    
    @pytest.mark.asyncio
    async def test_mixed_encoding_csv(self, loader):
        """Test CSV with mixed encoding"""
        # Latin-1 encoded text with special characters
        latin1_csv = 'Name,City\nJosé,São Paulo\n'.encode('latin-1')
        
        # Should handle this with encoding fallback
        docs = await loader.load_document(latin1_csv, 'mixed.csv')
        assert len(docs) > 0
        assert docs[0].page_content
    
    @pytest.mark.asyncio
    async def test_encoding_error_message_details(self, loader):
        """Test that encoding errors provide detailed information"""
        # Completely invalid bytes for text
        invalid_bytes = b'\x80\x81\x82\x83\x84\x85'
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(invalid_bytes, 'invalid.txt')
        
        error = exc_info.value
        # Should mention attempted encodings
        assert 'utf-8' in error.message.lower() or 'encoding' in error.message.lower()


class TestInsufficientContent:
    """Test insufficient content scenarios - Requirement 1.3"""
    
    @pytest.mark.asyncio
    async def test_content_below_threshold(self, loader):
        """Test file with content below 10 character threshold"""
        short_content = b'Hi there'  # 8 characters
        
        docs = await loader.load_document(short_content, 'short.txt')
        
        # Should load but fail validation
        validation = await loader.validate_document_content(docs, 'short.txt', '.txt')
        assert validation['valid'] is False
        assert validation['failure_reason'] == 'insufficient_content'
        assert '8 characters' in validation['error']
        assert 'minimum required is 10' in validation['error']
    
    @pytest.mark.asyncio
    async def test_content_at_threshold(self, loader):
        """Test file with exactly 10 characters (minimum threshold)"""
        threshold_content = b'Ten chars!'  # Exactly 10 characters
        
        docs = await loader.load_document(threshold_content, 'threshold.txt')
        
        # Should pass validation
        validation = await loader.validate_document_content(docs, 'threshold.txt', '.txt')
        assert validation['valid'] is True
    
    @pytest.mark.asyncio
    async def test_low_content_warning(self, loader):
        """Test file with content between 10-50 characters gets warning"""
        low_content = b'This has twenty chars'  # 21 characters
        
        docs = await loader.load_document(low_content, 'low.txt')
        
        # Should pass but with warning
        validation = await loader.validate_document_content(docs, 'low.txt', '.txt')
        assert validation['valid'] is True
        assert len(validation['warnings']) > 0
        assert 'very little text content' in validation['warnings'][0]
    
    @pytest.mark.asyncio
    async def test_pdf_with_minimal_text(self, loader):
        """Test PDF with minimal extractable text"""
        # This would be a real PDF with very little text
        # For testing, we'll simulate the validation result
        from langchain_core.documents import Document
        
        minimal_doc = [Document(page_content="PDF", metadata={})]
        validation = await loader.validate_document_content(minimal_doc, 'minimal.pdf', '.pdf')
        
        assert validation['valid'] is False
        assert validation['failure_reason'] == 'insufficient_content'


class TestErrorMessageQuality:
    """Test error message quality and user-friendliness - Requirement 1.4"""
    
    @pytest.mark.asyncio
    async def test_error_includes_filename(self, loader):
        """Test that error messages include the filename"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'', 'myfile.pdf')
        
        error = exc_info.value
        assert 'myfile.pdf' in error.message
    
    @pytest.mark.asyncio
    async def test_error_is_actionable(self, loader):
        """Test that error messages provide actionable information"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'content', 'file.xyz')
        
        error = exc_info.value
        # Should tell user what formats are supported
        assert 'Supported formats' in error.message or 'supported' in error.message.lower()
    
    @pytest.mark.asyncio
    async def test_user_vs_system_error_distinction(self, loader):
        """Test distinction between user errors and system errors"""
        # User error: unsupported format
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'content', 'file.xyz')
        
        user_error = exc_info.value
        assert user_error.is_user_error is True
        
        # Empty file is also a user error
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'', 'empty.pdf')
        
        empty_error = exc_info.value
        assert empty_error.is_user_error is True
    
    @pytest.mark.asyncio
    async def test_error_to_dict_format(self, loader):
        """Test that errors can be converted to dict for API responses"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(b'', 'test.pdf')
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        assert 'error' in error_dict
        assert 'error_category' in error_dict
        assert 'error_type' in error_dict
        assert 'details' in error_dict
        assert error_dict['error_type'] in ['user_error', 'system_error']


class TestValidationFailureReasons:
    """Test specific validation failure reasons - Requirement 1.5"""
    
    @pytest.mark.asyncio
    async def test_no_documents_failure(self, loader):
        """Test validation failure when no documents extracted"""
        validation = await loader.validate_document_content([], 'test.pdf', '.pdf')
        
        assert validation['valid'] is False
        assert validation['failure_reason'] == 'no_documents'
        assert 'No documents were extracted' in validation['error']
    
    @pytest.mark.asyncio
    async def test_empty_content_failure(self, loader):
        """Test validation failure for empty content"""
        from langchain_core.documents import Document
        
        empty_docs = [Document(page_content="", metadata={})]
        validation = await loader.validate_document_content(empty_docs, 'test.pdf', '.pdf')
        
        assert validation['valid'] is False
        assert validation['failure_reason'] == 'empty_content'
    
    @pytest.mark.asyncio
    async def test_whitespace_only_failure(self, loader):
        """Test validation failure for whitespace-only content"""
        from langchain_core.documents import Document
        
        whitespace_docs = [Document(page_content="   \n\n   ", metadata={})]
        validation = await loader.validate_document_content(whitespace_docs, 'test.txt', '.txt')
        
        assert validation['valid'] is False
        assert validation['failure_reason'] in ['whitespace_only', 'empty_content']
    
    @pytest.mark.asyncio
    async def test_insufficient_content_failure(self, loader):
        """Test validation failure for insufficient content"""
        from langchain_core.documents import Document
        
        short_docs = [Document(page_content="Short", metadata={})]  # 5 characters
        validation = await loader.validate_document_content(short_docs, 'test.txt', '.txt')
        
        assert validation['valid'] is False
        assert validation['failure_reason'] == 'insufficient_content'
        assert '5 characters' in validation['error']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
