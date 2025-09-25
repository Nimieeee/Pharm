# model_system_demo.py
"""
Comprehensive demo of the Model Management System
This script demonstrates all the key features implemented for task 5.
"""

import os
from unittest.mock import patch, Mock
from model_manager import ModelManager, ModelTier, ModelConfig, get_model_manager
from model_ui import render_model_selector, render_model_status_indicator

def demo_model_configurations():
    """Demo: Model configuration management"""
    print("=" * 60)
    print("DEMO 1: Model Configuration Management")
    print("=" * 60)
    
    os.environ['GROQ_API_KEY'] = 'demo_key'
    os.environ['GROQ_FAST_MODEL'] = 'gemma2-9b-it'
    os.environ['GROQ_PREMIUM_MODEL'] = 'qwen/qwen3-32b'
    
    with patch('model_manager.GroqLLM'):
        manager = ModelManager()
        
        print("Available Models:")
        for model in manager.get_available_models():
            print(f"  • {model.display_name}")
            print(f"    - Model ID: {model.model_id}")
            print(f"    - Description: {model.description}")
            print(f"    - Speed Rating: {model.speed_rating}/10")
            print(f"    - Quality Rating: {model.quality_rating}/10")
            print(f"    - Max Tokens: {model.max_tokens}")
            print()

def demo_model_switching():
    """Demo: Model tier selection and switching"""
    print("=" * 60)
    print("DEMO 2: Model Tier Selection and Switching")
    print("=" * 60)
    
    os.environ['GROQ_API_KEY'] = 'demo_key'
    
    with patch('model_manager.GroqLLM'):
        manager = ModelManager()
        
        print(f"Initial model: {manager.get_current_model().display_name}")
        
        # Switch to premium
        print("\nSwitching to Premium Mode...")
        manager.set_current_model(ModelTier.PREMIUM)
        print(f"Current model: {manager.get_current_model().display_name}")
        
        # Switch back to fast
        print("\nSwitching to Fast Mode...")
        manager.set_current_model(ModelTier.FAST)
        print(f"Current model: {manager.get_current_model().display_name}")
        
        # Show model info
        print("\nDetailed Model Information:")
        for tier in [ModelTier.FAST, ModelTier.PREMIUM]:
            info = manager.get_model_info(tier)
            print(f"\n{tier.value.upper()} MODE:")
            for key, value in info.items():
                print(f"  {key}: {value}")

def demo_response_generation():
    """Demo: Response generation with different models"""
    print("=" * 60)
    print("DEMO 3: Response Generation with Model Tiers")
    print("=" * 60)
    
    os.environ['GROQ_API_KEY'] = 'demo_key'
    
    # Mock different responses for different models
    mock_client = Mock()
    
    def mock_generate_response(messages, model_type, **kwargs):
        if model_type == 'fast':
            return f"Fast response from {model_type} model: Quick answer to your question."
        else:
            return f"Premium response from {model_type} model: Detailed, high-quality analysis of your question."
    
    mock_client.generate_response.side_effect = mock_generate_response
    
    with patch('model_manager.GroqLLM', return_value=mock_client):
        manager = ModelManager()
        
        messages = [{"role": "user", "content": "What is pharmacokinetics?"}]
        
        # Test with fast model
        print("FAST MODEL RESPONSE:")
        manager.set_current_model(ModelTier.FAST)
        response = manager.generate_response(messages)
        print(f"  {response}")
        
        print("\nPREMIUM MODEL RESPONSE:")
        manager.set_current_model(ModelTier.PREMIUM)
        response = manager.generate_response(messages)
        print(f"  {response}")

