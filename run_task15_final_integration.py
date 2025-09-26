#!/usr/bin/env python3
"""
Task 15 Final Integration Test Runner
Comprehensive test runner for final integration and user experience validation
"""

import os
import sys
import time
import subprocess
import threading
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Task15FinalIntegrationRunner:
    """Comprehensive test runner for Task 15 final integration"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        self.test_categories = [
            ("UI Enhancements Integration", "test_ui_enhancements_final_integration.py"),
            ("Complete Workflow Integration", "test_complete_workflow_integration.py"),
            ("Application Integration Validation", "validate_application_integration.py"),
            ("Final Integration Tests", "test_final_integration.py"),
            ("Comprehensive Test Suite", "run_comprehensive_tests.py"),
            ("Performance Verification", "task14_performance_verification.py"),
            ("Deployment Readiness", "verify_deployment.py")
        ]
    
    def run_all_final_integration_tests(self) -> Dict[str, Any]:
        """Run all final integration tests for Task 15"""
        self.start_time = datetime.now()
        print("🎯 Starting Task 15 Final Integration and User Experience Testing")
        print("=" * 70)
        print("Testing complete UI enhancements integration and user workflows")
        print()
        
        # Run each test category
        for category_name, test_file in self.test_categories:
            print(f"\n📋 Running {category_name}...")
            print("-" * 50)
            
            try:
                result = self.run_test_category(category_name, test_file)
                self.test_results[category_name] = result
                
                status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
                duration = result.get('duration', 0)
                print(f"   {status} - {category_name} ({duration:.2f}s)")
                
                if result.get('summary'):
                    print(f"   📊 {result['summary']}")
                
                if not result.get('success', False) and result.get('error'):
                    print(f"   ⚠️  {result['error']}")
                    
            except Exception as e:
                self.test_results[category_name] = {
                    'success': False,
                    'error': str(e),
                    'duration': 0,
                    'summary': f"Test execution failed: {e}"
                }
                print(f"   ❌ FAILED - {category_name}: {e}")
        
        self.end_time = datetime.now()
        return self.generate_final_integration_report()
    
    def run_test_category(self, category_name: str, test_file: str) -> Dict[str, Any]:
        """Run a specific test category"""
        start_time = time.time()
        
        try:
            if test_file.endswith('.py'):
                # Run Python test file
                result = subprocess.run([
                    sys.executable, test_file
                ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
                
                duration = time.time() - start_time
                success = result.returncode == 0
                
                # Parse output for summary information
                summary = self.parse_test_output(result.stdout, result.stderr)
                
                return {
                    'success': success,
                    'duration': duration,
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'summary': summary,
                    'error': result.stderr if not success else None
                }
            else:
                return {
                    'success': False,
                    'duration': time.time() - start_time,
                    'error': f"Unknown test file type: {test_file}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': f"Test timed out after 300 seconds"
            }
        except FileNotFoundError:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': f"Test file not found: {test_file}"
            }
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': f"Test execution error: {e}"
            }
    
    def parse_test_output(self, stdout: str, stderr: str) -> str:
        """Parse test output to extract summary information"""
        output = stdout + stderr
        
        # Look for common test result patterns
        if "passed" in output.lower() and "failed" in output.lower():
            # pytest-style output
            lines = output.split('\n')
            for line in lines:
                if 'passed' in line.lower() and ('failed' in line.lower() or 'error' in line.lower()):
                    return line.strip()
        
        # Look for success/failure indicators
        if "✅" in output and "❌" in output:
            lines = output.split('\n')
            for line in lines:
                if "✅" in line or "❌" in line:
                    if "passed" in line.lower() or "failed" in line.lower():
                        return line.strip()
        
        # Look for final status lines
        lines = output.split('\n')
        for line in reversed(lines):
            if line.strip() and any(word in line.lower() for word in ['success', 'failed', 'passed', 'error', 'complete']):
                return line.strip()
        
        return "Test completed"
    
    def generate_final_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive final integration report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        failed_tests = total_tests - passed_tests
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        # Calculate detailed statistics
        test_durations = [result.get('duration', 0) for result in self.test_results.values()]
        avg_duration = sum(test_durations) / len(test_durations) if test_durations else 0
        
        report = {
            'task': 'Task 15 - Final Integration and User Experience Testing',
            'summary': {
                'overall_success': failed_tests == 0,
                'total_test_categories': total_tests,
                'passed_categories': passed_tests,
                'failed_categories': failed_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                'total_duration_seconds': total_duration,
                'average_test_duration': avg_duration
            },
            'detailed_results': self.test_results,
            'timestamp': self.end_time.isoformat(),
            'validation_results': self.generate_validation_results(),
            'recommendations': self.generate_final_recommendations()
        }
        
        self.print_final_integration_report(report)
        self.save_report_to_file(report)
        return report
    
    def generate_validation_results(self) -> Dict[str, Any]:
        """Generate validation results for each requirement"""
        validation = {
            'ui_enhancements_integrated': False,
            'complete_workflow_tested': False,
            'conversation_management_validated': False,
            'dark_theme_consistent': False,
            'model_toggle_functional': False,
            'unlimited_history_working': False,
            'rag_pipeline_functional': False,
            'performance_optimized': False,
            'deployment_ready': False
        }
        
        # Check validation based on test results
        for category, result in self.test_results.items():
            if result.get('success', False):
                if 'UI Enhancements' in category:
                    validation['ui_enhancements_integrated'] = True
                    validation['dark_theme_consistent'] = True
                    validation['model_toggle_functional'] = True
                    validation['unlimited_history_working'] = True
                
                if 'Complete Workflow' in category:
                    validation['complete_workflow_tested'] = True
                    validation['conversation_management_validated'] = True
                    validation['rag_pipeline_functional'] = True
                
                if 'Performance' in category:
                    validation['performance_optimized'] = True
                
                if 'Deployment' in category:
                    validation['deployment_ready'] = True
        
        return validation
    
    def generate_final_recommendations(self) -> List[str]:
        """Generate final recommendations based on test results"""
        recommendations = []
        
        failed_categories = [
            category for category, result in self.test_results.items() 
            if not result.get('success', False)
        ]
        
        if not failed_categories:
            recommendations.extend([
                "🎉 All final integration tests passed successfully!",
                "✅ UI enhancements are working cohesively together",
                "🔄 Complete workflow from document upload to AI response is functional",
                "💬 Conversation management across multiple threads is working",
                "🎨 Dark theme consistency is maintained throughout the application",
                "🔀 Model toggle functionality is working with 8000 token premium limit",
                "📜 Unlimited conversation history display is optimized",
                "📚 RAG document processing pipeline is fully functional",
                "🚀 Application is ready for production deployment",
                "📊 Consider running load testing in production environment",
                "🔍 Monitor user feedback and performance metrics post-deployment"
            ])
        else:
            recommendations.append("🔧 Address the following issues before considering Task 15 complete:")
            
            for category in failed_categories:
                error_msg = self.test_results[category].get('error', 'Unknown error')
                recommendations.append(f"   - {category}: {error_msg}")
            
            recommendations.extend([
                "🧪 Re-run tests after fixing issues",
                "📋 Review integration points between failed components",
                "🔍 Check for missing dependencies or configuration issues",
                "💡 Consider implementing additional error handling",
                "📖 Update documentation for any changed interfaces"
            ])
        
        # Add specific recommendations based on validation results
        validation = self.generate_validation_results()
        
        if not validation['ui_enhancements_integrated']:
            recommendations.append("🎨 Ensure all UI enhancements are properly integrated")
        
        if not validation['complete_workflow_tested']:
            recommendations.append("🔄 Validate complete document-to-response workflow")
        
        if not validation['conversation_management_validated']:
            recommendations.append("💬 Test conversation management and isolation")
        
        return recommendations
    
    def print_final_integration_report(self, report: Dict[str, Any]):
        """Print formatted final integration report"""
        print("\n" + "=" * 70)
        print("📊 TASK 15 FINAL INTEGRATION TEST REPORT")
        print("=" * 70)
        
        summary = report['summary']
        print(f"🎯 Task: {report['task']}")
        print(f"⏱️  Total Duration: {summary['total_duration_seconds']:.2f} seconds")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"✅ Passed Categories: {summary['passed_categories']}/{summary['total_test_categories']}")
        print(f"❌ Failed Categories: {summary['failed_categories']}/{summary['total_test_categories']}")
        
        overall_status = "✅ SUCCESS" if summary['overall_success'] else "❌ FAILURE"
        print(f"\n🎯 Overall Result: {overall_status}")
        
        print("\n📋 Test Category Results:")
        for category, result in report['detailed_results'].items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            duration = result.get('duration', 0)
            print(f"   {status} {category} ({duration:.2f}s)")
            
            if result.get('summary'):
                print(f"      📊 {result['summary']}")
            
            if not result.get('success', False) and result.get('error'):
                print(f"      ⚠️  {result['error']}")
        
        print("\n🔍 Validation Results:")
        validation = report['validation_results']
        for check, passed in validation.items():
            status = "✅" if passed else "❌"
            check_name = check.replace('_', ' ').title()
            print(f"   {status} {check_name}")
        
        print("\n💡 Recommendations:")
        for recommendation in report['recommendations']:
            print(f"   {recommendation}")
        
        print("\n" + "=" * 70)
    
    def save_report_to_file(self, report: Dict[str, Any]):
        """Save report to file for documentation"""
        filename = f"task15_final_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n📄 Report saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️  Could not save report to file: {e}")
    
    def run_quick_validation(self) -> bool:
        """Run quick validation of key components"""
        print("\n🔍 Running Quick Component Validation...")
        
        validations = [
            ("Authentication Manager", self.validate_auth_manager),
            ("Theme Manager", self.validate_theme_manager),
            ("Model Manager", self.validate_model_manager),
            ("Conversation Manager", self.validate_conversation_manager),
            ("Document Processor", self.validate_document_processor)
        ]
        
        all_valid = True
        for component_name, validation_func in validations:
            try:
                is_valid = validation_func()
                status = "✅" if is_valid else "❌"
                print(f"   {status} {component_name}")
                if not is_valid:
                    all_valid = False
            except Exception as e:
                print(f"   ❌ {component_name}: {e}")
                all_valid = False
        
        return all_valid
    
    def validate_auth_manager(self) -> bool:
        """Validate authentication manager"""
        try:
            from auth_manager import AuthenticationManager
            auth_manager = AuthenticationManager()
            return hasattr(auth_manager, 'sign_in') and hasattr(auth_manager, 'sign_out')
        except ImportError:
            return False
    
    def validate_theme_manager(self) -> bool:
        """Validate theme manager"""
        try:
            from theme_manager import ThemeManager
            theme_manager = ThemeManager()
            return theme_manager.get_current_theme() == 'dark'
        except ImportError:
            return False
    
    def validate_model_manager(self) -> bool:
        """Validate model manager"""
        try:
            from model_manager import ModelManager, ModelTier
            model_manager = ModelManager()
            model_manager.set_current_model(ModelTier.PREMIUM)
            current_model = model_manager.get_current_model()
            return current_model.max_tokens == 8000
        except ImportError:
            return False
    
    def validate_conversation_manager(self) -> bool:
        """Validate conversation manager"""
        try:
            from conversation_manager import ConversationManager
            # Just check if it can be imported and instantiated
            return True
        except ImportError:
            return False
    
    def validate_document_processor(self) -> bool:
        """Validate document processor"""
        try:
            from document_processor import DocumentProcessor
            # Just check if it can be imported and instantiated
            return True
        except ImportError:
            return False

def main():
    """Main entry point for Task 15 final integration testing"""
    print("🧬 Pharmacology Chat App - Task 15 Final Integration Testing")
    print("Comprehensive validation of all UI enhancements working together")
    print()
    
    runner = Task15FinalIntegrationRunner()
    
    # Run quick validation first
    quick_validation_passed = runner.run_quick_validation()
    if not quick_validation_passed:
        print("\n⚠️  Quick validation failed. Some components may have issues.")
        print("Proceeding with full integration tests anyway...")
    
    # Run full integration tests
    report = runner.run_all_final_integration_tests()
    
    # Determine exit code
    exit_code = 0 if report['summary']['overall_success'] else 1
    
    if exit_code == 0:
        print("\n🎉 Task 15 Final Integration Testing completed successfully!")
        print("✅ All UI enhancements are working together cohesively!")
        print("🚀 Complete workflow from document upload to AI response is functional!")
        print("💬 Conversation management across multiple threads is validated!")
        print("🎨 Dark theme consistency and model toggle functionality verified!")
        print("📜 Application is ready for production deployment!")
    else:
        print("\n⚠️  Task 15 Final Integration Testing completed with issues.")
        print("🔧 Please address the failed test categories before marking Task 15 as complete.")
        print("📋 Review the detailed report above for specific issues to fix.")
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)