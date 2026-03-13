#!/usr/bin/env python3
"""
Deployment Validation Script for PharmGPT Backend
Validates that the enhanced RAG system is properly deployed and functional
"""

import asyncio
import sys
import os
import time
import json
from typing import Dict, Any, List, Tuple
import httpx
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings


class DeploymentValidator:
    """Validates deployment of enhanced RAG system"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or f"http://localhost:{settings.PORT}"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.validation_results = {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "tests": {},
            "overall_status": "unknown",
            "errors": [],
            "warnings": []
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test result"""
        self.validation_results["tests"][test_name] = {
            "status": status,
            "message": message,
            "details": details or {}
        }
        
        status_emoji = {
            "passed": "✅",
            "failed": "❌", 
            "warning": "⚠️",
            "skipped": "⏭️"
        }
        
        print(f"{status_emoji.get(status, '❓')} {test_name}: {message}")
        
        if details and settings.DEBUG:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    async def test_basic_connectivity(self) -> bool:
        """Test basic server connectivity"""
        try:
            response = await self.client.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                self.log_test(
                    "basic_connectivity", 
                    "passed", 
                    f"Server responding on {self.base_url}"
                )
                return True
            else:
                self.log_test(
                    "basic_connectivity", 
                    "failed", 
                    f"Server returned status {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "basic_connectivity", 
                "failed", 
                f"Connection failed: {str(e)}"
            )
            return False
    
    async def test_health_endpoints(self) -> bool:
        """Test health check endpoints"""
        health_endpoints = [
            "/api/v1/health",
            "/api/v1/health/embeddings", 
            "/api/v1/health/migration",
            "/api/v1/health/database",
            "/api/v1/health/performance"
        ]
        
        all_passed = True
        
        for endpoint in health_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    
                    if status == "healthy":
                        self.log_test(
                            f"health_{endpoint.split('/')[-1]}", 
                            "passed", 
                            f"Health check passed"
                        )
                    elif status == "degraded":
                        self.log_test(
                            f"health_{endpoint.split('/')[-1]}", 
                            "warning", 
                            f"Service degraded: {data.get('errors', [])}"
                        )
                        self.validation_results["warnings"].extend(data.get("errors", []))
                    else:
                        self.log_test(
                            f"health_{endpoint.split('/')[-1]}", 
                            "failed", 
                            f"Service unhealthy: {data.get('errors', [])}"
                        )
                        self.validation_results["errors"].extend(data.get("errors", []))
                        all_passed = False
                else:
                    self.log_test(
                        f"health_{endpoint.split('/')[-1]}", 
                        "failed", 
                        f"Health endpoint returned {response.status_code}"
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test(
                    f"health_{endpoint.split('/')[-1]}", 
                    "failed", 
                    f"Health check failed: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    async def test_embedding_generation(self) -> bool:
        """Test embedding generation functionality"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/health/test-embedding"
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    details = data.get("test_details", {})
                    self.log_test(
                        "embedding_generation", 
                        "passed", 
                        f"Embedding test passed ({details.get('embedding_dimensions')} dims, "
                        f"{details.get('generation_time', 0):.3f}s)",
                        details
                    )
                    return True
                else:
                    self.log_test(
                        "embedding_generation", 
                        "failed", 
                        f"Embedding test failed: {data.get('message')}"
                    )
                    return False
            else:
                self.log_test(
                    "embedding_generation", 
                    "failed", 
                    f"Embedding test endpoint returned {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "embedding_generation", 
                "failed", 
                f"Embedding test failed: {str(e)}"
            )
            return False
    
    async def test_api_documentation(self) -> bool:
        """Test API documentation availability"""
        try:
            response = await self.client.get(f"{self.base_url}/docs")
            
            if response.status_code == 200:
                self.log_test(
                    "api_documentation", 
                    "passed", 
                    "API documentation accessible"
                )
                return True
            else:
                self.log_test(
                    "api_documentation", 
                    "failed", 
                    f"API docs returned {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "api_documentation", 
                "failed", 
                f"API docs test failed: {str(e)}"
            )
            return False
    
    async def test_configuration_validation(self) -> bool:
        """Test configuration validation"""
        config_tests = []
        
        # Test required environment variables
        required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SECRET_KEY"]
        for var in required_vars:
            value = getattr(settings, var, None)
            if value:
                config_tests.append(f"{var}: configured")
            else:
                config_tests.append(f"{var}: MISSING")
                self.validation_results["errors"].append(f"Missing required variable: {var}")
        
        # Test optional but important variables
        optional_vars = {
            "MISTRAL_API_KEY": "Mistral embeddings",
            "USE_MISTRAL_EMBEDDINGS": "Mistral integration",
            "USE_LANGCHAIN_LOADERS": "LangChain loaders"
        }
        
        for var, description in optional_vars.items():
            value = getattr(settings, var, None)
            if value:
                config_tests.append(f"{var}: {value} ({description})")
            else:
                config_tests.append(f"{var}: not set ({description})")
                self.validation_results["warnings"].append(f"Optional variable not set: {var}")
        
        # Test configuration values
        chunk_size = getattr(settings, "LANGCHAIN_CHUNK_SIZE", 0)
        chunk_overlap = getattr(settings, "LANGCHAIN_CHUNK_OVERLAP", 0)
        
        if chunk_overlap >= chunk_size:
            self.validation_results["errors"].append("Chunk overlap >= chunk size")
            config_tests.append("Chunk configuration: INVALID")
        else:
            config_tests.append(f"Chunk configuration: {chunk_size}/{chunk_overlap}")
        
        has_errors = any("MISSING" in test or "INVALID" in test for test in config_tests)
        
        self.log_test(
            "configuration_validation", 
            "failed" if has_errors else "passed", 
            f"Configuration validation {'failed' if has_errors else 'passed'}",
            {"tests": config_tests}
        )
        
        return not has_errors
    
    async def test_database_migration_status(self) -> bool:
        """Test database migration status"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health/migration")
            
            if response.status_code == 200:
                data = response.json()
                migration_status = data.get("migration_status", {})
                validation = data.get("validation", {})
                
                migration_percentage = migration_status.get("migration_percentage", 0)
                
                if migration_percentage == 100 and validation.get("valid", False):
                    self.log_test(
                        "database_migration", 
                        "passed", 
                        "Database migration completed successfully"
                    )
                    return True
                elif migration_percentage > 0:
                    self.log_test(
                        "database_migration", 
                        "warning", 
                        f"Migration {migration_percentage}% complete",
                        migration_status
                    )
                    return True
                else:
                    self.log_test(
                        "database_migration", 
                        "warning", 
                        "No migration detected - using legacy embeddings",
                        migration_status
                    )
                    return True
            else:
                self.log_test(
                    "database_migration", 
                    "failed", 
                    f"Migration status check returned {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "database_migration", 
                "failed", 
                f"Migration status check failed: {str(e)}"
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print(f"🚀 Starting deployment validation for {self.base_url}")
        print("=" * 60)
        
        test_functions = [
            self.test_basic_connectivity,
            self.test_configuration_validation,
            self.test_health_endpoints,
            self.test_embedding_generation,
            self.test_database_migration_status,
            self.test_api_documentation
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_func in test_functions:
            try:
                result = await test_func()
                if result:
                    passed_tests += 1
            except Exception as e:
                self.log_test(
                    test_func.__name__, 
                    "failed", 
                    f"Test execution failed: {str(e)}"
                )
                self.validation_results["errors"].append(f"Test {test_func.__name__} failed: {str(e)}")
        
        # Determine overall status
        if passed_tests == total_tests and not self.validation_results["errors"]:
            self.validation_results["overall_status"] = "passed"
        elif passed_tests > 0 and not self.validation_results["errors"]:
            self.validation_results["overall_status"] = "warning"
        else:
            self.validation_results["overall_status"] = "failed"
        
        print("=" * 60)
        print(f"📊 Validation Summary:")
        print(f"   Tests passed: {passed_tests}/{total_tests}")
        print(f"   Overall status: {self.validation_results['overall_status'].upper()}")
        
        if self.validation_results["errors"]:
            print(f"   Errors: {len(self.validation_results['errors'])}")
            for error in self.validation_results["errors"]:
                print(f"     ❌ {error}")
        
        if self.validation_results["warnings"]:
            print(f"   Warnings: {len(self.validation_results['warnings'])}")
            for warning in self.validation_results["warnings"]:
                print(f"     ⚠️  {warning}")
        
        return self.validation_results


async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate PharmGPT deployment")
    parser.add_argument(
        "--url", 
        default=None, 
        help="Base URL to test (default: http://localhost:PORT)"
    )
    parser.add_argument(
        "--output", 
        default=None, 
        help="Output file for validation results (JSON)"
    )
    parser.add_argument(
        "--fail-on-warnings", 
        action="store_true", 
        help="Exit with error code if warnings are found"
    )
    
    args = parser.parse_args()
    
    # Determine base URL
    base_url = args.url
    if not base_url:
        port = getattr(settings, 'PORT', 8000)
        base_url = f"http://localhost:{port}"
    
    # Run validation
    async with DeploymentValidator(base_url) as validator:
        results = await validator.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Results saved to {args.output}")
    
    # Determine exit code
    if results["overall_status"] == "failed":
        print("💥 Deployment validation FAILED")
        sys.exit(1)
    elif results["overall_status"] == "warning" and args.fail_on_warnings:
        print("⚠️  Deployment validation has WARNINGS (treated as failure)")
        sys.exit(1)
    else:
        print("✅ Deployment validation PASSED")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())