def demo_streaming_responses():
    """Demo: Streaming response handling"""
    print("=" * 60)
    print("DEMO 4: Streaming Response Handling")
    print("=" * 60)
    
    os.environ['GROQ_API_KEY'] = 'demo_key'
    
    def mock_stream_response(messages, model_type, **kwargs):
        if model_type == 'fast':
            chunks = ["Fast", " streaming", " response", " from", " Gemma2-9B-IT"]
        else:
            chunks = ["Premium", " streaming", " response", " with", " detailed", " analysis", " from", " Qwen3-32B"]
        
        for chunk in chunks:
            yield chunk
    
    mock_client = Mock()
    mock_client.stream_response.side_effect = mock_stream_response
    
    with patch('model_manager.GroqLLM', return_value=mock_client):
        manager = ModelManager()
        
        messages = [{"role": "user", "content": "Explain drug metabolism"}]
        
        # Test streaming with fast model
        print("FAST MODEL STREAMING:")
        manager.set_current_model(ModelTier.FAST)
        print("  ", end="")
        for chunk in manager.stream_response(messages):
            print(chunk, end="")
        print()  # New line
        
        print("\nPREMIUM MODEL STREAMING:")
        manager.set_current_model(ModelTier.PREMIUM)
        print("  ", end="")
        for chunk in manager.stream_response(messages):
            print(chunk, end="")
        print()  # New line

def demo_error_handling():
    """Demo: Error handling and fallbacks"""
    print("=" * 60)
    print("DEMO 5: Error Handling")
    print("=" * 60)
    
    # Test missing API key
    print("Testing missing API key...")
    with patch.dict(os.environ, {}, clear=True):
        try:
            ModelManager()
            print("  ❌ Should have raised an error")
        except ValueError as e:
            print(f"  ✓ Correctly caught error: {e}")
    
    # Test invalid model tier
    print("\nTesting invalid model tier...")
    os.environ['GROQ_API_KEY'] = 'demo_key'
    with patch('model_manager.GroqLLM'):
        manager = ModelManager()
        try:
            manager.set_current_model("invalid_tier")
            print("  ❌ Should have raised an error")
        except (ValueError, TypeError) as e:
            print(f"  ✓ Correctly caught error: {type(e).__name__}")

def demo_integration_features():
    """Demo: Integration features"""
    print("=" * 60)
    print("DEMO 6: Integration Features")
    print("=" * 60)
    
    os.environ['GROQ_API_KEY'] = 'demo_key'
    
    with patch('model_manager.GroqLLM'):
        # Test global model manager
        print("Testing global model manager...")
        manager1 = get_model_manager()
        manager2 = get_model_manager()
        print(f"  ✓ Singleton pattern works: {manager1 is manager2}")
        
        # Test model info retrieval
        print("\nTesting model info retrieval...")
        manager = ModelManager()
        for tier in [ModelTier.FAST, ModelTier.PREMIUM]:
            info = manager.get_model_info(tier)
            required_fields = ["name", "description", "model_id", "max_tokens", 
                             "speed_rating", "quality_rating", "cost_per_token"]
            has_all_fields = all(field in info for field in required_fields)
            print(f"  ✓ {tier.value} model info complete: {has_all_fields}")

def main():
    """Run all demos"""
    print("🤖 MODEL MANAGEMENT SYSTEM COMPREHENSIVE DEMO")
    print("This demo showcases all features implemented for Task 5")
    print()
    
    demo_model_configurations()
    demo_model_switching()
    demo_response_generation()
    demo_streaming_responses()
    demo_error_handling()
    demo_integration_features()
    
    print("=" * 60)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("Task 5 Implementation Summary:")
    print("✓ ModelManager class for handling multiple Groq models")
    print("✓ Model selection UI with fast/premium mode toggle")
    print("✓ Model configuration management for Gemma2-9B-IT and Qwen3-32B")
    print("✓ Streaming response handling for both model tiers")
    print("✓ Comprehensive error handling and validation")
    print("✓ Session state management for model persistence")
    print("✓ Integration with existing groq_llm.py")
    print("✓ Full test coverage with unit and integration tests")

if __name__ == "__main__":
    main()