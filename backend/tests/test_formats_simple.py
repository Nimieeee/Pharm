"""
Simple standalone test for XLSX, CSV, and PPTX processing
Tests the core functionality without requiring full app context
"""
import pandas as pd
import tempfile
import os
from pathlib import Path


def test_xlsx_support():
    """Test that openpyxl can read XLSX files"""
    print("Test 1: XLSX Support")
    
    # Create a test XLSX file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df = pd.DataFrame({
            'Product': ['Widget A', 'Widget B', 'Widget C'],
            'Price': [10.99, 15.99, 20.99],
            'Stock': [100, 50, 75]
        })
        df.to_excel(tmp.name, sheet_name='Products', index=False, engine='openpyxl')
        tmp_path = tmp.name
    
    try:
        # Read it back
        df_read = pd.read_excel(tmp_path, sheet_name='Products', engine='openpyxl')
        
        assert len(df_read) == 3, "Wrong number of rows"
        assert 'Product' in df_read.columns, "Missing Product column"
        assert df_read['Product'].iloc[0] == 'Widget A', "Wrong data"
        
        print("   ✅ XLSX reading works")
        print(f"   ✅ Read {len(df_read)} rows, {len(df_read.columns)} columns")
        return True
    except Exception as e:
        print(f"   ❌ XLSX test failed: {e}")
        return False
    finally:
        os.unlink(tmp_path)


def test_csv_support():
    """Test that pandas can read CSV files"""
    print("\nTest 2: CSV Support")
    
    # Create a test CSV file
    csv_content = """Name,Age,City
John Doe,30,New York
Jane Smith,25,Los Angeles
Bob Johnson,35,Chicago"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        tmp.write(csv_content)
        tmp_path = tmp.name
    
    try:
        # Read it back
        df = pd.read_csv(tmp_path)
        
        assert len(df) == 3, "Wrong number of rows"
        assert 'Name' in df.columns, "Missing Name column"
        assert df['Name'].iloc[0] == 'John Doe', "Wrong data"
        
        print("   ✅ CSV reading works")
        print(f"   ✅ Read {len(df)} rows, {len(df.columns)} columns")
        return True
    except Exception as e:
        print(f"   ❌ CSV test failed: {e}")
        return False
    finally:
        os.unlink(tmp_path)


def test_pptx_support():
    """Test that unstructured can be imported"""
    print("\nTest 3: PPTX Support (Library Check)")
    
    try:
        # Just check if we can import the library
        from langchain_community.document_loaders import UnstructuredPowerPointLoader
        
        print("   ✅ UnstructuredPowerPointLoader can be imported")
        print("   ✅ PPTX processing library available")
        return True
    except ImportError as e:
        print(f"   ❌ PPTX library import failed: {e}")
        return False


def test_pandas_import():
    """Test pandas import"""
    print("\nTest 4: Pandas Import")
    
    try:
        import pandas as pd
        print(f"   ✅ Pandas version: {pd.__version__}")
        return True
    except ImportError as e:
        print(f"   ❌ Pandas import failed: {e}")
        return False


def test_openpyxl_import():
    """Test openpyxl import"""
    print("\nTest 5: OpenPyXL Import")
    
    try:
        import openpyxl
        print(f"   ✅ OpenPyXL version: {openpyxl.__version__}")
        return True
    except ImportError as e:
        print(f"   ❌ OpenPyXL import failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("Testing New Document Format Dependencies")
    print("="*60)
    print()
    
    results = []
    
    # Test imports first
    results.append(test_pandas_import())
    results.append(test_openpyxl_import())
    results.append(test_pptx_support())
    
    # Test functionality
    results.append(test_csv_support())
    results.append(test_xlsx_support())
    
    # Summary
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed! Dependencies are correctly installed.")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    print("="*60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
