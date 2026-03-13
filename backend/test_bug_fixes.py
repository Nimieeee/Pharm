#!/usr/bin/env python3
"""
Test script to verify the three bug fixes:
1. RPC parameter name mismatch (conversation_uuid -> query_conversation_id)
2. PDF extraction returning 0 chunks (better error handling)
3. Generic greeting despite document context (system prompt update)
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_rpc_parameter_fix():
    """Test that the RPC call uses correct parameter names"""
    print("\n" + "="*60)
    print("TEST 1: RPC Parameter Name Fix")
    print("="*60)
    
    # Read the enhanced_rag.py file
    rag_file = Path(__file__).parent / "app" / "services" / "enhanced_rag.py"
    content = rag_file.read_text()
    
    # Check for correct parameter names
    has_correct_params = (
        "query_conversation_id" in content and
        "query_user_id" in content
    )
    has_wrong_params = (
        "conversation_uuid" in content or
        "user_session_uuid" in content
    )
    
    if has_correct_params and not has_wrong_params:
        print("✅ PASS: RPC parameters are correct")
        print("   - Uses 'query_conversation_id' ✓")
        print("   - Uses 'query_user_id' ✓")
        return True
    else:
        print("❌ FAIL: RPC parameters are incorrect")
        if has_wrong_params:
            print("   - Still using old parameter names")
        if not has_correct_params:
            print("   - Missing correct parameter names")
        return False


async def test_pdf_error_handling():
    """Test that PDF processing has better error handling"""
    print("\n" + "="*60)
    print("TEST 2: PDF Error Handling")
    print("="*60)
    
    # Read the vision_service.py file
    vision_file = Path(__file__).parent / "app" / "services" / "vision_service.py"
    content = vision_file.read_text()
    
    # Check for error handling when no content is extracted
    has_empty_check = "if not full_text.strip():" in content
    has_error_log = "No content extracted" in content
    has_placeholder_return = "PDF Processing Error" in content
    
    if has_empty_check and has_error_log and has_placeholder_return:
        print("✅ PASS: PDF error handling is improved")
        print("   - Checks for empty content ✓")
        print("   - Logs error when no content extracted ✓")
        print("   - Returns placeholder instead of empty string ✓")
        return True
    else:
        print("❌ FAIL: PDF error handling is incomplete")
        if not has_empty_check:
            print("   - Missing empty content check")
        if not has_error_log:
            print("   - Missing error logging")
        if not has_placeholder_return:
            print("   - Missing placeholder return")
        return False


async def test_greeting_suppression():
    """Test that system prompt suppresses greetings with document context"""
    print("\n" + "="*60)
    print("TEST 3: Greeting Suppression with Document Context")
    print("="*60)
    
    # Read the ai.py file
    ai_file = Path(__file__).parent / "app" / "services" / "ai.py"
    content = ai_file.read_text()
    
    # Check for greeting protocol instructions
    has_greeting_protocol = "GREETING PROTOCOL:" in content
    has_no_greeting_instruction = "DO NOT start with a greeting" in content
    has_document_context_check = "When <document_context> is present" in content
    
    if has_greeting_protocol and has_no_greeting_instruction and has_document_context_check:
        print("✅ PASS: Greeting suppression is configured")
        print("   - Has GREETING PROTOCOL section ✓")
        print("   - Instructs to skip greeting with document context ✓")
        print("   - Checks for document_context presence ✓")
        return True
    else:
        print("❌ FAIL: Greeting suppression is incomplete")
        if not has_greeting_protocol:
            print("   - Missing GREETING PROTOCOL section")
        if not has_no_greeting_instruction:
            print("   - Missing no-greeting instruction")
        if not has_document_context_check:
            print("   - Missing document context check")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BENCHSIDE BUG FIX VERIFICATION")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(await test_rpc_parameter_fix())
    results.append(await test_pdf_error_handling())
    results.append(await test_greeting_suppression())
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Bug fixes verified!")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Review fixes needed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
