#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies that all components are properly configured for Streamlit Cloud deployment
"""

import sys
import importlib
import subprocess
from typing import List, Dict, Any
from deployment_config import deployment_config
from health_check import health_checker, error_monitor

def check_dependencies() -> Dict[str, bool]:
    """Check if all required dependencies can be imported"""
    required_modules = [
        'streamlit',
        'supabase',
        'langchain',
        'groq',
        'sentence_transformers',
        'psutil',
        'numpy',
        'pandas'
    ]
    
    results = {}
    for module in required_modules:
        try:
            importlib.import_module(module)
            results[module] = True
        except ImportError:
            results[module] = False
    
    return results

def check_application_modules() -> Dict[str, bool]:
    """Check if all application modules can be imported"""
    app_modules = [
        'auth_manager',
        'session_manager', 
        'chat_manager',
        'message_store',
        'model_manager',
        'theme_manager',
        'rag_orchestrator_optimized',
        'vector_retriever',
        'document_processor',
        'deployment_config',
        'health_check'
    ]
    
    results = {}
    for module in app_modules:
        try:
            importlib.import_module(module)
            results[module] = True
        except ImportError as e:
            results[module] = False
            print(f"Failed to import {module}: {e}")
    
    return results

def check_configuration() -> Dict[str, Any]:
    """Check deployment configuration"""
    try:
        config_status = {
            'config_loaded': True,
            'environment': deployment_config.environment,
            'is_production': deployment_config.is_production(),
            'database_config': bool(deployment_config.get_database_config()),
            'model_config': bool(deployment_config.get_model_config())
        }
        
        # Validate configuration
        validation_results = deployment_config.validate_config()
        config_status.update(validation_results)
        
        return config_status
        
    except Exception as e:
        return {
            'config_loaded': False,
            'error': str(e)
        }

def check_streamlit_config() -> Dict[str, bool]:
    """Check Streamlit configuration files"""
    import os
    
    config_files = {
        '.streamlit/config.toml': os.path.exists('.streamlit/config.toml'),
        'requirements.txt': os.path.exists('requirements.txt'),
        'app.py': os.path.exists('app.py'),
        'DEPLOYMENT_GUIDE.md': os.path.exists('DEPLOYMENT_GUIDE.md')
    }
    
    return config_files

def run_health_checks() -> Dict[str, Any]:
    """Run comprehensive health checks"""
    try:
        health_results = health_checker.run_comprehensive_health_check()
        overall_status = health_checker.get_overall_status(health_results)
        
        return {
            'overall_status': overall_status,
            'individual_checks': {k: v.status for k, v in health_results.items()},
            'health_check_available': True
        }
    except Exception as e:
        return {
            'health_check_available': False,
            'error': str(e)
        }

def print_results(title: str, results: Dict[str, Any], success_key: str = None):
    """Print formatted results"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    
    for key, value in results.items():
        if isinstance(value, bool):
            status = "✅ PASS" if value else "❌ FAIL"
            print(f"{key:30} {status}")
        elif isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, bool):
                    status = "✅ PASS" if sub_value else "❌ FAIL"
                    print(f"  {sub_key:28} {status}")
                else:
                    print(f"  {sub_key:28} {sub_value}")
        else:
            print(f"{key:30} {value}")

def main():
    """Main verification function"""
    print("🚀 Streamlit Cloud Deployment Verification")
    print("=" * 50)
    
    all_passed = True
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    dep_results = check_dependencies()
    print_results("Dependency Check", dep_results)
    if not all(dep_results.values()):
        all_passed = False
    
    # Check application modules
    print("\n🔧 Checking Application Modules...")
    app_results = check_application_modules()
    print_results("Application Module Check", app_results)
    if not all(app_results.values()):
        all_passed = False
    
    # Check configuration
    print("\n⚙️  Checking Configuration...")
    config_results = check_configuration()
    print_results("Configuration Check", config_results)
    
    # Check Streamlit files
    print("\n📄 Checking Streamlit Files...")
    file_results = check_streamlit_config()
    print_results("Streamlit File Check", file_results)
    if not all(file_results.values()):
        all_passed = False
    
    # Run health checks
    print("\n🏥 Running Health Checks...")
    health_results = run_health_checks()
    print_results("Health Check", health_results)
    
    # Final summary
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 DEPLOYMENT VERIFICATION PASSED")
        print("Your application is ready for Streamlit Cloud deployment!")
    else:
        print("⚠️  DEPLOYMENT VERIFICATION FAILED")
        print("Please fix the issues above before deploying.")
        sys.exit(1)
    
    print(f"{'='*50}")
    
    # Deployment instructions
    print("\n📋 Next Steps:")
    print("1. Push your code to GitHub")
    print("2. Deploy to Streamlit Cloud")
    print("3. Configure secrets in Streamlit Cloud dashboard")
    print("4. Test your deployed application")
    print("5. Monitor health at: https://your-app.streamlit.app/?page=health&token=your_token")

if __name__ == "__main__":
    main()