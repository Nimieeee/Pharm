"""
Test script for XLSX, CSV, and PPTX document processing
"""
import asyncio
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock test to verify the loaders are properly configured
async def test_document_loader_initialization():
    """Test that document loader supports new formats"""
    from app.services.document_loaders import document_loader
    
    supported = document_loader.get_supported_formats()
    
    assert '.xlsx' in supported, "XLSX format not supported"
    assert '.csv' in supported, "CSV format not supported"
    assert '.pptx' in supported, "PPTX format not supported"
    
    print("✅ All new formats are supported")
    print(f"Supported formats: {', '.join(supported)}")
    
    stats = document_loader.get_processing_stats()
    print(f"\nLoaders configured:")
    for ext, loader in stats['loaders'].items():
        print(f"  {ext}: {loader}")
    
    return True


async def test_csv_processing():
    """Test CSV file processing"""
    from app.services.document_loaders import document_loader
    
    # Create a test CSV file
    csv_content = """Name,Age,City
John Doe,30,New York
Jane Smith,25,Los Angeles
Bob Johnson,35,Chicago"""
    
    csv_bytes = csv_content.encode('utf-8')
    
    try:
        documents = await document_loader.load_document(
            csv_bytes, 
            "test.csv"
        )
        
        assert len(documents) > 0, "No documents extracted from CSV"
        assert "John Doe" in documents[0].page_content, "CSV content not extracted"
        assert documents[0].metadata['file_type'] == 'csv', "Wrong file type"
        
        print("✅ CSV processing works")
        print(f"   Extracted {len(documents)} document(s)")
        print(f"   Content preview: {documents[0].page_content[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ CSV processing failed: {e}")
        return False


async def test_xlsx_processing():
    """Test XLSX file processing"""
    from app.services.document_loaders import document_loader
    
    # Create a test XLSX file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df = pd.DataFrame({
            'Product': ['Widget A', 'Widget B', 'Widget C'],
            'Price': [10.99, 15.99, 20.99],
            'Stock': [100, 50, 75]
        })
        df.to_excel(tmp.name, sheet_name='Products', index=False)
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'rb') as f:
            xlsx_bytes = f.read()
        
        documents = await document_loader.load_document(
            xlsx_bytes,
            "test.xlsx"
        )
        
        assert len(documents) > 0, "No documents extracted from XLSX"
        assert "Widget A" in documents[0].page_content, "XLSX content not extracted"
        assert documents[0].metadata['file_type'] == 'xlsx', "Wrong file type"
        
        print("✅ XLSX processing works")
        print(f"   Extracted {len(documents)} document(s)")
        print(f"   Content preview: {documents[0].page_content[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ XLSX processing failed: {e}")
        return False
    finally:
        os.unlink(tmp_path)


async def main():
    """Run all tests"""
    print("Testing new document format support...\n")
    
    results = []
    
    # Test 1: Initialization
    print("Test 1: Document Loader Initialization")
    results.append(await test_document_loader_initialization())
    print()
    
    # Test 2: CSV Processing
    print("Test 2: CSV Processing")
    results.append(await test_csv_processing())
    print()
    
    # Test 3: XLSX Processing
    print("Test 3: XLSX Processing")
    results.append(await test_xlsx_processing())
    print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")
    print(f"{'='*50}")
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
