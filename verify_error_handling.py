"""
Verification script for comprehensive error handling implementation.
Tests all error handling features and fallback mechanisms.
"""

import sys
import traceback
import logging
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_error_handler_module():
    """Verify the error handler module is properly implemented"""
    print("🔍 Verifying error handler module...")
    
    try:
        from error_handler import (
            ErrorHandler, ErrorType, ErrorSeverity, ErrorInfo, RetryConfig,
            with_error_handling, get_error_handler
        )
        
        # Test basic functionality
        handler = ErrorHandler()
        assert handler is not None, "Error handler should initialize"
        
        # Test error handling
        error = Exception("Test error")
        error_info = handler.handle_error(error, ErrorType.AUTHENTICATION, "test")
        assert error_info.error_type == ErrorType.AUTHENTICATION, "Error type should match"
        assert error_info.user_message is not None, "User message should be provided"
        
        # Test retry configuration
        config = RetryConfig(max_attempts=3, base_delay=1.0)
        delay = handler.get_retry_delay(1, config)
        assert delay > 0, "Retry delay should be positive"
        
        print("✅ Error handler module verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handler module verification failed: {str(e)}")
        traceback.print_exc()
        return False

def verify_authentication_error_handling():
    """Verify authentication error handling"""
    print("🔍 Verifying authentication error handling...")
    
    try:
        # Mock Streamlit secrets and Supabase
        with patch('streamlit.secrets') as mock_secrets, \
             patch('auth_manager.create_client') as mock_create_client:
            
            # Setup mocks
            mock_secrets.__getitem__.side_effect = lambda key: {
                "SUPABASE_URL": "test_url",
                "SUPABASE_ANON_KEY": "test_key"
            }[key]
            
            mock_client = Mock()
            mock_create_client.return_value = mock_client
            mock_client.auth.get_session.return_value = None
            
            from auth_manager import AuthenticationManager
            
            # Test initialization
            auth_manager = AuthenticationManager()
            assert auth_manager.error_handler is not None, "Auth manager should have error handler"
            
            # Test sign in with network error (should retry)
            mock_client.auth.sign_in_with_password.side_effect = [
                Exception("Network error"),
                Mock(user=Mock(id="user123", email="test@test.com", user_metadata={}))
            ]
            
            result = auth_manager.sign_in("test@test.com", "password")
            assert result.success, "Sign in should succeed after retry"
            assert result.user_id == "user123", "User ID should be returned"
            
            # Test sign in with invalid credentials (should not retry)
            mock_client.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
            result = auth_manager.sign_in("test@test.com", "wrong_password")
            assert not result.success, "Sign in should fail with invalid credentials"
            assert "Invalid email or password" in result.error_message, "Should show user-friendly message"
            
        print("✅ Authentication error handling verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Authentication error handling verification failed: {str(e)}")
        traceback.print_exc()
        return False

def verify_model_manager_error_handling():
    """Verify model manager error handling"""
    print("🔍 Verifying model manager error handling...")
    
    try:
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}), \
             patch('model_manager.GroqLLM') as mock_groq:
            
            from model_manager import ModelManager, ModelTier
            
            # Test initialization
            manager = ModelManager()
            assert manager.error_handler is not None, "Model manager should have error handler"
            assert manager.retry_config is not None, "Model manager should have retry config"
            
            # Test model health tracking
            assert all(manager.model_health.values()), "All models should start healthy"
            
            # Test response generation with fallback
            mock_groq_instance = Mock()
            mock_groq.return_value = mock_groq_instance
            
            # Mock to fail multiple times then succeed (simulating retries within same tier)
            mock_groq_instance.generate_response.side_effect = [
                Exception("Rate limit exceeded"),  # First attempt fails
                Exception("Rate limit exceeded"),  # Second attempt fails  
                Exception("Rate limit exceeded"),  # Third attempt fails (max retries for fast)
                "Success response"  # Premium model succeeds
            ]
            
            messages = [{"role": "user", "content": "test"}]
            response = manager.generate_response(messages, ModelTier.FAST)
            
            assert response == "Success response", "Should get response from fallback model"
            assert mock_groq_instance.generate_response.call_count >= 3, "Should try multiple attempts"
            
        print("✅ Model manager error handling verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Model manager error handling verification failed: {str(e)}")
        traceback.print_exc()
        return False

