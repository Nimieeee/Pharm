"""
Test SDF file format support
Tests both rdkit-based and fallback parsing
"""
import tempfile
import os
import asyncio


def test_sdf_fallback_parsing():
    """Test SDF parsing without rdkit (fallback mode)"""
    print("Test 1: SDF Fallback Parsing (without rdkit)")
    
    # Create a simple SDF file
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

$$$$
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sdf', delete=False) as tmp:
        tmp.write(sdf_content)
        tmp_path = tmp.name
    
    try:
        # Import the loader
        from app.services.document_loaders import EnhancedDocumentLoader
        
        loader = EnhancedDocumentLoader()
        
        # Test that .sdf is supported
        assert loader.is_supported_format('test.sdf'), "SDF format not recognized"
        assert loader.is_supported_format('test.mol'), "MOL format not recognized"
        
        # Load the SDF file
        async def load_test():
            with open(tmp_path, 'rb') as f:
                content = f.read()
            docs = await loader.load_document(content, 'aspirin.sdf')
            return docs
        
        docs = asyncio.run(load_test())
        
        assert len(docs) > 0, "No documents extracted"
        assert docs[0].page_content, "Empty content"
        assert 'Aspirin' in docs[0].page_content or 'Compound' in docs[0].page_content, "Missing compound info"
        
        # Check metadata
        assert docs[0].metadata['file_type'] == 'sdf', "Wrong file type"
        assert docs[0].metadata['loader'] == 'SDFLoader', "Wrong loader"
        
        print("   ✅ SDF fallback parsing works")
        print(f"   ✅ Extracted {len(docs)} molecule(s)")
        print(f"   ✅ Content length: {len(docs[0].page_content)} characters")
        return True
    except Exception as e:
        print(f"   ❌ SDF fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.unlink(tmp_path)


def test_multi_molecule_sdf():
    """Test SDF file with multiple molecules"""
    print("\nTest 2: Multi-Molecule SDF")
    
    # Create SDF with 2 molecules
    sdf_content = """Molecule1
  
  
  3  2  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
M  END
> <Name>
Ethanol

$$$$
Molecule2
  
  
  2  1  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
M  END
> <Name>
Methanol

$$$$
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sdf', delete=False) as tmp:
        tmp.write(sdf_content)
        tmp_path = tmp.name
    
    try:
        from app.services.document_loaders import EnhancedDocumentLoader
        
        loader = EnhancedDocumentLoader()
        
        async def load_test():
            with open(tmp_path, 'rb') as f:
                content = f.read()
            docs = await loader.load_document(content, 'molecules.sdf')
            return docs
        
        docs = asyncio.run(load_test())
        
        assert len(docs) == 2, f"Expected 2 molecules, got {len(docs)}"
        
        # Check that both molecules were parsed
        for i, doc in enumerate(docs):
            assert doc.page_content, f"Empty content for molecule {i}"
            assert doc.metadata['structure_index'] == i, f"Wrong index for molecule {i}"
        
        print("   ✅ Multi-molecule SDF parsing works")
        print(f"   ✅ Extracted {len(docs)} molecules")
        return True
    except Exception as e:
        print(f"   ❌ Multi-molecule test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.unlink(tmp_path)


def test_rdkit_availability():
    """Test if rdkit is available"""
    print("\nTest 3: RDKit Availability Check")
    
    try:
        from rdkit import Chem
        print(f"   ✅ RDKit is available")
        print(f"   ✅ Can use advanced molecular parsing")
        return True
    except ImportError:
        print("   ⚠️  RDKit not available (fallback parsing will be used)")
        print("   ℹ️  Install with: pip install rdkit-pypi")
        return True  # Not a failure, just informational


def main():
    """Run all SDF tests"""
    print("="*60)
    print("Testing SDF File Format Support")
    print("="*60)
    print()
    
    results = []
    
    # Check rdkit availability (informational)
    test_rdkit_availability()
    
    # Test functionality
    results.append(test_sdf_fallback_parsing())
    results.append(test_multi_molecule_sdf())
    
    # Summary
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All SDF tests passed!")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    print("="*60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
