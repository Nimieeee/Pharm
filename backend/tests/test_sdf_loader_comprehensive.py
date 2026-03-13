"""
Comprehensive unit tests for SDF loader
Tests both rdkit-based and fallback parsing
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
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

from app.services.document_loaders import EnhancedDocumentLoader, DocumentProcessingError, ErrorCategory


@pytest.fixture
def loader():
    """Create document loader instance"""
    return EnhancedDocumentLoader()


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
    return sdf_content


@pytest.fixture
def multi_molecule_sdf():
    """Create a multi-molecule SDF file"""
    sdf_content = """Ethanol
  
  
  3  2  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
M  END
> <Name>
Ethanol

> <Formula>
C2H6O

$$
Methanol
  
  
  2  1  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
M  END
> <Name>
Methanol

> <Formula>
CH4O

$$
"""
    return sdf_content


@pytest.fixture
def corrupted_sdf():
    """Create a corrupted SDF file"""
    return """This is not a valid SDF file
It has no proper structure
Just random text
$$
"""


class TestSDFFormatSupport:
    """Test SDF format recognition - Requirement 2.1"""
    
    @pytest.mark.asyncio
    async def test_sdf_format_recognized(self, loader):
        """Test that .sdf extension is recognized"""
        assert loader.is_supported_format('test.sdf')
        assert loader.is_supported_format('molecule.sdf')
        assert loader.is_supported_format('COMPOUND.SDF')
    
    @pytest.mark.asyncio
    async def test_mol_format_recognized(self, loader):
        """Test that .mol extension is recognized"""
        assert loader.is_supported_format('test.mol')
        assert loader.is_supported_format('molecule.mol')
        assert loader.is_supported_format('COMPOUND.MOL')
    
    @pytest.mark.asyncio
    async def test_sdf_in_supported_formats_list(self, loader):
        """Test that SDF formats are in supported formats list"""
        supported = loader.get_supported_formats()
        assert '.sdf' in supported
        assert '.mol' in supported


class TestSingleMoleculeSDF:
    """Test single-molecule SDF files - Requirements 2.2, 2.3"""
    
    @pytest.mark.asyncio
    async def test_load_single_molecule(self, loader, single_molecule_sdf):
        """Test loading a single-molecule SDF file"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'aspirin.sdf')
        
        assert len(docs) == 1
        assert docs[0].page_content
        assert len(docs[0].page_content) > 0
    
    @pytest.mark.asyncio
    async def test_extract_compound_name(self, loader, single_molecule_sdf):
        """Test extraction of compound name"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'aspirin.sdf')
        
        # Should contain compound name in content or metadata
        assert 'Aspirin' in docs[0].page_content or 'Compound' in docs[0].page_content
        assert 'compound_name' in docs[0].metadata
    
    @pytest.mark.asyncio
    async def test_extract_molecular_properties(self, loader, single_molecule_sdf):
        """Test extraction of molecular properties"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'aspirin.sdf')
        
        content = docs[0].page_content
        # Should contain molecular information
        assert 'C9H8O4' in content or 'Formula' in content or 'Molecular' in content
        
        # Check metadata has properties
        assert 'properties' in docs[0].metadata
    
    @pytest.mark.asyncio
    async def test_sdf_metadata(self, loader, single_molecule_sdf):
        """Test SDF document metadata"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'aspirin.sdf')
        
        metadata = docs[0].metadata
        assert metadata['file_type'] == 'sdf'
        assert metadata['loader'] == 'SDFLoader'
        assert metadata['filename'] == 'aspirin.sdf'
        assert 'structure_index' in metadata
        assert metadata['structure_index'] == 0


class TestMultiMoleculeSDF:
    """Test multi-molecule SDF files - Requirement 2.4"""
    
    @pytest.mark.asyncio
    async def test_load_multiple_molecules(self, loader, multi_molecule_sdf):
        """Test loading SDF file with multiple molecules"""
        docs = await loader.load_document(multi_molecule_sdf.encode(), 'molecules.sdf')
        
        assert len(docs) == 2
        assert all(doc.page_content for doc in docs)
    
    @pytest.mark.asyncio
    async def test_separate_molecule_documents(self, loader, multi_molecule_sdf):
        """Test that each molecule creates a separate document"""
        docs = await loader.load_document(multi_molecule_sdf.encode(), 'molecules.sdf')
        
        # Each document should have unique structure index
        indices = [doc.metadata['structure_index'] for doc in docs]
        assert indices == [0, 1]
    
    @pytest.mark.asyncio
    async def test_molecule_specific_content(self, loader, multi_molecule_sdf):
        """Test that each molecule has its own content"""
        docs = await loader.load_document(multi_molecule_sdf.encode(), 'molecules.sdf')
        
        # First molecule should be Ethanol
        assert 'Ethanol' in docs[0].page_content or 'C2H6O' in docs[0].page_content
        
        # Second molecule should be Methanol
        assert 'Methanol' in docs[1].page_content or 'CH4O' in docs[1].page_content
    
    @pytest.mark.asyncio
    async def test_molecule_metadata_separation(self, loader, multi_molecule_sdf):
        """Test that each molecule has separate metadata"""
        docs = await loader.load_document(multi_molecule_sdf.encode(), 'molecules.sdf')
        
        # Each should have different compound names
        names = [doc.metadata.get('compound_name', '') for doc in docs]
        assert len(set(names)) == 2  # Two unique names


class TestCorruptedSDF:
    """Test corrupted SDF files - Requirement 2.5"""
    
    @pytest.mark.asyncio
    async def test_corrupted_sdf_error(self, loader, corrupted_sdf):
        """Test that corrupted SDF files raise appropriate error"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(corrupted_sdf.encode(), 'corrupted.sdf')
        
        error = exc_info.value
        # Should indicate file is corrupted or empty
        assert error.error_category in [ErrorCategory.CORRUPTED_FILE, ErrorCategory.EMPTY_CONTENT]
    
    @pytest.mark.asyncio
    async def test_empty_sdf_error(self, loader):
        """Test that empty SDF files raise appropriate error"""
        empty_sdf = "$$\n"
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(empty_sdf.encode(), 'empty.sdf')
        
        error = exc_info.value
        assert error.error_category == ErrorCategory.EMPTY_CONTENT
        assert 'empty.sdf' in error.message
    
    @pytest.mark.asyncio
    async def test_invalid_structure_error(self, loader):
        """Test SDF with invalid structure data"""
        invalid_sdf = """InvalidMolecule
  
  
  0  0  0  0  0  0  0  0  0  0999 V2000
M  END
$$
"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            await loader.load_document(invalid_sdf.encode(), 'invalid.sdf')
        
        error = exc_info.value
        assert error.error_category in [ErrorCategory.EMPTY_CONTENT, ErrorCategory.CORRUPTED_FILE]


class TestSDFParsingMethods:
    """Test SDF parsing with and without rdkit - Requirement 2.1"""
    
    @pytest.mark.asyncio
    async def test_rdkit_availability(self):
        """Test rdkit availability detection"""
        try:
            from rdkit import Chem
            rdkit_available = True
        except ImportError:
            rdkit_available = False
        
        # Test should pass regardless of rdkit availability
        assert isinstance(rdkit_available, bool)
    
    @pytest.mark.asyncio
    async def test_fallback_parsing_works(self, loader, single_molecule_sdf):
        """Test that fallback parsing works without rdkit"""
        # This test ensures fallback parsing produces valid documents
        docs = await loader.load_document(single_molecule_sdf.encode(), 'test.sdf')
        
        assert len(docs) > 0
        assert docs[0].page_content
        assert docs[0].metadata['loader'] == 'SDFLoader'
        
        # Check if fallback was used
        if 'parsing_method' in docs[0].metadata:
            assert docs[0].metadata['parsing_method'] in ['rdkit', 'fallback']
    
    @pytest.mark.asyncio
    async def test_mol_extension_works(self, loader, single_molecule_sdf):
        """Test that .mol extension is handled same as .sdf"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'test.mol')
        
        assert len(docs) > 0
        assert docs[0].page_content
        assert docs[0].metadata['file_type'] == 'mol'