def verify_database_error_handling():
    """Verify database error handling"""
    print("🔍 Verifying database error handling...")
    
    try:
        from database_utils import DatabaseUtils
        
        # Mock Supabase client
        mock_client = Mock()
        db_utils = DatabaseUtils(mock_client)
        
        assert db_utils.error_handler is not None, "Database utils should have error handler"
        assert db_utils.retry_config is not None, "Database utils should have retry config"
        
        # Test health check
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        mock_select = Mock()
        mock_table.select.return_value = mock_select
        mock_limit = Mock()
        mock_select.limit.return_value = mock_limit
        mock_limit.execute.return_value = Mock(data=[])
        
        health = db_utils.health_check()
        assert health, "Health check should pass with mocked client"
        
        # Test save message with retry
        mock_insert = Mock()
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.side_effect = [
            Exception("Connection timeout"),
            Mock(data=[{"id": "msg123", "content": "test"}])
        ]
        
        with patch.object(db_utils, '_check_connection_health', return_value=True):
            result = db_utils.save_message("user123", "user", "test message")
        
        assert result is not None, "Should get result after retry"
        assert result["id"] == "msg123", "Should return correct message data"
        
        print("✅ Database error handling verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Database error handling verification failed: {str(e)}")
        traceback.print_exc()
        return False

def verify_rag_orchestrator_error_handling():
    """Verify RAG orchestrator error handling"""
    print("🔍 Verifying RAG orchestrator error handling...")
    
    try:
        with patch('rag_orchestrator_optimized.VectorRetriever') as mock_retriever, \
             patch('rag_orchestrator_optimized.ContextBuilder') as mock_builder, \
             patch('rag_orchestrator_optimized.GroqLLM') as mock_llm:
            
            from rag_orchestrator_optimized import RAGOrchestrator
            
            # Test initialization
            orchestrator = RAGOrchestrator()
            assert orchestrator.error_handler is not None, "RAG orchestrator should have error handler"
            assert orchestrator.component_health is not None, "Should track component health"
            
            # Test document retrieval failure with fallback
            mock_retriever_instance = Mock()
            mock_retriever.return_value = mock_retriever_instance
            mock_retriever_instance.similarity_search.side_effect = Exception("Vector search failed")
            
            mock_builder_instance = Mock()
            mock_builder.return_value = mock_builder_instance
            mock_builder_instance.build_context.return_value = ""  # Empty context
            mock_builder_instance.get_context_stats.return_value = {"context_length": 0}
            
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance
            mock_llm_instance.generate_response.return_value = "Fallback response"
            
            response = orchestrator.process_query("test query", "user123")
            
            assert response.success, "Should succeed with fallback"
            assert "Fallback response" in response.response, "Should use fallback response"
            assert not orchestrator.component_health['vector_retriever'], "Should mark retriever as unhealthy"
            
            # Test complete failure with emergency fallback
            # Reset the mock to simulate complete failure then emergency success
            mock_retriever_instance.similarity_search.side_effect = Exception("Vector search failed")
            mock_builder_instance.build_context.side_effect = Exception("Context building failed")
            mock_llm_instance.generate_response.side_effect = [
                Exception("Generation failed"),  # First generation fails
                Exception("Generation failed"),  # Retry fails
                "Emergency response"  # Emergency fallback succeeds
            ]
            
            # Create a new orchestrator instance to reset component health
            orchestrator2 = RAGOrchestrator()
            response = orchestrator2.process_query("test query", "user123")
            assert response.success, "Should succeed with emergency fallback"
            assert "Emergency response" in response.response, "Should use emergency response"
            
        print("✅ RAG orchestrator error handling verification passed")
        return True
        
    except Exception as e:
        print(f"❌ RAG orchestrator error handling verification failed: {str(e)}")
        traceback.print_exc()
        return False

