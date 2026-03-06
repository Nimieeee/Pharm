#!/usr/bin/env python3
"""
Comprehensive Document Loader Test Suite
Tests all supported document types following CLAUDE.md TDD principles
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

async def test_document_type(file_path, expected_chars_min=50):
    """Test a single document type"""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(file_path)}")
    print(f"Path: {file_path}")
    print(f"{'='*60}")

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    # Read file
    with open(file_path, 'rb') as f:
        content = f.read()

    print(f"📄 File size: {len(content):,} bytes")

    # Test Smart Loader
    try:
        from app.services.smart_loader import process_file
        from app.core.config import settings

        result = await process_file(
            file_content=content,
            filename=os.path.basename(file_path),
            user_prompt="Extract all text and data from this document",
            api_key=settings.MISTRAL_API_KEY,
            mode="detailed"
        )

        print(f"📊 Smart Loader result: {len(result)} chars")

        if len(result) < expected_chars_min:
            print(f"⚠️  Warning: Less than {expected_chars_min} chars extracted")
            if result.startswith("Error") or result.startswith("❌") or "Processing Error" in result or "Unsupported" in result:
                print(f"❌ Error message returned: {result[:200]}...")
                return False
        else:
            print(f"✅ Content extracted successfully")
            print(f"   Preview: {result[:150]}...")
            return True

    except Exception as e:
        print(f"❌ Smart Loader error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run tests for all document types found in codebase"""
    print("="*60)
    print("COMPREHENSIVE DOCUMENT LOADER TEST SUITE")
    print("Testing all document types found in codebase")
    print("="*60)

    # Define test files by type (actual files from codebase)
    test_files = {
        'PDF': [
            '/Users/mac/Desktop/phhh/CNS STIMULANTS_PHA 425.pdf',
            '/Users/mac/Desktop/phhh/From Malaria Drug to Anticancer Agent A Five-Year Review of Artemisinin.pdf',
            '/Users/mac/Desktop/phhh/Levetiracetam vs. Valproate in a Drosophila Model of Dementia.pdf',
        ],
        'DOCX': [
            '/Users/mac/Desktop/phhh/tolu tech2.docx',
            '/Users/mac/Desktop/phhh/g2 manuscript.docx',
            '/Users/mac/Desktop/phhh/tolu-result.docx',
        ],
        'PPTX': [
            '/Users/mac/Desktop/phhh/Acute Toxicity.pptx',
        ],
        'XLSX': [
            '/Users/mac/Desktop/phhh/admet.xlsx',
        ],
        'TXT': [
            '/Users/mac/Desktop/phhh/Artemisinin for Cancer research.txt',
        ],
        'SDF': [
            '/Users/mac/Desktop/phhh/top_20_mmgbsa.sdf',
        ],
        'Images': [
            '/Users/mac/Desktop/phhh/Benchside 2.png',
        ],
    }

    results = {}

    for doc_type, files in test_files.items():
        print(f"\n{'='*60}")
        print(f"Testing {doc_type} Documents")
        print(f"{'='*60}")

        if not files:
            print(f"⊘ No {doc_type} test files found")
            results[doc_type] = "SKIPPED (no files)"
            continue

        type_results = []
        for file_path in files:
            success = await test_document_type(file_path)
            type_results.append(success)
            results[os.path.basename(file_path)] = "✅ PASS" if success else "❌ FAIL"

        # Summary for this type
        passed = sum(type_results)
        total = len(type_results)
        print(f"\n{doc_type} Summary: {passed}/{total} passed")
        results[doc_type] = f"{passed}/{total}"

    # Final Summary
    print(f"\n{'='*60}")
    print("FINAL TEST SUMMARY")
    print(f"{'='*60}")
    for key, value in results.items():
        print(f"{key}: {value}")

    # Calculate overall pass rate
    total_tests = sum(1 for v in results.values() if isinstance(v, str) and ('PASS' in v or 'FAIL' in v))
    passed_tests = sum(1 for v in results.values() if isinstance(v, str) and 'PASS' in v)

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total_tests - passed_tests} tests failed")

    return results

if __name__ == "__main__":
    results = asyncio.run(run_all_tests())
