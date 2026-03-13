"""
Comprehensive integration tests for document processing
Tests SDF upload through API, error responses, and response format
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""
import pytest
import sys
import os
from io import BytesIO
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock settings and dependencies
from unittest.mock import MagicMock, AsyncMock, patch
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = MagicMock()

from app.services.enhanced_rag import EnhancedRAGService
from app.services.document_loaders import EnhancedDocumentLoader, DocumentProcessingError, ErrorCategory
from app.models.document import DocumentUploadResponse


@pytest.fixture
def mock_db():
    """Create mock database client"""
    db = MagicMock()
    return db


@pytest.fixture
def rag_service(mock_db):
    """Create RAG service instance"""
    return EnhancedRAGService(mock_db)


@pytest.fixture
def single_molecule_sdf():
    """Create a single-molecule SDF file"""
    sdf_content = """Aspirin
  -ISIS-  01231512342D

 13 13  0  0  0  0  0  0  0  0999 V2000
    2.8660   -0.7500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    3.7320   -0.2500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    3.7320    0.7500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    4.5981   -0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    5.4641   -0.2500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    6.3301   -0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    7.1962   -0.2500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    7.1962    0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    6.3301    1.2500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    5.4641    0.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    6.3301    2.2500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    7.1962    2.7500    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    7.1962    3.7500    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  2  0  0  0  0
  2  4  1  0  0  0  0
  4  5  1  0  0  0  0
  5  6  2  0  0  0  0
  6  7  1  0  0  0  0
  7  8  2  0  0  0  0
  8  9  1  0  0  0  0
  9 10  2  0  0  0  0
 10  5  1  0  0  0  0
  9 11  1  0  0  0  0
 11 12  1  0  0  0  0
 12 13  2  0  0  0  0
M  END
> <PUBCHEM_COMPOUND_CID>
2244

> <PUBCHEM_MOLECULAR_FORMULA>
C9H8O4

> <PUBCHEM_MOLECULAR_WEIGHT>
180.16

$$
"""
    return sdf_content.encode()


class TestSDFUploadIntegration:
    """Test SDF upload through API endpoint - Requirement 3.1"""
    
    @pytest.mark.asyncio
    async def test_sdf_upload_success(self, rag_service, single_molecule_sdf, mock_db):
        """Test successful SDF file upload"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        # Mock database operations
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        # Process the file
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=single_molecule_sdf,
                filename='aspirin.sdf',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        # Verify response structure
        assert isinstance(result, DocumentUploadResponse)
        assert result.success is True
        assert result.chunk_count > 0
        assert 'aspirin.sdf' in result.message
    
    @pytest.mark.asyncio
    async def test_sdf_upload_metadata(self, rag_service, single_molecule_sdf, mock_db):
        """Test that SDF upload includes proper metadata"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=single_molecule_sdf,
                filename='aspirin.sdf',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        # Check file_info field
        assert result.file_info is not None
        assert result.file_info['filename'] == 'aspirin.sdf'
        assert result.file_info['format'] == 'sdf'
        assert result.file_info['size_bytes'] > 0
    
    @pytest.mark.asyncio
    async def test_mol_extension_upload(self, rag_service, single_molecule_sdf, mock_db):
        """Test that .mol extension works same as .sdf"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=single_molecule_sdf,
                filename='molecule.mol',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        assert result.success is True
        assert result.file_info['format'] == 'mol'


