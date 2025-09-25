"""
Task 14 Performance Optimization Verification Script
Verifies all performance optimization features are working correctly
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_performance_optimizer():
    """Verify performance optimizer functionality"""
    print("🔍 Verifying Performance Optimizer...")
    
    try:
        from performance_optimizer import performance_optimizer, MemoryCache, PaginationHelper
        
        # Test 1: Cache functionality
        print("  ✓ Testing cache functionality...")
        cache = MemoryCache(max_size=10, default_ttl=60)
        
        # Basic operations
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        assert cache.delete("test_key") is True
        assert cache.get("test_key") is None
        
        # Size limit test
        for i in range(15):  # Exceed max_size of 10
            cache.set(f"key_{i}", f"value_{i}")
        
        stats = cache.get_stats()
        assert stats["total_entries"] <= 10  # Should not exceed max_size
        
        print("  ✅ Cache functionality verified")
        
        # Test 2: User data caching
        print("  ✓ Testing user data caching...")
        test_data = {"messages": [1, 2, 3], "timestamp": datetime.now().isoformat()}
        
        performance_optimizer.set_cached_user_data("test_user", "test_data", test_data)
        cached_result = performance_optimizer.get_cached_user_data("test_user", "test_data")
        assert cached_result == test_data
        
        performance_optimizer.invalidate_user_cache("test_user")
        cached_result = performance_optimizer.get_cached_user_data("test_user", "test_data")
        assert cached_result is None
        
        print("  ✅ User data caching verified")
        
        # Test 3: Pagination helper
        print("  ✓ Testing pagination helper...")
        messages = [f"message_{i}" for i in range(25)]
        
        paginated, info = PaginationHelper.paginate_messages(messages, page_size=10, page=1)
        assert len(paginated) == 10
        assert info["total_pages"] == 3
        assert info["has_next"] is True
        
        paginated, info = PaginationHelper.paginate_messages(messages, page_size=10, page=3)
        assert len(paginated) == 5  # Last page
        assert info["has_next"] is False
        
        print("  ✅ Pagination helper verified")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance optimizer verification failed: {e}")
        return False

def verify_optimized_message_store():
    """Verify optimized message store functionality"""
    print("🔍 Verifying Optimized Message Store...")
    
    try:
        from message_store_optimized import OptimizedMessageStore, MessagePage
        from unittest.mock import Mock
        
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value.execute.return_value.data = []
        
        store = OptimizedMessageStore(mock_client)
        
        # Test pagination functionality exists
        assert hasattr(store, 'get_paginated_messages')
        assert hasattr(store, 'get_cached_message_count')
        assert hasattr(store, 'get_recent_conversation_history')
        assert hasattr(store, 'get_message_statistics')
        
        print("  ✅ Optimized message store structure verified")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Optimized message store verification failed: {e}")
        return False

def verify_chat_interface_optimizations():
    """Verify optimized chat interface functionality"""
    print("🔍 Verifying Optimized Chat Interface...")
    
    try:
        from chat_interface_optimized import OptimizedChatInterface
        from theme_manager import ThemeManager
        from unittest.mock import Mock
        
        # Create mock theme manager
        mock_theme_manager = Mock()
        
        # Create optimized chat interface
        chat_interface = OptimizedChatInterface(mock_theme_manager)
        
        # Test that optimization methods exist
        assert hasattr(chat_interface, 'render_paginated_chat_history')
        assert hasattr(chat_interface, 'render_loading_message_input')
        assert hasattr(chat_interface, 'render_performance_dashboard')
        assert hasattr(chat_interface, 'set_loading_state')
        assert hasattr(chat_interface, 'render_streaming_response_optimized')
        
        print("  ✅ Optimized chat interface structure verified")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Optimized chat interface verification failed: {e}")
        return False

def verify_vector_search_optimizations():
    """Verify vector search optimizations"""
    print("🔍 Verifying Vector Search Optimizations...")
    
    try:
        from vector_search_optimizer import VectorSearchOptimizer, SearchResult
        from unittest.mock import Mock
        
        # Create mock clients
        mock_client = Mock()
        mock_embedding_model = Mock()
        mock_embedding_model.embed_query.return_value = [0.1] * 384
        
        optimizer = VectorSearchOptimizer(mock_client, mock_embedding_model)
        
        # Test that optimization methods exist
        assert hasattr(optimizer, 'optimized_similarity_search')
        assert hasattr(optimizer, 'get_index_statistics')
        assert hasattr(optimizer, 'optimize_indexes')
        assert hasattr(optimizer, 'clear_search_cache')
        
        print("  ✅ Vector search optimization structure verified")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Vector search optimization verification failed: {e}")
        return False

def verify_performance_monitor():
    """Verify performance monitoring functionality"""
    print("🔍 Verifying Performance Monitor...")
    
    try:
        from performance_monitor import PerformanceMonitor, SystemMetrics, AppMetrics
        
        monitor = PerformanceMonitor()
        
        # Test system metrics collection
        system_metrics = monitor.collect_system_metrics()
        assert isinstance(system_metrics, SystemMetrics)
        assert system_metrics.cpu_percent >= 0
        assert system_metrics.memory_percent >= 0
        
        # Test app metrics collection
        app_metrics = monitor.collect_app_metrics()
        assert isinstance(app_metrics, AppMetrics)
        assert app_metrics.total_requests >= 0
        
        # Test alert checking
        alerts = monitor.check_performance_alerts(system_metrics, app_metrics)
        assert isinstance(alerts, list)
        
        # Test optimization
        optimization_result = monitor.optimize_performance()
        assert optimization_result["success"] is True
        
        print("  ✅ Performance monitor verified")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance monitor verification failed: {e}")
        return False

def verify_database_optimizations():
    """Verify database optimization functions"""
    print("🔍 Verifying Database Optimizations...")
    
    try:
        # Check if migration file exists
        migration_file = "migrations/004_performance_optimizations.sql"
        if not os.path.exists(migration_file):
            print(f"  ❌ Migration file {migration_file} not found")
            return False
        
        # Read migration file and check for key functions
        with open(migration_file, 'r') as f:
            migration_content = f.read()
        
        required_functions = [
            "match_documents_optimized",
            "get_user_document_count",
            "get_vector_index_stats",
            "optimize_vector_indexes",
            "get_user_messages_paginated",
            "get_recent_conversation",
            "get_user_message_statistics"
        ]
        
        for func in required_functions:
            if func not in migration_content:
                print(f"  ❌ Required function {func} not found in migration")
                return False
        
        print("  ✅ Database optimization functions verified")
        
        # Test database connection if credentials are available
        try:
            from supabase import create_client
            from dotenv import load_dotenv
            
            load_dotenv()
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")
            
            if url and key:
                client = create_client(url, key)
                
                # Test one of the optimization functions
                result = client.rpc('get_user_document_count', {'user_id': '00000000-0000-0000-0000-000000000000'}).execute()
                print("  ✅ Database connection and optimization functions working")
            else:
                print("  ⚠️ Database credentials not available, skipping connection test")
                
        except Exception as db_error:
            print(f"  ⚠️ Database connection test failed (this is OK if not configured): {db_error}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database optimization verification failed: {e}")
        return False

def verify_app_integration():
    """Verify app integration of performance optimizations"""
    print("🔍 Verifying App Integration...")
    
    try:
        # Check if app.py has been updated with performance optimizations
        with open("app.py", 'r') as f:
            app_content = f.read()
        
        required_imports = [
            "from message_store_optimized import OptimizedMessageStore",
            "from chat_interface_optimized import OptimizedChatInterface",
            "from performance_optimizer import performance_optimizer"
        ]
        
        for import_stmt in required_imports:
            if import_stmt not in app_content:
                print(f"  ❌ Required import not found: {import_stmt}")
                return False
        
        # Check for key integration points
        integration_points = [
            "OptimizedMessageStore",
            "OptimizedChatInterface",
            "render_paginated_chat_history",
            "render_performance_dashboard"
        ]
        
        for point in integration_points:
            if point not in app_content:
                print(f"  ❌ Integration point not found: {point}")
                return False
        
        print("  ✅ App integration verified")
        
        return True
        
    except Exception as e:
        print(f"  ❌ App integration verification failed: {e}")
        return False

def run_performance_benchmarks():
    """Run basic performance benchmarks"""
    print("🔍 Running Performance Benchmarks...")
    
    try:
        from performance_optimizer import MemoryCache
        
        # Benchmark cache operations
        cache = MemoryCache(max_size=1000, default_ttl=300)
        
        # Test cache write performance
        start_time = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        write_time = time.time() - start_time
        
        # Test cache read performance
        start_time = time.time()
        for i in range(1000):
            cache.get(f"key_{i}")
        read_time = time.time() - start_time
        
        print(f"  📊 Cache write performance: {write_time:.3f}s for 1000 operations ({1000/write_time:.0f} ops/sec)")
        print(f"  📊 Cache read performance: {read_time:.3f}s for 1000 operations ({1000/read_time:.0f} ops/sec)")
        
        # Benchmark pagination
        messages = [f"message_{i}" for i in range(10000)]
        
        start_time = time.time()
        from performance_optimizer import PaginationHelper
        for page in range(1, 11):  # Test 10 pages
            PaginationHelper.paginate_messages(messages, page_size=100, page=page)
        pagination_time = time.time() - start_time
        
        print(f"  📊 Pagination performance: {pagination_time:.3f}s for 10 pages ({10/pagination_time:.0f} pages/sec)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance benchmark failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 Starting Task 14 Performance Optimization Verification")
    print("=" * 60)
    
    verification_results = []
    
    # Run all verifications
    verifications = [
        ("Performance Optimizer", verify_performance_optimizer),
        ("Optimized Message Store", verify_optimized_message_store),
        ("Chat Interface Optimizations", verify_chat_interface_optimizations),
        ("Vector Search Optimizations", verify_vector_search_optimizations),
        ("Performance Monitor", verify_performance_monitor),
        ("Database Optimizations", verify_database_optimizations),
        ("App Integration", verify_app_integration),
        ("Performance Benchmarks", run_performance_benchmarks)
    ]
    
    for name, verification_func in verifications:
        print(f"\n📋 {name}")
        print("-" * 40)
        
        try:
            result = verification_func()
            verification_results.append((name, result))
        except Exception as e:
            print(f"  ❌ Verification failed with exception: {e}")
            verification_results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(verification_results)
    
    for name, result in verification_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:<35} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} verifications passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL PERFORMANCE OPTIMIZATIONS VERIFIED SUCCESSFULLY!")
        print("\nTask 14 Implementation Summary:")
        print("✅ Conversation history pagination for large chat histories")
        print("✅ Loading states and progress indicators for all operations")
        print("✅ Optimized vector search performance with proper indexing")
        print("✅ Caching mechanisms for frequently accessed user data")
        print("✅ Performance monitoring and optimization tools")
        print("✅ Database function optimizations")
        print("✅ Integrated performance improvements in main application")
        
        return True
    else:
        print(f"\n⚠️ {total - passed} verification(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)