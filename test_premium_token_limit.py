#!/usr/bin/env python3
"""
Test script to verify that the premium model token limit has been increased to 8,000.
This test validates requirement 4.1, 4.2, 4.3, 4.4, and 4.5.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from model_manager import ModelManager, ModelTier, ModelConfig

class TestPremiumTokenLimit(unittest.TestCase):
    """Test cases for premium model token limit increase"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock the API key for testing
        self.test_api_key = "test_groq_api_key"
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    def test_premium_model_config_has_8000_tokens(self):
        """Test that premium model configuration has max_tokens set to 8000"""
        # Requirement 4.1: WHEN a user selects premium mode THEN the system SHALL set the maximum token limit to 8,000 tokens
        manager = ModelManager(api_key=self.test_api_key)
        
        premium_config = manager.get_model_config(ModelTier.PREMIUM)
        
        self.assertEqual(premium_config.max_tokens, 8000, 
                        "Premium model should have max_tokens set to 8000")
        self.assertEqual(premium_config.tier, ModelTier.PREMIUM,
                        "Config should be for premium tier")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    def test_fast_model_config_unchanged(self):
        """Test that fast model configuration remains unchanged at 1024 tokens"""
        # Requirement 4.5: WHEN fast mode is selected THEN the system SHALL maintain the existing lower token limits for performance
        manager = ModelManager(api_key=self.test_api_key)
        
        fast_config = manager.get_model_config(ModelTier.FAST)
        
        self.assertEqual(fast_config.max_tokens, 1024,
                        "Fast model should maintain 1024 token limit")
        self.assertEqual(fast_config.tier, ModelTier.FAST,
                        "Config should be for fast tier")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    def test_model_info_reflects_8000_tokens(self):
        """Test that get_model_info returns 8000 tokens for premium model"""
        # Requirement 4.2: WHEN generating responses in premium mode THEN the system SHALL allow for longer, more comprehensive answers up to 8,000 tokens
        manager = ModelManager(api_key=self.test_api_key)
        
        premium_info = manager.get_model_info(ModelTier.PREMIUM)
        
        self.assertEqual(premium_info['max_tokens'], 8000,
                        "Premium model info should show 8000 max tokens")
        self.assertIn('Premium', premium_info['name'],
                     "Should be premium model info")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    @patch('model_manager.GroqLLM')
    def test_generate_response_uses_8000_tokens_for_premium(self, mock_groq_llm):
        """Test that generate_response passes 8000 tokens when using premium model"""
        # Requirement 4.3: WHEN premium mode is active THEN the system SHALL maintain context for longer conversations without truncation
        mock_client = MagicMock()
        mock_groq_llm.return_value = mock_client
        mock_client.generate_response.return_value = "Test response"
        
        manager = ModelManager(api_key=self.test_api_key)
        
        # Test with premium tier
        test_messages = [{"role": "user", "content": "Test message"}]
        manager.generate_response(test_messages, tier=ModelTier.PREMIUM)
        
        # Verify that the GroqLLM was called with max_tokens=8000
        mock_client.generate_response.assert_called_once()
        call_args = mock_client.generate_response.call_args
        self.assertEqual(call_args[1]['max_tokens'], 8000,
                        "Premium model should be called with max_tokens=8000")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    @patch('model_manager.GroqLLM')
    def test_stream_response_uses_8000_tokens_for_premium(self, mock_groq_llm):
        """Test that stream_response passes 8000 tokens when using premium model"""
        # Requirement 4.4: WHEN the 8,000 token limit is applied THEN the system SHALL ensure responses can be more detailed and thorough
        mock_client = MagicMock()
        mock_groq_llm.return_value = mock_client
        mock_client.stream_response.return_value = iter(["Test", " response"])
        
        manager = ModelManager(api_key=self.test_api_key)
        
        # Test with premium tier
        test_messages = [{"role": "user", "content": "Test message"}]
        list(manager.stream_response(test_messages, tier=ModelTier.PREMIUM))
        
        # Verify that the GroqLLM was called with max_tokens=8000
        mock_client.stream_response.assert_called_once()
        call_args = mock_client.stream_response.call_args
        self.assertEqual(call_args[1]['max_tokens'], 8000,
                        "Premium model streaming should be called with max_tokens=8000")
        
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test_groq_api_key'})
    @patch('model_manager.GroqLLM')
    def test_custom_max_tokens_override_works(self, mock_groq_llm):
        """Test that custom max_tokens parameter can still override the default"""
        mock_client = MagicMock()
        mock_groq_llm.return_value = mock_client
        mock_client.generate_response.return_value = "Test response"
        
        manager = ModelManager(api_key=self.test_api_key)
        
        # Test with custom max_tokens override
        test_messages = [{"role": "user", "content": "Test message"}]
        custom_tokens = 4000
        manager.generate_response(test_messages, tier=ModelTier.PREMIUM, max_tokens=custom_tokens)
        
        # Verify that the custom max_tokens was used
        mock_client.generate_response.assert_called_once()
        call_args = mock_client.generate_response.call_args
        self.assertEqual(call_args[1]['max_tokens'], custom_tokens,
                        f"Custom max_tokens={custom_tokens} should override default")

def run_tests():
    """Run all token limit tests"""
    print("🧪 Testing Premium Model Token Limit Increase to 8,000...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPremiumTokenLimit)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All token limit tests passed!")
        print("✅ Premium model now supports 8,000 tokens")
        print("✅ Fast model maintains 1,024 tokens for performance")
        print("✅ Token limits are properly applied during response generation")
        return True
    else:
        print("❌ Some tests failed!")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)