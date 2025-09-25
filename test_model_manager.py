# test_model_manager.py
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from model_manager import ModelManager, ModelTier, ModelConfig
import streamlit as st

class TestModelManager:
    """Test suite for ModelManager class"""
    
    def setup_method(self):
        """Set up test environment"""
        # Mock environment variables
        self.env_vars = {
            "GROQ_API_KEY": "test_api_key",
            "GROQ_FAST_MODEL": "gemma2-9b-it",
            "GROQ_PREMIUM_MODEL": "qwen/qwen3-32b"
        }
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_api_key"})
    @patch('model_manager.GroqLLM')
    def test_model_manager_initialization(self, mock_groq_llm):
        """Test ModelManager initialization"""
        manager = ModelManager()
        
        assert manager.api_key == "test_api_key"
        assert manager.current_model_tier == ModelTier.FAST
        assert len(manager.model_configs) == 2
        assert ModelTier.FAST in manager.model_configs
        assert ModelTier.PREMIUM in manager.model_configs
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_api_key"})
    @patch('model_manager.GroqLLM')
    def test_get_available_models(self, mock_groq_llm):
        """Test getting available models"""
        manager = ModelManager()
        models = manager.get_available_models()
        
        assert len(models) == 2
        assert all(isinstance(model, ModelConfig) for model in models)
        
        # Check that we have both tiers
        tiers = [model.tier for model in models]
        assert ModelTier.FAST in tiers
        assert ModelTier.PREMIUM in tiers
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_api_key"})
    @patch('model_manager.GroqLLM')
    def test_model_config_properties(self, mock_groq_llm):
        """Test model configuration properties"""
        manager = ModelManager()
        
        fast_config = manager.get_model_config(ModelTier.FAST)
        premium_config = manager.get_model_config(ModelTier.PREMIUM)
        
        # Test fast model config
        assert fast_config.name == "fast"
        assert fast_config.tier == ModelTier.FAST
        assert fast_config.speed_rating > fast_config.quality_rating
        assert "gemma2-9b-it" in fast_config.model_id.lower()
        
        # Test premium model config
        assert premium_config.name == "premium"
        assert premium_config.tier == ModelTier.PREMIUM
        assert premium_config.quality_rating > premium_config.speed_rating
        assert "qwen" in premium_config.model_id.lower()
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_api_key"})
    @patch('model_manager.GroqLLM')
    def test_set_current_model(self, mock_groq_llm):
        """Test setting current model"""
        manager = ModelManager()
        
        # Initially should be FAST
        assert manager.current_model_tier == ModelTier.FAST
        
        # Change to PREMIUM
        manager.set_current_model(ModelTier.PREMIUM)
        assert manager.current_model_tier == ModelTier.PREMIUM
        
        # Change back to FAST
        manager.set_current_model(ModelTier.FAST)
        assert manager.current_model_tier == ModelTier.FAST
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_api_key"})
    @patch('model_manager.GroqLLM')
    def test_generate_response(self, mock_groq_llm):
        """Test response generation"""
        # Mock the GroqLLM instance
        mock_client = Mock()
        mock_client.generate_response.return_value = "Test response"
        mock_groq_llm.return_value = mock_client
        
        manager = ModelManager()
        messages = [{"role": "user", "content": "Hello"}]
        
        # Test with default (fast) model
        response = manager.generate_response(messages)
        assert response == "Test response"
        mock_client.generate_response.assert_called_once()
        
        # Test with premium model
        mock_client.reset_mock()
        response = manager.generate_response(messages, tier=ModelTier.PREMIUM)
        assert response == "Test response"
        mock_client.generate_response.assert_called_once()
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_api_key"})
    @patch('model_manager.GroqLLM')
    def test_stream_response(self, mock_groq_llm):
        """Test streaming response"""
        # Mock the GroqLLM instance
        mock_client = Mock()
        mock_client.stream_response.return_value = iter(["chunk1", "chunk2", "chunk3"])
        mock_groq_llm.return_value = mock_client
        
        manager = ModelManager()
        messages = [{"role": "user", "content": "Hello"}]
        
        # Test streaming
        chunks = list(manager.stream_response(messages))
        assert chunks == ["chunk1", "chunk2", "chunk3"]
        mock_client.stream_response.assert_called_once()
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_api_key"})
    @patch('model_manager.GroqLLM')
    def test_get_model_info(self, mock_groq_llm):
        """Test getting model information"""
        manager = ModelManager()
        
        fast_info = manager.get_model_info(ModelTier.FAST)
        premium_info = manager.get_model_info(ModelTier.PREMIUM)
        
        # Check required fields
        required_fields = ["name", "description", "model_id", "max_tokens", 
                          "speed_rating", "quality_rating", "cost_per_token"]
        
        for field in required_fields:
            assert field in fast_info
            assert field in premium_info
        
        # Check that premium has higher quality rating
        assert premium_info["quality_rating"] > fast_info["quality_rating"]
        # Check that fast has higher speed rating
        assert fast_info["speed_rating"] > premium_info["speed_rating"]
    
    def test_missing_api_key(self):
        """Test error handling when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY must be provided"):
                ModelManager()
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_api_key"})
    @patch('model_manager.GroqLLM')
    def test_invalid_model_tier(self, mock_groq_llm):
        """Test error handling for invalid model tier"""
        manager = ModelManager()
        
        with pytest.raises(ValueError, match="Invalid model tier"):
            manager.set_current_model("invalid_tier")

class MockSessionState:
    """Mock class for Streamlit session state"""
    def __init__(self):
        self._data = {}
    
    def __contains__(self, key):
        return key in self._data
    
    def __getattr__(self, key):
        return self._data.get(key)
    
    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            if not hasattr(self, '_data'):
                super().__setattr__('_data', {})
            self._data[key] = value

class TestModelUI:
    """Test suite for model UI components"""
    
    def test_session_state_management(self):
        """Test session state management functions"""
        # Mock streamlit session state
        mock_session_state = MockSessionState()
        
        with patch('model_manager.st.session_state', mock_session_state):
            from model_manager import get_session_model_tier, set_session_model_tier
            
            # Test default value
            tier = get_session_model_tier()
            assert tier == ModelTier.FAST
            
            # Test setting value
            set_session_model_tier(ModelTier.PREMIUM)
            tier = get_session_model_tier()
            assert tier == ModelTier.PREMIUM

def test_model_manager_integration():
    """Integration test for model manager with actual environment"""
    # Skip if no API key available
    if not os.environ.get("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not available for integration test")
    
    try:
        manager = ModelManager()
        
        # Test basic functionality
        models = manager.get_available_models()
        assert len(models) > 0
        
        current_model = manager.get_current_model()
        assert current_model is not None
        
        # Test model switching
        manager.set_current_model(ModelTier.PREMIUM)
        assert manager.current_model_tier == ModelTier.PREMIUM
        
        manager.set_current_model(ModelTier.FAST)
        assert manager.current_model_tier == ModelTier.FAST
        
    except Exception as e:
        pytest.fail(f"Integration test failed: {str(e)}")

if __name__ == "__main__":
    # Run basic tests
    print("Running ModelManager tests...")
    
    # Test with mock environment
    with patch.dict(os.environ, {"GROQ_API_KEY": "test_key"}):
        with patch('model_manager.GroqLLM'):
            manager = ModelManager()
            print(f"✓ ModelManager initialized with {len(manager.get_available_models())} models")
            
            # Test model switching
            manager.set_current_model(ModelTier.PREMIUM)
            print(f"✓ Switched to {manager.get_current_model().display_name}")
            
            manager.set_current_model(ModelTier.FAST)
            print(f"✓ Switched to {manager.get_current_model().display_name}")
            
            print("✓ All basic tests passed!")