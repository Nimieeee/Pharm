# test_model_streaming.py
"""
Test streaming functionality of the ModelManager
"""
import os
from unittest.mock import patch, Mock
from model_manager import ModelManager, ModelTier

def test_streaming_integration():
    """Test that streaming works with both model tiers"""
    
    # Set up environment
    os.environ['GROQ_API_KEY'] = 'test_key'
    
    # Mock the GroqLLM client
    mock_client = Mock()
    mock_client.stream_response.return_value = iter(['Hello', ' world', '!'])
    
    with patch('model_manager.GroqLLM', return_value=mock_client):
        manager = ModelManager()
        
        messages = [{"role": "user", "content": "Hello"}]
        
        # Test fast model streaming
        manager.set_current_model(ModelTier.FAST)
        chunks = list(manager.stream_response(messages))
        assert chunks == ['Hello', ' world', '!']
        print("✓ Fast model streaming works")
        
        # Test premium model streaming
        mock_client.stream_response.return_value = iter(['Hello', ' world', '!'])  # Reset iterator
        manager.set_current_model(ModelTier.PREMIUM)
        chunks = list(manager.stream_response(messages))
        assert chunks == ['Hello', ' world', '!']
        print("✓ Premium model streaming works")
        
        # Verify the correct model types were used
        calls = mock_client.stream_response.call_args_list
        assert len(calls) == 2
        
        # Check that different model types were used
        fast_call = calls[0]
        premium_call = calls[1]
        
        assert fast_call[1]['model_type'] == 'fast'
        assert premium_call[1]['model_type'] == 'premium'
        print("✓ Correct model types used for streaming")

def test_response_generation():
    """Test that response generation works with both model tiers"""
    
    os.environ['GROQ_API_KEY'] = 'test_key'
    
    mock_client = Mock()
    mock_client.generate_response.return_value = "Test response"
    
    with patch('model_manager.GroqLLM', return_value=mock_client):
        manager = ModelManager()
        
        messages = [{"role": "user", "content": "Hello"}]
        
        # Test fast model
        manager.set_current_model(ModelTier.FAST)
        response = manager.generate_response(messages)
        assert response == "Test response"
        print("✓ Fast model response generation works")
        
        # Test premium model
        manager.set_current_model(ModelTier.PREMIUM)
        response = manager.generate_response(messages)
        assert response == "Test response"
        print("✓ Premium model response generation works")

if __name__ == "__main__":
    print("Testing model streaming functionality...")
    test_streaming_integration()
    test_response_generation()
    print("✓ All streaming tests passed!")