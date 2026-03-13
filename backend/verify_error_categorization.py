"""
Verification script for error categorization implementation
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock dependencies
from unittest.mock import MagicMock
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = MagicMock()

from app.services.document_loaders import (
    DocumentProcessingError,
    ErrorCategory,
    ErrorMessageTemplates
)

def verify_error_categories():
    """Verify all error categories are defined"""
    print("✓ Verifying error categories...")
    categories = [
        'EMPTY_CONTENT',
        'ENCODING_ERROR',
        'CORRUPTED_FILE',
        'UNSUPPORTED_FORMAT',
        'INSUFFICIENT_CONTENT',
        'PROCESSING_ERROR',
        'VALIDATION_ERROR',
        'FILE_NOT_FOUND',
        'PERMISSION_ERROR'
    ]
    
    for category in categories:
        assert hasattr(ErrorCategory, category), f"Missing category: {category}"
        print(f"  ✓ {category}: {getattr(ErrorCategory, category)}")
    
    print("✅ All error categories defined\n")

def verify_error_message_templates():
    """Verify all error message templates work"""
    print("✓ Verifying error message templates...")
    
    # Test unsupported format
    msg = ErrorMessageTemplates.unsupported_format("test.xyz", ".xyz", [".pdf", ".txt"])
    assert "test.xyz" in msg and ".xyz" in msg
    print(f"  ✓ unsupported_format: {msg[:80]}...")
    
    # Test empty content
    msg = ErrorMessageTemplates.empty_content("empty.pdf")
    assert "empty.pdf" in msg and "No content" in msg
    print(f"  ✓ empty_content: {msg[:80]}...")
    
    # Test encoding error
    msg = ErrorMessageTemplates.encoding_error("test.txt", ["utf-8", "latin-1"])
    assert "test.txt" in msg and "utf-8" in msg
    print(f"  ✓ encoding_error: {msg[:80]}...")
    
    # Test corrupted file
    msg = ErrorMessageTemplates.corrupted_file("broken.pdf", "PDF")
    assert "broken.pdf" in msg and "corrupted" in msg.lower()
    print(f"  ✓ corrupted_file: {msg[:80]}...")
    
    # Test insufficient content
    msg = ErrorMessageTemplates.insufficient_content("short.txt", 5, 10)
    assert "short.txt" in msg and "5" in msg and "10" in msg
    print(f"  ✓ insufficient_content: {msg[:80]}...")
    
    # Test processing error
    msg = ErrorMessageTemplates.processing_error("test.pdf", "Unknown error")
    assert "test.pdf" in msg and "Unknown error" in msg
    print(f"  ✓ processing_error: {msg[:80]}...")
    
    # Test validation error
    msg = ErrorMessageTemplates.validation_error("test.pdf", "Content too short")
    assert "test.pdf" in msg and "Content too short" in msg
    print(f"  ✓ validation_error: {msg[:80]}...")
    
    # Test file not found
    msg = ErrorMessageTemplates.file_not_found("missing.pdf")
    assert "missing.pdf" in msg and "not found" in msg.lower()
    print(f"  ✓ file_not_found: {msg[:80]}...")
    
    # Test permission error
    msg = ErrorMessageTemplates.permission_error("locked.pdf")
    assert "locked.pdf" in msg and "Permission denied" in msg
    print(f"  ✓ permission_error: {msg[:80]}...")
    
    print("✅ All error message templates working\n")

def verify_document_processing_error():
    """Verify DocumentProcessingError class"""
    print("✓ Verifying DocumentProcessingError class...")
    
    # Test basic error creation
    error = DocumentProcessingError("Test error")
    assert error.message == "Test error"
    assert error.error_category == "processing_error"
    assert error.is_user_error is True
    assert error.details == {}
    print("  ✓ Basic error creation")
    
    # Test error with category
    error = DocumentProcessingError(
        "Empty file",
        error_category=ErrorCategory.EMPTY_CONTENT
    )
    assert error.error_category == ErrorCategory.EMPTY_CONTENT
    print("  ✓ Error with category")
    
    # Test system error
    error = DocumentProcessingError(
        "System failure",
        is_user_error=False
    )
    assert error.is_user_error is False
    print("  ✓ System error distinction")
    
    # Test error with details
    details = {"filename": "test.pdf", "file_size": 0}
    error = DocumentProcessingError(
        "Processing failed",
        error_category=ErrorCategory.ENCODING_ERROR,
        details=details
    )
    assert error.details == details
    print("  ✓ Error with details")
    
    # Test to_dict method
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
    print("  ✓ to_dict() method")
    
    # Test user vs system error in dict
    user_error = DocumentProcessingError("User error", is_user_error=True)
    system_error = DocumentProcessingError("System error", is_user_error=False)
    assert user_error.to_dict()["error_type"] == "user_error"
    assert system_error.to_dict()["error_type"] == "system_error"
    print("  ✓ User vs system error in dict")
    
    print("✅ DocumentProcessingError class working correctly\n")

def main():
    """Run all verification tests"""
    print("=" * 70)
    print("ERROR CATEGORIZATION VERIFICATION")
    print("=" * 70)
    print()
    
    try:
        verify_error_categories()
        verify_error_message_templates()
        verify_document_processing_error()
        
        print("=" * 70)
        print("✅ ALL VERIFICATIONS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ 9 error categories defined")
        print("  ✓ 9 error message templates working")
        print("  ✓ DocumentProcessingError class fully functional")
        print("  ✓ User vs system error distinction implemented")
        print("  ✓ Error details and metadata support working")
        print()
        return 0
        
    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
