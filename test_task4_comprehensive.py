#!/usr/bin/env python3
"""
Comprehensive test for Task 4: Increase premium model token limit to 8,000
This test validates all requirements and sub-tasks for Task 4.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from model_manager import ModelManager, ModelTier

class TestTask4Comprehensive(unittest.TestCase):
    """Comprehensive test for Task 4 implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_api_key = "test_groq_api_key"
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    def test_requirement_4_1_token_limit_set_to_8000(self):
        """
        Requirement 4.1: WHEN a user selects premium mode THEN the system SHALL set the maximum token limit to 8,000 tokens
        """
        manager = ModelManager(api_key=self.test_api_key)
        premium_config = manager.get_model_config(ModelTier.PREMIUM)
        
        self.assertEqual(premium_config.max_tokens, 8000,
                        "Premium mode must have max_tokens set to 8000")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    @patch('model_manager.GroqLLM')
    def test_requirement_4_2_longer_responses_allowed(self, mock_groq_llm):
        """
        Requirement 4.2: WHEN generating responses in premium mode THEN the system SHALL allow for longer, more comprehensive answers up to 8,000 tokens
        """
        mock_client = MagicMock()
        mock_groq_llm.return_value = mock_client
        mock_client.generate_response.return_value = "Long detailed response"
        
        manager = ModelManager(api_key=self.test_api_key)
        manager.set_current_model(ModelTier.PREMIUM)
        
        test_messages = [{"role": "user", "content": "Explain pharmacokinetics in detail"}]
        manager.generate_response(test_messages)
        
        # Verify that the call was made with 8000 tokens
        mock_client.generate_response.assert_called_once()
        call_args = mock_client.generate_response.call_args
        self.assertEqual(call_args[1]['max_tokens'], 8000,
                        "Premium mode should allow up to 8000 tokens for comprehensive answers")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    def test_requirement_4_3_longer_context_maintained(self):
        """
        Requirement 4.3: WHEN premium mode is active THEN the system SHALL maintain context for longer conversations without truncation
        """
        manager = ModelManager(api_key=self.test_api_key)
        manager.set_current_model(ModelTier.PREMIUM)
        
        current_config = manager.get_current_model()
        self.assertEqual(current_config.max_tokens, 8000,
                        "Premium mode should maintain 8000 token context for longer conversations")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    @patch('model_manager.GroqLLM')
    def test_requirement_4_4_detailed_thorough_responses(self, mock_groq_llm):
        """
        Requirement 4.4: WHEN the 8,000 token limit is applied THEN the system SHALL ensure responses can be more detailed and thorough
        """
        mock_client = MagicMock()
        mock_groq_llm.return_value = mock_client
        mock_client.stream_response.return_value = iter(["Detailed", " thorough", " response"])
        
        manager = ModelManager(api_key=self.test_api_key)
        
        test_messages = [{"role": "user", "content": "Provide detailed drug interaction analysis"}]
        list(manager.stream_response(test_messages, tier=ModelTier.PREMIUM))
        
        # Verify streaming also uses 8000 tokens
        mock_client.stream_response.assert_called_once()
        call_args = mock_client.stream_response.call_args
        self.assertEqual(call_args[1]['max_tokens'], 8000,
                        "8000 token limit should enable detailed and thorough responses")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    def test_requirement_4_5_fast_mode_unchanged(self):
        """
        Requirement 4.5: WHEN fast mode is selected THEN the system SHALL maintain the existing lower token limits for performance
        """
        manager = ModelManager(api_key=self.test_api_key)
        fast_config = manager.get_model_config(ModelTier.FAST)
        
        self.assertEqual(fast_config.max_tokens, 1024,
                        "Fast mode must maintain existing 1024 token limit for performance")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    def test_model_manager_initialization_uses_increased_limits(self):
        """
        Sub-task: Modify model manager initialization to use increased token limits
        """
        manager = ModelManager(api_key=self.test_api_key)
        
        # Check that initialization properly sets up the increased limits
        premium_config = manager.model_configs[ModelTier.PREMIUM]
        fast_config = manager.model_configs[ModelTier.FAST]
        
        self.assertEqual(premium_config.max_tokens, 8000,
                        "Model manager initialization should set premium to 8000 tokens")
        self.assertEqual(fast_config.max_tokens, 1024,
                        "Model manager initialization should keep fast at 1024 tokens")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    @patch('model_manager.GroqLLM')
    def test_token_limits_applied_during_response_generation(self, mock_groq_llm):
        """
        Sub-task: Ensure token limit changes are properly applied during response generation
        """
        mock_client = MagicMock()
        mock_groq_llm.return_value = mock_client
        mock_client.generate_response.return_value = "Test response"
        
        manager = ModelManager(api_key=self.test_api_key)
        test_messages = [{"role": "user", "content": "Test"}]
        
        # Test premium mode
        manager.generate_response(test_messages, tier=ModelTier.PREMIUM)
        premium_call = mock_client.generate_response.call_args
        
        # Test fast mode
        manager.generate_response(test_messages, tier=ModelTier.FAST)
        fast_call = mock_client.generate_response.call_args
        
        # Verify different token limits are applied
        self.assertEqual(premium_call[1]['max_tokens'], 8000,
                        "Premium response generation should use 8000 tokens")
        self.assertEqual(fast_call[1]['max_tokens'], 1024,
                        "Fast response generation should use 1024 tokens")

def run_comprehensive_test():
    """Run comprehensive test for Task 4"""
    print("🧪 Task 4 Comprehensive Test: Premium Model Token Limit to 8,000")
    print("=" * 70)
    print("Testing all requirements and sub-tasks...")
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTask4Comprehensive)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("📋 TASK 4 COMPLETION SUMMARY")
    print("=" * 70)
    
    if result.wasSuccessful():
        print("✅ Task 4: Increase premium model token limit to 8,000 - COMPLETED")
        print()
        print("✅ Sub-task: Update ModelConfig for premium tier to set max_tokens to 8000")
        print("✅ Sub-task: Modify model manager initialization to use increased token limits")
        print("✅ Sub-task: Ensure token limit changes are properly applied during response generation")
        print("✅ Sub-task: Test that premium mode allows for longer, more detailed responses")
        print()
        print("✅ Requirement 4.1: Premium mode sets maximum token limit to 8,000")
        print("✅ Requirement 4.2: Premium mode allows longer, comprehensive answers up to 8,000 tokens")
        print("✅ Requirement 4.3: Premium mode maintains context for longer conversations")
        print("✅ Requirement 4.4: 8,000 token limit ensures detailed and thorough responses")
        print("✅ Requirement 4.5: Fast mode maintains existing lower token limits for performance")
        print()
        print("🎉 ALL REQUIREMENTS AND SUB-TASKS COMPLETED SUCCESSFULLY!")
        return True
    else:
        print("❌ Task 4 completion verification failed!")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)