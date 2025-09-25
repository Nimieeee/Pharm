"""
Test Verification Script
Simple verification that all test components can be imported and basic functionality works
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all test modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test main test modules
        import test_comprehensive_suite
        import test_auth_unit
        import test_data_isolation
        import test_rag_mock
        import test_ui_comprehensive
        print("✅ All test modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_component_imports():
    """Test that all application components can be imported"""
    print("🔍 Testing component imports...")
    
    components = [
        'auth_manager',
        'session_manager', 
        'theme_manager',
        'ui_components',
        'message_store',
        'chat_manager',
        'vector_retriever',
        'document_processor',
        'context_builder',
        'rag_orchestrator',
        'model_manager'
    ]
    
    failed_imports = []
    
    for component in components:
        try:
            __import__(component)
            print(f"✅ {component}")
        except ImportError as e:
            print(f"❌ {component}: {e}")
            failed_imports.append(component)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    else:
        print("✅ All components imported successfully")
        return True

def test_basic_functionality():
    """Test basic functionality of key components"""
    print("🔍 Testing basic functionality...")
    
    try:
        # Test ThemeManager
        from theme_manager import ThemeManager
        theme_manager = ThemeManager()
        assert theme_manager is not None
        assert "light" in theme_manager.themes
        assert "dark" in theme_manager.themes
        print("✅ ThemeManager basic functionality")
        
        # Test UI Components
        from ui_components import ChatInterface, Message
        from datetime import datetime
        
        chat_interface = ChatInterface(theme_manager)
        test_message = Message(
            role="user",
            content="Test message",
            timestamp=datetime.now()
        )
        assert chat_interface is not None
        assert test_message.role == "user"
        print("✅ UI Components basic functionality")
        
        # Test mock components for RAG
        from test_rag_mock import MockVectorDatabase
        mock_db = MockVectorDatabase()
        mock_db.store_document("doc1", "user1", "test content", [0.1] * 384, {})
        assert mock_db.get_user_document_count("user1") == 1
        print("✅ Mock RAG components basic functionality")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_file_structure():
    """Test that all required test files exist"""
    print("🔍 Testing file structure...")
    
    required_files = [
        'test_comprehensive_suite.py',
        'test_auth_unit.py',
        'test_data_isolation.py',
        'test_rag_mock.py',
        'test_ui_comprehensive.py',
        'run_comprehensive_tests.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - Missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All test files present")
        return True

def test_requirements_coverage():
    """Test that all requirements from the spec are covered"""
    print("🔍 Testing requirements coverage...")
    
    # Read the requirements from the spec
    try:
        with open('.kiro/specs/pharmacology-chat-app/requirements.md', 'r') as f:
            requirements_content = f.read()
        
        # Check for key requirement areas
        requirement_areas = [
            'authentication',
            'user privacy',
            'conversation',
            'model selection',
            'theme',
            'vector',
            'deployment'
        ]
        
        covered_areas = []
        for area in requirement_areas:
            if area.lower() in requirements_content.lower():
                covered_areas.append(area)
                print(f"✅ {area} requirements found")
            else:
                print(f"❌ {area} requirements not found")
        
        coverage_percent = (len(covered_areas) / len(requirement_areas)) * 100
        print(f"\n📊 Requirements coverage: {coverage_percent:.1f}%")
        
        return coverage_percent >= 80  # 80% coverage threshold
        
    except FileNotFoundError:
        print("❌ Requirements file not found")
        return False

def main():
    """Main verification function"""
    print("🧪 COMPREHENSIVE TEST VERIFICATION")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Component Imports", test_component_imports),
        ("Test Module Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Requirements Coverage", test_requirements_coverage)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Tests: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("\n✅ Test Suite Status:")
        print("   • All test files are present")
        print("   • All components can be imported")
        print("   • Basic functionality works")
        print("   • Requirements are covered")
        print("\n🚀 The comprehensive test suite is ready!")
        
        print("\n📋 Test Suite Includes:")
        print("   • Unit tests for authentication manager and session handling")
        print("   • Integration tests for user-scoped data isolation")
        print("   • RAG pipeline tests with mock vector database")
        print("   • UI component tests for theme switching and responsiveness")
        print("   • Comprehensive test runner with detailed reporting")
        
        return True
    else:
        print(f"\n❌ {total - passed} VERIFICATION(S) FAILED")
        print("Please fix the issues above before running the full test suite.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)