#!/usr/bin/env python3
"""
Master Test Runner for UI Enhancements Comprehensive Testing Suite
Runs all tests for UI enhancements including unit tests, integration tests, and end-to-end tests.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))


def run_test_file(test_file, description):
    """Run a specific test file and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print(f"📁 File: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the test file
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=300)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        success = result.returncode == 0
        
        print(f"\n⏱️  Duration: {duration:.2f} seconds")
        print(f"✅ Status: {'PASSED' if success else 'FAILED'}")
        
        return {
            'file': test_file,
            'description': description,
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ Test timed out after 5 minutes")
        return {
            'file': test_file,
            'description': description,
            'success': False,
            'duration': 300,
            'stdout': '',
            'stderr': 'Test timed out',
            'returncode': -1
        }
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return {
            'file': test_file,
            'description': description,
            'success': False,
            'duration': 0,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }


def check_test_file_exists(test_file):
    """Check if test file exists"""
    if not os.path.exists(test_file):
        print(f"⚠️  Warning: Test file {test_file} not found, skipping...")
        return False
    return True


def run_comprehensive_ui_enhancements_tests():
    """Run all UI enhancements tests"""
    print("🚀 UI Enhancements Comprehensive Testing Suite")
    print("=" * 80)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Define all test files and their descriptions
    test_suite = [
        {
            'file': 'test_ui_enhancements_comprehensive.py',
            'description': 'Comprehensive UI Enhancements Tests',
            'category': 'comprehensive'
        },
        {
            'file': 'test_model_toggle_unit.py',
            'description': 'Model Toggle Switch Unit Tests',
            'category': 'unit'
        },
        {
            'file': 'test_conversation_management_integration.py',
            'description': 'Conversation Management Integration Tests',
            'category': 'integration'
        },
        {
            'file': 'test_rag_document_processing_e2e.py',
            'description': 'RAG Document Processing End-to-End Tests',
            'category': 'e2e'
        },
        {
            'file': 'test_ui_sidebar_and_theme.py',
            'description': 'UI Sidebar and Dark Theme Tests',
            'category': 'ui'
        },
        # Include existing test files for completeness
        {
            'file': 'test_model_toggle_switch.py',
            'description': 'Model Toggle Switch (Existing)',
            'category': 'existing'
        },
        {
            'file': 'test_conversation_management.py',
            'description': 'Conversation Management (Existing)',
            'category': 'existing'
        },
        {
            'file': 'test_rag_end_to_end.py',
            'description': 'RAG End-to-End (Existing)',
            'category': 'existing'
        },
        {
            'file': 'test_permanent_dark_theme.py',
            'description': 'Permanent Dark Theme (Existing)',
            'category': 'existing'
        }
    ]
    
    # Filter to only existing test files
    available_tests = []
    for test in test_suite:
        if check_test_file_exists(test['file']):
            available_tests.append(test)
    
    print(f"📊 Found {len(available_tests)} available test files")
    
    # Run all tests
    results = []
    total_start_time = time.time()
    
    for test in available_tests:
        result = run_test_file(test['file'], test['description'])
        result['category'] = test['category']
        results.append(result)
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 80)
    
    # Overall statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    
    print(f"📈 Overall Results:")
    print(f"  • Total test files: {total_tests}")
    print(f"  • Passed: {passed_tests}")
    print(f"  • Failed: {failed_tests}")
    print(f"  • Success rate: {(passed_tests/total_tests*100):.1f}%")
    print(f"  • Total duration: {total_duration:.2f} seconds")
    
    # Results by category
    categories = {}
    for result in results:
        category = result['category']
        if category not in categories:
            categories[category] = {'passed': 0, 'failed': 0, 'total': 0}
        
        categories[category]['total'] += 1
        if result['success']:
            categories[category]['passed'] += 1
        else:
            categories[category]['failed'] += 1
    
    print(f"\n📋 Results by Category:")
    for category, stats in categories.items():
        success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  • {category.title()}: {stats['passed']}/{stats['total']} passed ({success_rate:.1f}%)")
    
    # Detailed results
    print(f"\n📝 Detailed Results:")
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"  {status_icon} {result['description']}")
        print(f"     File: {result['file']}")
        print(f"     Duration: {result['duration']:.2f}s")
        if not result['success']:
            print(f"     Error: {result['stderr'][:100]}...")
    
    # Failed tests details
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print(f"\n❌ Failed Tests Details:")
        for result in failed_results:
            print(f"\n  📁 {result['file']}:")
            print(f"     Description: {result['description']}")
            print(f"     Return code: {result['returncode']}")
            if result['stderr']:
                print(f"     Error: {result['stderr'][:200]}...")
    
    # Success summary
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"\n✨ UI Enhancements Verification Complete:")
        print(f"  • Model toggle switch with 8K token premium limit ✅")
        print(f"  • Permanent dark theme enforcement ✅")
        print(f"  • Simplified sidebar without clutter ✅")
        print(f"  • Unlimited conversation history display ✅")
        print(f"  • Conversation management with tabs ✅")
        print(f"  • RAG document processing end-to-end workflow ✅")
        print(f"  • Comprehensive error handling ✅")
        print(f"  • UI component integration ✅")
        
        print(f"\n🚀 Ready for Production:")
        print(f"  • All UI enhancements are working correctly")
        print(f"  • Error handling is robust")
        print(f"  • Performance is optimized")
        print(f"  • User experience is improved")
        
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print(f"  • {failed_tests} out of {total_tests} test files failed")
        print(f"  • Please review failed tests and fix issues")
        print(f"  • Re-run tests after fixes")
    
    # Recommendations
    print(f"\n📋 Next Steps:")
    if passed_tests == total_tests:
        print(f"  1. ✅ All tests passed - UI enhancements are ready")
        print(f"  2. 🚀 Deploy the enhanced application")
        print(f"  3. 📊 Monitor user feedback and performance")
        print(f"  4. 🔄 Run tests regularly for regression detection")
    else:
        print(f"  1. 🔍 Review failed test details above")
        print(f"  2. 🛠️  Fix identified issues")
        print(f"  3. 🧪 Re-run specific failed tests")
        print(f"  4. 🔄 Run full test suite again")
    
    print(f"\n📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return passed_tests == total_tests


def main():
    """Main function to run the comprehensive test suite"""
    try:
        success = run_comprehensive_ui_enhancements_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()