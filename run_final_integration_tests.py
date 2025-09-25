#!/usr/bin/env python3
"""
Final Integration Test Runner
Comprehensive end-to-end testing of the complete application
"""

import os
import sys
import time
import subprocess
import threading
from typing import Dict, List, Any
import requests
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class FinalIntegrationTestRunner:
    """Comprehensive test runner for final integration validation"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all final integration tests"""
        self.start_time = datetime.now()
        print("🚀 Starting Final Integration Test Suite")
        print("=" * 60)
        
        # Test categories
        test_categories = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("User Journey Tests", self.run_user_journey_tests),
            ("Data Isolation Tests", self.run_data_isolation_tests),
            ("UI/Theme Tests", self.run_ui_theme_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Security Tests", self.run_security_tests),
            ("Deployment Tests", self.run_deployment_tests)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\n📋 Running {category_name}...")
            try:
                result = test_function()
                self.test_results[category_name] = result
                status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
                print(f"   {status} - {result.get('message', 'No message')}")
            except Exception as e:
                self.test_results[category_name] = {
                    'success': False,
                    'error': str(e),
                    'message': f"Test execution failed: {e}"
                }
                print(f"   ❌ FAILED - {e}")
        
        self.end_time = datetime.now()
        return self.generate_final_report()
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests for individual components"""
        try:
            # Run existing unit tests
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "test_auth_unit.py",
                "test_model_manager.py", 
                "test_message_storage.py",
                "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=120)
            
            return {
                'success': result.returncode == 0,
                'message': f"Unit tests completed with return code {result.returncode}",
                'output': result.stdout,
                'errors': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': "Unit tests timed out after 120 seconds"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Unit test execution failed: {e}"
            }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "test_final_integration.py",
                "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=180)
            
            return {
                'success': result.returncode == 0,
                'message': f"Integration tests completed with return code {result.returncode}",
                'output': result.stdout,
                'errors': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': "Integration tests timed out after 180 seconds"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Integration test execution failed: {e}"
            }
    
    def run_user_journey_tests(self) -> Dict[str, Any]:
        """Test complete user journeys"""
        try:
            # Test user signup -> login -> chat -> logout flow
            from test_final_integration import TestFinalIntegration
            
            test_instance = TestFinalIntegration()
            test_instance.setup_test_environment()
            
            # Run user journey test
            test_instance.test_complete_user_journey_signup_to_logout()
            
            return {
                'success': True,
                'message': "User journey tests completed successfully"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"User journey tests failed: {e}"
            }
    
    def run_data_isolation_tests(self) -> Dict[str, Any]:
        """Test user data isolation"""
        try:
            from test_final_integration import TestFinalIntegration
            
            test_instance = TestFinalIntegration()
            test_instance.setup_test_environment()
            
            # Run data isolation test
            test_instance.test_user_data_isolation_multiple_users()
            
            return {
                'success': True,
                'message': "Data isolation tests completed successfully"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Data isolation tests failed: {e}"
            }
    
    def run_ui_theme_tests(self) -> Dict[str, Any]:
        """Test UI components and theme switching"""
        try:
            from test_final_integration import TestFinalIntegration
            
            test_instance = TestFinalIntegration()
            test_instance.setup_test_environment()
            
            # Run theme and UI tests
            test_instance.test_theme_switching_and_responsive_design()
            test_instance.test_ui_component_integration()
            
            return {
                'success': True,
                'message': "UI and theme tests completed successfully"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"UI/Theme tests failed: {e}"
            }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Test performance optimizations"""
        try:
            # Run performance verification
            result = subprocess.run([
                sys.executable, "task14_performance_verification.py"
            ], capture_output=True, text=True, timeout=120)
            
            return {
                'success': result.returncode == 0,
                'message': f"Performance tests completed with return code {result.returncode}",
                'output': result.stdout,
                'errors': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': "Performance tests timed out after 120 seconds"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Performance test execution failed: {e}"
            }
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Test security measures"""
        try:
            from test_final_integration import TestFinalIntegration
            
            test_instance = TestFinalIntegration()
            test_instance.setup_test_environment()
            
            # Run security tests
            test_instance.test_security_and_data_protection()
            
            return {
                'success': True,
                'message': "Security tests completed successfully"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Security tests failed: {e}"
            }
    
    def run_deployment_tests(self) -> Dict[str, Any]:
        """Test deployment readiness"""
        try:
            # Run deployment verification
            result = subprocess.run([
                sys.executable, "verify_deployment.py"
            ], capture_output=True, text=True, timeout=60)
            
            return {
                'success': result.returncode == 0,
                'message': f"Deployment tests completed with return code {result.returncode}",
                'output': result.stdout,
                'errors': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': "Deployment tests timed out after 60 seconds"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Deployment test execution failed: {e}"
            }
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        failed_tests = total_tests - passed_tests
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                'duration_seconds': duration,
                'overall_success': failed_tests == 0
            },
            'detailed_results': self.test_results,
            'timestamp': self.end_time.isoformat(),
            'recommendations': self.generate_recommendations()
        }
        
        self.print_final_report(report)
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_categories = [
            category for category, result in self.test_results.items() 
            if not result.get('success', False)
        ]
        
        if not failed_categories:
            recommendations.append("🎉 All tests passed! Application is ready for deployment.")
            recommendations.append("✅ Consider running additional load testing in production environment.")
            recommendations.append("📊 Monitor application performance and user feedback post-deployment.")
        else:
            recommendations.append("🔧 Address the following failed test categories before deployment:")
            for category in failed_categories:
                error_msg = self.test_results[category].get('message', 'Unknown error')
                recommendations.append(f"   - {category}: {error_msg}")
            
            recommendations.append("🧪 Re-run tests after fixing issues.")
            recommendations.append("📋 Consider implementing additional monitoring for failed areas.")
        
        return recommendations
    
    def print_final_report(self, report: Dict[str, Any]):
        """Print formatted final report"""
        print("\n" + "=" * 60)
        print("📊 FINAL INTEGRATION TEST REPORT")
        print("=" * 60)
        
        summary = report['summary']
        print(f"⏱️  Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"✅ Passed: {summary['passed']}/{summary['total_tests']}")
        print(f"❌ Failed: {summary['failed']}/{summary['total_tests']}")
        
        print(f"\n🎯 Overall Result: {'✅ SUCCESS' if summary['overall_success'] else '❌ FAILURE'}")
        
        print("\n📋 Test Category Results:")
        for category, result in report['detailed_results'].items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            print(f"   {status} {category}")
            if not result.get('success', False) and 'message' in result:
                print(f"      └─ {result['message']}")
        
        print("\n💡 Recommendations:")
        for recommendation in report['recommendations']:
            print(f"   {recommendation}")
        
        print("\n" + "=" * 60)

def main():
    """Main entry point for final integration testing"""
    print("🧬 Pharmacology Chat App - Final Integration Testing")
    print("Testing complete user journey and system integration")
    print()
    
    runner = FinalIntegrationTestRunner()
    report = runner.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if report['summary']['overall_success'] else 1
    
    if exit_code == 0:
        print("\n🎉 All integration tests completed successfully!")
        print("🚀 Application is ready for production deployment!")
    else:
        print("\n⚠️  Some integration tests failed.")
        print("🔧 Please address the issues before deploying to production.")
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)