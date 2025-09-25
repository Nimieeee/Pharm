"""
Comprehensive Test Runner
Executes all test suites for the pharmacology chat app
"""

import sys
import os
import subprocess
from datetime import datetime
import traceback

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test modules
from test_comprehensive_suite import TestRunner
from test_auth_unit import run_auth_unit_tests
from test_data_isolation import run_data_isolation_tests
from test_rag_mock import run_rag_mock_tests
from test_ui_comprehensive import run_ui_comprehensive_tests


class ComprehensiveTestRunner:
    """Main test runner for all test suites"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.test_results = {
            'comprehensive_suite': {'status': 'pending', 'duration': 0},
            'auth_unit_tests': {'status': 'pending', 'duration': 0},
            'data_isolation_tests': {'status': 'pending', 'duration': 0},
            'rag_mock_tests': {'status': 'pending', 'duration': 0},
            'ui_comprehensive_tests': {'status': 'pending', 'duration': 0}
        }
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 COMPREHENSIVE TEST SUITE EXECUTION")
        print("=" * 80)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        overall_success = True
        
        # Run each test suite
        test_suites = [
            ("Comprehensive Suite", self._run_comprehensive_suite),
            ("Authentication Unit Tests", self._run_auth_unit_tests),
            ("Data Isolation Tests", self._run_data_isolation_tests),
            ("RAG Pipeline Mock Tests", self._run_rag_mock_tests),
            ("UI Comprehensive Tests", self._run_ui_comprehensive_tests)
        ]
        
        for suite_name, test_function in test_suites:
            print(f"\n{'='*20} {suite_name} {'='*20}")
            
            suite_start = datetime.now()
            try:
                success = test_function()
                suite_end = datetime.now()
                duration = (suite_end - suite_start).total_seconds()
                
                suite_key = suite_name.lower().replace(' ', '_')
                self.test_results[suite_key]['status'] = 'passed' if success else 'failed'
                self.test_results[suite_key]['duration'] = duration
                
                if not success:
                    overall_success = False
                    
            except Exception as e:
                suite_end = datetime.now()
                duration = (suite_end - suite_start).total_seconds()
                
                suite_key = suite_name.lower().replace(' ', '_')
                self.test_results[suite_key]['status'] = 'error'
                self.test_results[suite_key]['duration'] = duration
                
                print(f"❌ {suite_name} encountered an error: {str(e)}")
                traceback.print_exc()
                overall_success = False
        
        # Print final summary
        self._print_final_summary(overall_success)
        
        return overall_success
    
    def _run_comprehensive_suite(self):
        """Run the main comprehensive test suite"""
        try:
            test_runner = TestRunner()
            return test_runner.run_all_tests()
        except Exception as e:
            print(f"Error running comprehensive suite: {e}")
            return False
    
    def _run_auth_unit_tests(self):
        """Run authentication unit tests"""
        try:
            return run_auth_unit_tests()
        except Exception as e:
            print(f"Error running auth unit tests: {e}")
            return False
    
    def _run_data_isolation_tests(self):
        """Run data isolation tests"""
        try:
            return run_data_isolation_tests()
        except Exception as e:
            print(f"Error running data isolation tests: {e}")
            return False
    
    def _run_rag_mock_tests(self):
        """Run RAG pipeline mock tests"""
        try:
            return run_rag_mock_tests()
        except Exception as e:
            print(f"Error running RAG mock tests: {e}")
            return False
    
    def _run_ui_comprehensive_tests(self):
        """Run UI comprehensive tests"""
        try:
            return run_ui_comprehensive_tests()
        except Exception as e:
            print(f"Error running UI comprehensive tests: {e}")
            return False
    
    def _print_final_summary(self, overall_success):
        """Print final test execution summary"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 FINAL TEST EXECUTION SUMMARY")
        print("=" * 80)
        
        # Print individual suite results
        passed_count = 0
        failed_count = 0
        error_count = 0
        
        for suite_name, results in self.test_results.items():
            status = results['status']
            duration = results['duration']
            
            if status == 'passed':
                status_icon = "✅"
                passed_count += 1
            elif status == 'failed':
                status_icon = "❌"
                failed_count += 1
            else:  # error
                status_icon = "💥"
                error_count += 1
            
            suite_display = suite_name.replace('_', ' ').title()
            print(f"{status_icon} {suite_display:<30} {status:<8} ({duration:.2f}s)")
        
        print("-" * 80)
        print(f"Total Execution Time: {total_duration:.2f} seconds")
        print(f"Test Suites: {passed_count} passed, {failed_count} failed, {error_count} errors")
        
        if overall_success:
            print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
            print("\n✅ Test Coverage Summary:")
            print("   • Authentication system (unit & integration)")
            print("   • Session management and user isolation")
            print("   • RAG pipeline with mock vector database")
            print("   • UI components and theme switching")
            print("   • Responsive design and accessibility")
            print("   • Error handling and fallback mechanisms")
            print("   • End-to-end user flows")
            
            print("\n🚀 The pharmacology chat app is ready for deployment!")
            
        else:
            print(f"\n❌ {failed_count + error_count} TEST SUITE(S) FAILED")
            print("\n🔧 Please review the failed tests above and fix the issues.")
            print("   Run individual test suites for more detailed error information.")
        
        print("\n" + "=" * 80)
    
    def run_specific_suite(self, suite_name):
        """Run a specific test suite"""
        suite_functions = {
            'comprehensive': self._run_comprehensive_suite,
            'auth': self._run_auth_unit_tests,
            'isolation': self._run_data_isolation_tests,
            'rag': self._run_rag_mock_tests,
            'ui': self._run_ui_comprehensive_tests
        }
        
        if suite_name.lower() in suite_functions:
            print(f"Running {suite_name} test suite...")
            return suite_functions[suite_name.lower()]()
        else:
            print(f"Unknown test suite: {suite_name}")
            print(f"Available suites: {', '.join(suite_functions.keys())}")
            return False


def run_pytest_tests():
    """Run pytest-based tests if available"""
    try:
        # Check if pytest is available
        import pytest
        
        print("🔬 Running pytest-based tests...")
        
        # Run pytest on test files
        test_files = [
            "test_comprehensive_suite.py",
            "test_auth_unit.py",
            "test_data_isolation.py",
            "test_rag_mock.py",
            "test_ui_comprehensive.py"
        ]
        
        # Filter existing test files
        existing_files = [f for f in test_files if os.path.exists(f)]
        
        if existing_files:
            result = pytest.main(["-v"] + existing_files)
            return result == 0
        else:
            print("No pytest test files found")
            return True
            
    except ImportError:
        print("pytest not available, skipping pytest tests")
        return True
    except Exception as e:
        print(f"Error running pytest: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Run specific test suite
        suite_name = sys.argv[1]
        runner = ComprehensiveTestRunner()
        success = runner.run_specific_suite(suite_name)
    else:
        # Run all tests
        runner = ComprehensiveTestRunner()
        success = runner.run_all_tests()
        
        # Also run pytest tests if available
        pytest_success = run_pytest_tests()
        success = success and pytest_success
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())