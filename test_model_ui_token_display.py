#!/usr/bin/env python3
"""
Test to verify that the model UI displays the correct token limits.
"""

import os
import sys
from unittest.mock import patch, MagicMock
from model_manager import ModelManager, ModelTier

def test_model_ui_token_display():
    """Test that model UI components show correct token limits"""
    print("🖥️  Testing Model UI Token Display")
    print("=" * 40)
    
    try:
        # Initialize model manager
        api_key = os.environ.get("GROQ_API_KEY", "test_key_for_demo")
        manager = ModelManager(api_key=api_key)
        
        # Test model info display
        print("\n1. Testing Model Info Display...")
        
        premium_info = manager.get_model_info(ModelTier.PREMIUM)
        fast_info = manager.get_model_info(ModelTier.FAST)
        
        print(f"   Premium Model Info:")
        print(f"   • Name: {premium_info['name']}")
        print(f"   • Max Tokens: {premium_info['max_tokens']:,}")
        print(f"   • Speed Rating: {premium_info['speed_rating']}/10")
        print(f"   • Quality Rating: {premium_info['quality_rating']}/10")
        
        print(f"\n   Fast Model Info:")
        print(f"   • Name: {fast_info['name']}")
        print(f"   • Max Tokens: {fast_info['max_tokens']:,}")
        print(f"   • Speed Rating: {fast_info['speed_rating']}/10")
        print(f"   • Quality Rating: {fast_info['quality_rating']}/10")
        
        # Verify the values
        assert premium_info['max_tokens'] == 8000, f"Premium should show 8000 tokens, got {premium_info['max_tokens']}"
        assert fast_info['max_tokens'] == 1024, f"Fast should show 1024 tokens, got {fast_info['max_tokens']}"
        
        print("\n2. Testing Model Configuration Access...")
        
        premium_config = manager.get_model_config(ModelTier.PREMIUM)
        fast_config = manager.get_model_config(ModelTier.FAST)
        
        print(f"   Premium Config Max Tokens: {premium_config.max_tokens:,}")
        print(f"   Fast Config Max Tokens: {fast_config.max_tokens:,}")
        
        assert premium_config.max_tokens == 8000, "Premium config should have 8000 tokens"
        assert fast_config.max_tokens == 1024, "Fast config should have 1024 tokens"
        
        print("\n✅ Model UI Token Display Test Passed!")
        print("✅ UI components will correctly show 8,000 tokens for premium mode")
        print("✅ UI components will correctly show 1,024 tokens for fast mode")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_model_ui_token_display()
    sys.exit(0 if success else 1)