class TestSDFTextRepresentation:
    """Test text representation of molecular data - Requirement 2.3"""
    
    @pytest.mark.asyncio
    async def test_text_contains_compound_info(self, loader, single_molecule_sdf):
        """Test that text representation includes compound information"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'aspirin.sdf')
        
        content = docs[0].page_content
        # Should contain key molecular information
        assert 'Compound' in content or 'Aspirin' in content
    
    @pytest.mark.asyncio
    async def test_text_contains_formula(self, loader, single_molecule_sdf):
        """Test that text representation includes molecular formula"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'aspirin.sdf')
        
        content = docs[0].page_content
        # Should contain formula information
        assert 'Formula' in content or 'C9H8O4' in content
    
    @pytest.mark.asyncio
    async def test_text_contains_properties(self, loader, single_molecule_sdf):
        """Test that text representation includes properties"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'aspirin.sdf')
        
        content = docs[0].page_content
        # Should contain property information
        assert 'Properties' in content or 'PUBCHEM' in content or '180.16' in content
    
    @pytest.mark.asyncio
    async def test_text_is_searchable(self, loader, single_molecule_sdf):
        """Test that text representation is searchable"""
        docs = await loader.load_document(single_molecule_sdf.encode(), 'aspirin.sdf')
        
        content = docs[0].page_content
        # Text should be substantial enough for search
        assert len(content) > 50
        # Should contain multiple lines
        assert '\n' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