class TestErrorResponseIntegration:
    """Test error responses for each error type - Requirements 3.2, 3.3"""
    
    @pytest.mark.asyncio
    async def test_empty_file_error_response(self, rag_service, mock_db):
        """Test error response for empty file"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await rag_service.process_uploaded_file(
                file_content=b'',
                filename='empty.pdf',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        # Verify error structure
        assert error_dict['error_category'] == ErrorCategory.EMPTY_CONTENT
        assert error_dict['error_type'] == 'user_error'
        assert 'empty.pdf' in error_dict['error']
    
    @pytest.mark.asyncio
    async def test_unsupported_format_error_response(self, rag_service, mock_db):
        """Test error response for unsupported format"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await rag_service.process_uploaded_file(
                file_content=b'some content',
                filename='file.xyz',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        # Verify error includes supported formats
        assert error_dict['error_category'] == ErrorCategory.UNSUPPORTED_FORMAT
        assert '.xyz' in error_dict['error']
        assert 'supported_formats' in error_dict['details'] or 'Supported formats' in error_dict['error']
    
    @pytest.mark.asyncio
    async def test_corrupted_file_error_response(self, rag_service, mock_db):
        """Test error response for corrupted file"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        corrupted_pdf = b'%PDF-1.4\nNot a valid PDF\n%%EOF'
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await rag_service.process_uploaded_file(
                file_content=corrupted_pdf,
                filename='corrupted.pdf',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        assert error_dict['error_category'] in [ErrorCategory.CORRUPTED_FILE, ErrorCategory.EMPTY_CONTENT]
        assert 'corrupted.pdf' in error_dict['error']
    
    @pytest.mark.asyncio
    async def test_encoding_error_response(self, rag_service, mock_db):
        """Test error response for encoding errors"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        invalid_encoding = bytes(range(256))
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await rag_service.process_uploaded_file(
                file_content=invalid_encoding,
                filename='invalid.txt',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        assert error_dict['error_category'] in [ErrorCategory.ENCODING_ERROR, ErrorCategory.EMPTY_CONTENT]
    
    @pytest.mark.asyncio
    async def test_insufficient_content_error_response(self, rag_service, mock_db):
        """Test error response for insufficient content"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        short_content = b'Hi'  # Only 2 characters
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await rag_service.process_uploaded_file(
                file_content=short_content,
                filename='short.txt',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        assert error_dict['error_category'] in [ErrorCategory.INSUFFICIENT_CONTENT, ErrorCategory.VALIDATION_ERROR]


class TestResponseFormatStructure:
    """Test response format matches expected structure - Requirements 3.4, 3.5"""
    
    @pytest.mark.asyncio
    async def test_success_response_structure(self, rag_service, single_molecule_sdf, mock_db):
        """Test that success response has all required fields"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=single_molecule_sdf,
                filename='test.sdf',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        # Verify all required fields are present
        assert hasattr(result, 'success')
        assert hasattr(result, 'message')
        assert hasattr(result, 'chunk_count')
        assert hasattr(result, 'processing_time')
        assert hasattr(result, 'file_info')
        assert hasattr(result, 'warnings')
        
        # Verify field types
        assert isinstance(result.success, bool)
        assert isinstance(result.message, str)
        assert isinstance(result.chunk_count, int)
        assert isinstance(result.file_info, dict)
        assert isinstance(result.warnings, list)
    
    @pytest.mark.asyncio
    async def test_file_info_structure(self, rag_service, single_molecule_sdf, mock_db):
        """Test that file_info contains all expected fields"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=single_molecule_sdf,
                filename='test.sdf',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        file_info = result.file_info
        
        # Verify file_info structure
        assert 'filename' in file_info
        assert 'format' in file_info
        assert 'size_bytes' in file_info
        assert 'content_length' in file_info
        
        # Verify values
        assert file_info['filename'] == 'test.sdf'
        assert file_info['format'] == 'sdf'
        assert file_info['size_bytes'] > 0
        assert file_info['content_length'] > 0
    
    @pytest.mark.asyncio
    async def test_warnings_field_populated(self, rag_service, mock_db):
        """Test that warnings field is populated for low content"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        # Content with 15 characters (above minimum but below warning threshold)
        low_content = b'Fifteen chars!!'
        
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=low_content,
                filename='low.txt',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        # Should have warnings about low content
        assert len(result.warnings) > 0
        assert any('little text content' in w for w in result.warnings)
    
    @pytest.mark.asyncio
    async def test_processing_time_included(self, rag_service, single_molecule_sdf, mock_db):
        """Test that processing time is included in response"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=single_molecule_sdf,
                filename='test.sdf',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        # Processing time should be present and positive
        assert result.processing_time is not None
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_error_response_structure(self, rag_service, mock_db):
        """Test that error responses have proper structure"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await rag_service.process_uploaded_file(
                file_content=b'',
                filename='empty.pdf',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        # Verify error response structure
        assert 'error' in error_dict
        assert 'error_category' in error_dict
        assert 'error_type' in error_dict
        assert 'details' in error_dict
        
        # Verify error_type is valid
        assert error_dict['error_type'] in ['user_error', 'system_error']


class TestMultipleFormatIntegration:
    """Test integration with multiple file formats"""
    
    @pytest.mark.asyncio
    async def test_text_file_upload(self, rag_service, mock_db):
        """Test text file upload integration"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        text_content = b'This is a test document with sufficient content for processing.'
        
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=text_content,
                filename='test.txt',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        assert result.success is True
        assert result.file_info['format'] == 'txt'
    
    @pytest.mark.asyncio
    async def test_csv_file_upload(self, rag_service, mock_db):
        """Test CSV file upload integration"""
        conversation_id = uuid4()
        user_id = uuid4()
        
        csv_content = b'Name,Age,City\nJohn,30,NYC\nJane,25,LA\nBob,35,Chicago'
        
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
        
        with patch.object(rag_service, '_store_chunks', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = None
            
            result = await rag_service.process_uploaded_file(
                file_content=csv_content,
                filename='data.csv',
                conversation_id=conversation_id,
                user_id=user_id
            )
        
        assert result.success is True
        assert result.file_info['format'] == 'csv'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
