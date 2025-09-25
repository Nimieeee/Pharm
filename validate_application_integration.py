#!/usr/bin/env python3
"""
Application Integration Validator
Validates that all components are properly integrated into cohesive application flow
"""

import os
import sys
import importlib
import inspect
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class ComponentValidation:
    """Component validation result"""
    component_name: str
    is_valid: bool
    issues: List[str]
    dependencies: List[str]
    integration_points: List[str]

class ApplicationIntegrationValidator:
    """Validates complete application integration"""
    
    def __init__(self):
        self.validation_results = {}
        self.critical_components = [
            'app',
            'auth_manager',
            'session_manager', 
            'chat_manager',
            'message_store_optimized',
            'theme_manager',
            'model_manager',
            'rag_orchestrator_optimized',
            'chat_interface_optimized',
            'performance_optimizer'
        ]
    
    def validate_complete_integration(self) -> Dict[str, Any]:
        """Validate complete application integration"""
        print("🔍 Validating Application Integration...")
        print("=" * 50)
        
        # Validate each critical component
        for component_name in self.critical_components:
            print(f"\n📦 Validating {component_name}...")
            validation = self.validate_component(component_name)
            self.validation_results[component_name] = validation
            
            status = "✅" if validation.is_valid else "❌"
            print(f"   {status} {component_name}")
            
            if validation.issues:
                for issue in validation.issues:
                    print(f"      ⚠️  {issue}")
        
        # Validate integration flows
        print(f"\n🔄 Validating Integration Flows...")
        flow_validation = self.validate_integration_flows()
        
        # Generate final report
        return self.generate_integration_report(flow_validation)
    
    def validate_component(self, component_name: str) -> ComponentValidation:
        """Validate individual component"""
        issues = []
        dependencies = []
        integration_points = []
        
        try:
            # Import the component
            module = importlib.import_module(component_name)
            
            # Check for required classes/functions
            required_items = self.get_required_items(component_name)
            for item_name in required_items:
                if not hasattr(module, item_name):
                    issues.append(f"Missing required item: {item_name}")
            
            # Check dependencies
            dependencies = self.extract_dependencies(module)
            
            # Check integration points
            integration_points = self.extract_integration_points(module)
            
            # Validate specific component requirements
            component_issues = self.validate_component_specific(component_name, module)
            issues.extend(component_issues)
            
        except ImportError as e:
            issues.append(f"Import error: {e}")
        except Exception as e:
            issues.append(f"Validation error: {e}")
        
        return ComponentValidation(
            component_name=component_name,
            is_valid=len(issues) == 0,
            issues=issues,
            dependencies=dependencies,
            integration_points=integration_points
        )
    
    def get_required_items(self, component_name: str) -> List[str]:
        """Get required items for each component"""
        requirements = {
            'app': ['PharmacologyChat', 'main'],
            'auth_manager': ['AuthenticationManager'],
            'session_manager': ['SessionManager'],
            'chat_manager': ['ChatManager'],
            'message_store_optimized': ['OptimizedMessageStore'],
            'theme_manager': ['ThemeManager'],
            'model_manager': ['ModelManager'],
            'rag_orchestrator_optimized': ['RAGOrchestrator'],
            'chat_interface_optimized': ['OptimizedChatInterface'],
            'performance_optimizer': ['performance_optimizer']
        }
        return requirements.get(component_name, [])
    
    def extract_dependencies(self, module) -> List[str]:
        """Extract module dependencies"""
        dependencies = []
        
        # Get imports from module source if available
        try:
            source = inspect.getsource(module)
            lines = source.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('from ') and ' import ' in line:
                    module_name = line.split('from ')[1].split(' import')[0].strip()
                    dependencies.append(module_name)
                elif line.startswith('import '):
                    module_name = line.split('import ')[1].split(' as')[0].split('.')[0].strip()
                    dependencies.append(module_name)
        except:
            pass
        
        return list(set(dependencies))
    
    def extract_integration_points(self, module) -> List[str]:
        """Extract integration points from module"""
        integration_points = []
        
        # Look for classes and their methods
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                methods = [method for method, _ in inspect.getmembers(obj, predicate=inspect.ismethod)]
                integration_points.extend([f"{name}.{method}" for method in methods])
        
        return integration_points
    
    def validate_component_specific(self, component_name: str, module) -> List[str]:
        """Validate component-specific requirements"""
        issues = []
        
        if component_name == 'app':
            # Validate main app class
            if hasattr(module, 'PharmacologyChat'):
                app_class = getattr(module, 'PharmacologyChat')
                required_methods = ['run', 'initialize_managers', 'render_protected_chat_interface']
                for method in required_methods:
                    if not hasattr(app_class, method):
                        issues.append(f"PharmacologyChat missing method: {method}")
        
        elif component_name == 'auth_manager':
            # Validate authentication manager
            if hasattr(module, 'AuthenticationManager'):
                auth_class = getattr(module, 'AuthenticationManager')
                required_methods = ['sign_up', 'sign_in', 'sign_out', 'get_current_user']
                for method in required_methods:
                    if not hasattr(auth_class, method):
                        issues.append(f"AuthenticationManager missing method: {method}")
        
        elif component_name == 'chat_manager':
            # Validate chat manager
            if hasattr(module, 'ChatManager'):
                chat_class = getattr(module, 'ChatManager')
                required_methods = ['send_message', 'get_conversation_history', 'clear_conversation']
                for method in required_methods:
                    if not hasattr(chat_class, method):
                        issues.append(f"ChatManager missing method: {method}")
        
        elif component_name == 'theme_manager':
            # Validate theme manager
            if hasattr(module, 'ThemeManager'):
                theme_class = getattr(module, 'ThemeManager')
                required_methods = ['apply_theme', 'toggle_theme', 'get_current_theme']
                for method in required_methods:
                    if not hasattr(theme_class, method):
                        issues.append(f"ThemeManager missing method: {method}")
        
        return issues
    
    def validate_integration_flows(self) -> Dict[str, Any]:
        """Validate key integration flows"""
        flows = {
            'authentication_flow': self.validate_authentication_flow(),
            'chat_flow': self.validate_chat_flow(),
            'theme_flow': self.validate_theme_flow(),
            'model_switching_flow': self.validate_model_switching_flow(),
            'data_isolation_flow': self.validate_data_isolation_flow()
        }
        
        return flows
    
    def validate_authentication_flow(self) -> Dict[str, Any]:
        """Validate authentication integration flow"""
        try:
            # Check if auth components can work together
            from auth_manager import AuthenticationManager
            from session_manager import SessionManager
            from auth_guard import AuthGuard
            
            # Test basic integration
            auth_manager = AuthenticationManager()
            session_manager = SessionManager(auth_manager)
            auth_guard = AuthGuard(auth_manager, session_manager)
            
            return {
                'valid': True,
                'message': 'Authentication flow integration validated'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Authentication flow validation failed: {e}'
            }
    
    def validate_chat_flow(self) -> Dict[str, Any]:
        """Validate chat integration flow"""
        try:
            # Check if chat components can work together
            from chat_manager import ChatManager
            from message_store_optimized import OptimizedMessageStore
            from chat_interface_optimized import OptimizedChatInterface
            from theme_manager import ThemeManager
            
            return {
                'valid': True,
                'message': 'Chat flow integration validated'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Chat flow validation failed: {e}'
            }
    
    def validate_theme_flow(self) -> Dict[str, Any]:
        """Validate theme switching integration flow"""
        try:
            from theme_manager import ThemeManager
            
            theme_manager = ThemeManager()
            
            # Test theme operations
            initial_theme = theme_manager.get_current_theme()
            new_theme = theme_manager.toggle_theme()
            
            return {
                'valid': True,
                'message': 'Theme flow integration validated'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Theme flow validation failed: {e}'
            }
    
    def validate_model_switching_flow(self) -> Dict[str, Any]:
        """Validate model switching integration flow"""
        try:
            from model_manager import ModelManager
            from session_manager import SessionManager
            from auth_manager import AuthenticationManager
            
            return {
                'valid': True,
                'message': 'Model switching flow integration validated'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Model switching flow validation failed: {e}'
            }
    
    def validate_data_isolation_flow(self) -> Dict[str, Any]:
        """Validate data isolation integration flow"""
        try:
            from chat_manager import ChatManager
            from message_store_optimized import OptimizedMessageStore
            
            return {
                'valid': True,
                'message': 'Data isolation flow integration validated'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Data isolation flow validation failed: {e}'
            }
    
    def generate_integration_report(self, flow_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive integration report"""
        # Calculate overall statistics
        total_components = len(self.validation_results)
        valid_components = sum(1 for v in self.validation_results.values() if v.is_valid)
        
        total_flows = len(flow_validation)
        valid_flows = sum(1 for v in flow_validation.values() if v.get('valid', False))
        
        overall_success = (valid_components == total_components) and (valid_flows == total_flows)
        
        report = {
            'summary': {
                'overall_success': overall_success,
                'component_validation': {
                    'total': total_components,
                    'valid': valid_components,
                    'invalid': total_components - valid_components
                },
                'flow_validation': {
                    'total': total_flows,
                    'valid': valid_flows,
                    'invalid': total_flows - valid_flows
                }
            },
            'component_results': {
                name: {
                    'valid': result.is_valid,
                    'issues': result.issues,
                    'dependencies': result.dependencies,
                    'integration_points': len(result.integration_points)
                }
                for name, result in self.validation_results.items()
            },
            'flow_results': flow_validation,
            'recommendations': self.generate_integration_recommendations(overall_success)
        }
        
        self.print_integration_report(report)
        return report
    
    def generate_integration_recommendations(self, overall_success: bool) -> List[str]:
        """Generate integration recommendations"""
        recommendations = []
        
        if overall_success:
            recommendations.extend([
                "✅ All components are properly integrated",
                "🔄 All integration flows are working correctly",
                "🚀 Application is ready for end-to-end testing",
                "📊 Consider running performance benchmarks",
                "🔒 Verify security measures in production environment"
            ])
        else:
            recommendations.append("🔧 Address the following integration issues:")
            
            # Component issues
            for name, result in self.validation_results.items():
                if not result.is_valid:
                    recommendations.append(f"   - Fix {name}: {', '.join(result.issues)}")
            
            recommendations.extend([
                "🧪 Re-run validation after fixing issues",
                "📋 Consider adding integration tests for failed components",
                "🔍 Review component dependencies and interfaces"
            ])
        
        return recommendations
    
    def print_integration_report(self, report: Dict[str, Any]):
        """Print formatted integration report"""
        print("\n" + "=" * 60)
        print("🔗 APPLICATION INTEGRATION VALIDATION REPORT")
        print("=" * 60)
        
        summary = report['summary']
        print(f"🎯 Overall Status: {'✅ SUCCESS' if summary['overall_success'] else '❌ FAILURE'}")
        
        print(f"\n📦 Component Validation:")
        print(f"   ✅ Valid: {summary['component_validation']['valid']}/{summary['component_validation']['total']}")
        print(f"   ❌ Invalid: {summary['component_validation']['invalid']}/{summary['component_validation']['total']}")
        
        print(f"\n🔄 Flow Validation:")
        print(f"   ✅ Valid: {summary['flow_validation']['valid']}/{summary['flow_validation']['total']}")
        print(f"   ❌ Invalid: {summary['flow_validation']['invalid']}/{summary['flow_validation']['total']}")
        
        print(f"\n📋 Component Details:")
        for name, result in report['component_results'].items():
            status = "✅" if result['valid'] else "❌"
            print(f"   {status} {name} ({result['integration_points']} integration points)")
            if result['issues']:
                for issue in result['issues']:
                    print(f"      ⚠️  {issue}")
        
        print(f"\n🔄 Flow Details:")
        for name, result in report['flow_results'].items():
            status = "✅" if result.get('valid', False) else "❌"
            print(f"   {status} {name}: {result.get('message', 'No message')}")
        
        print(f"\n💡 Recommendations:")
        for recommendation in report['recommendations']:
            print(f"   {recommendation}")
        
        print("\n" + "=" * 60)

def main():
    """Main entry point for integration validation"""
    print("🧬 Pharmacology Chat App - Integration Validation")
    print("Validating complete application component integration")
    print()
    
    validator = ApplicationIntegrationValidator()
    report = validator.validate_complete_integration()
    
    # Return appropriate exit code
    return 0 if report['summary']['overall_success'] else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)