def verify_error_handling_decorator():
    """Verify error handling decorator"""
    print("🔍 Verifying error handling decorator...")
    
    try:
        from error_handler import with_error_handling, ErrorType, RetryConfig
        
        # Test retry functionality
        call_count = 0
        
        @with_error_handling(ErrorType.MODEL_API, "test_function", RetryConfig(max_attempts=3))
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "Success"
        
        result = test_function()
        assert result == "Success", "Should succeed after retries"
        assert call_count == 3, "Should retry correct number of times"
        
        # Test fallback functionality
        def fallback_function():
            return "Fallback result"
        
        @with_error_handling(ErrorType.MODEL_API, "test_fallback", fallback_func=fallback_function)
        def failing_function():
            raise Exception("Always fails")
        
        result = failing_function()
        assert result == "Fallback result", "Should use fallback function"
        
        print("✅ Error handling decorator verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling decorator verification failed: {str(e)}")
        traceback.print_exc()
        return False

def verify_integration():
    """Verify integration between components"""
    print("🔍 Verifying error handling integration...")
    
    try:
        from error_handler import get_error_handler, ErrorType
        
        # Test global error handler
        handler = get_error_handler()
        assert handler is not None, "Global error handler should be available"
        
        # Test error tracking across multiple calls
        for i in range(3):
            handler.handle_error(
                Exception(f"Test error {i}"),
                ErrorType.MODEL_API,
                "integration_test"
            )
        
        assert handler.error_counts["model_api_integration_test"] == 3, "Should track error counts"
        
        # Test should_retry logic
        should_retry = handler.should_retry(ErrorType.MODEL_API, "integration_test", max_retries=5)
        assert should_retry, "Should allow more retries"
        
        should_not_retry = handler.should_retry(ErrorType.MODEL_API, "integration_test", max_retries=2)
        assert not should_not_retry, "Should not allow more retries when limit exceeded"
        
        print("✅ Error handling integration verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling integration verification failed: {str(e)}")
        traceback.print_exc()
        return False

def run_comprehensive_verification():
    """Run comprehensive verification of all error handling features"""
    print("🚀 Starting comprehensive error handling verification...\n")
    
    verifications = [
        ("Error Handler Module", verify_error_handler_module),
        ("Authentication Error Handling", verify_authentication_error_handling),
        ("Model Manager Error Handling", verify_model_manager_error_handling),
        ("Database Error Handling", verify_database_error_handling),
        ("RAG Orchestrator Error Handling", verify_rag_orchestrator_error_handling),
        ("Error Handling Decorator", verify_error_handling_decorator),
        ("Integration", verify_integration)
    ]
    
    results = []
    
    for name, verification_func in verifications:
        print(f"\n{'='*50}")
        print(f"Testing: {name}")
        print('='*50)
        
        try:
            success = verification_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} verification failed with exception: {str(e)}")
            results.append((name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("VERIFICATION SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} verifications passed")
    
    if passed == total:
        print("🎉 All error handling verifications passed successfully!")
        print("\n📋 Implemented Features:")
        print("- Comprehensive error handling with user-friendly messages")
        print("- Retry mechanisms with exponential backoff")
        print("- Graceful degradation and fallback strategies")
        print("- Component health monitoring")
        print("- Database connection error handling")
        print("- Model API error handling with fallbacks")
        print("- RAG pipeline error handling with LLM-only fallback")
        print("- Authentication error handling with appropriate feedback")
        return True
    else:
        print(f"⚠️ {total - passed} verifications failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_verification()
    sys.exit(0 if success else 1)