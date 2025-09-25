#!/usr/bin/env python3
"""
Test Model Switching and Preference Persistence
Tests the implementation of task 11: model switching with persistence
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_manager import ModelManager, ModelTier, get_session_model_tier, set_session_model_tier
from session_manager import SessionManager, UserSession
from model_ui import render_model_selector, render_model_settings_sidebar, render_header_model_indicator


class TestModelSwitching:
    """Test model switching functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Clear session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()
        
        # Mock session state
        self.mock_session_state = {}
        
    def test_get_session_model_tier_default(self):
        """Test getting default model tier"""
        with patch.object(st, 'session_state', self.mock_session_state):
            tier = get_session_model_tier()
            assert tier == ModelTier.FAST
    
    def test_get_session_model_tier_premium(self):
        """Test getting premium model tier from session"""
        self.mock_session_state['model_preference'] = 'premium'
        
        with patch.object(st, 'session_state', self.mock_session_state):
            tier = get_session_model_tier()
            assert tier == ModelTier.PREMIUM
    
    def test_set_session_model_tier(self):
        """Test setting model tier in session"""
        # Mock session manager to avoid database calls
        mock_session_manager = Mock()
        self.mock_session_state['session_manager'] = mock_session_manager
        
        with patch.object(st, 'session_state', self.mock_session_state):
            set_session_model_tier(ModelTier.PREMIUM)
            assert self.mock_session_state['model_preference'] == 'premium'
            
            set_session_model_tier(ModelTier.FAST)
            assert self.mock_session_state['model_preference'] == 'fast'
    
    def test_model_manager_tier_switching(self):
        """Test ModelManager tier switching"""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            manager = ModelManager()
            
            # Test default tier
            assert manager.current_model_tier == ModelTier.FAST
            
            # Test switching to premium
            manager.set_current_model(ModelTier.PREMIUM)
            assert manager.current_model_tier == ModelTier.PREMIUM
            
            # Test getting current config
            config = manager.get_current_model()
            assert config.tier == ModelTier.PREMIUM
    
    def test_model_config_properties(self):
        """Test model configuration properties"""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            manager = ModelManager()
            
            fast_config = manager.get_model_config(ModelTier.FAST)
            premium_config = manager.get_model_config(ModelTier.PREMIUM)
            
            # Test fast model properties
            assert fast_config.tier == ModelTier.FAST
            assert fast_config.speed_rating > premium_config.speed_rating
            assert fast_config.max_tokens < premium_config.max_tokens
            
            # Test premium model properties
            assert premium_config.tier == ModelTier.PREMIUM
            assert premium_config.quality_rating > fast_config.quality_rating


class TestSessionPersistence:
    """Test session persistence functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_auth_manager = Mock()
        self.mock_session_state = {}
    
    def test_session_manager_model_preference_update(self):
        """Test updating model preference in session manager"""
        # Create a proper mock session state that behaves like a dict
        mock_session_state = MagicMock()
        mock_session_state.__getitem__ = lambda self, key: self.__dict__.get(key)
        mock_session_state.__setitem__ = lambda self, key, value: setattr(self, key, value)
        mock_session_state.__contains__ = lambda self, key: hasattr(self, key)
        mock_session_state.get = lambda key, default=None: getattr(mock_session_state, key, default)
        
        with patch.object(st, 'session_state', mock_session_state):
            session_manager = SessionManager(self.mock_auth_manager)
            
            # Initialize a user session
            user_session = UserSession(
                user_id="test_user",
                email="test@example.com",
                preferences={},
                model_preference="fast",
                is_authenticated=True
            )
            mock_session_state.user_session = user_session
            
            # Test updating model preference
            with patch.object(session_manager, '_persist_user_preferences', return_value=True):
                session_manager.update_model_preference('premium')
                
                assert mock_session_state.model_preference == 'premium'
                assert mock_session_state.user_session.model_preference == 'premium'
    
    def test_session_initialization_with_preferences(self):
        """Test session initialization loads preferences"""
        # Create a proper mock session state
        mock_session_state = MagicMock()
        mock_session_state.__getitem__ = lambda self, key: getattr(self, key)
        mock_session_state.__setitem__ = lambda self, key, value: setattr(self, key, value)
        mock_session_state.__contains__ = lambda self, key: hasattr(self, key)
        mock_session_state.get = lambda key, default=None: getattr(mock_session_state, key, default)
        
        with patch.object(st, 'session_state', mock_session_state):
            session_manager = SessionManager(self.mock_auth_manager)
            
            # Mock loading preferences from database
            with patch.object(session_manager, 'load_user_preferences', 
                            return_value={'model_preference': 'premium', 'theme': 'dark'}):
                
                session_manager.initialize_session("test_user", "test@example.com")
                
                assert mock_session_state.model_preference == 'premium'
                assert mock_session_state.theme == 'dark'
    
    def test_preference_persistence_to_database(self):
        """Test preference persistence to database"""
        # Create a proper mock session state
        mock_session_state = MagicMock()
        mock_session_state.__getitem__ = lambda self, key: getattr(self, key)
        mock_session_state.__setitem__ = lambda self, key, value: setattr(self, key, value)
        mock_session_state.__contains__ = lambda self, key: hasattr(self, key)
        mock_session_state.get = lambda key, default=None: getattr(mock_session_state, key, default)
        
        with patch.object(st, 'session_state', mock_session_state):
            session_manager = SessionManager(self.mock_auth_manager)
            
            # Setup authenticated session
            user_session = UserSession(
                user_id="test_user",
                email="test@example.com",
                preferences={},
                model_preference="fast",
                is_authenticated=True
            )
            mock_session_state.user_session = user_session
            
            # Mock auth manager and database client
            mock_user = Mock()
            mock_user.id = "test_user"
            self.mock_auth_manager.get_current_user.return_value = mock_user
            
            mock_db_client = Mock()
            mock_table = Mock()
            mock_db_client.table.return_value = mock_table
            mock_table.update.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[{'preferences': {'model_preference': 'premium'}}])
            
            with patch('session_manager.get_database_client', return_value=mock_db_client):
                result = session_manager._persist_user_preferences()
                
                assert result == True
                mock_table.update.assert_called_once()


class TestModelUI:
    """Test model UI components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_session_state = {'model_preference': 'fast'}
        
    def test_header_model_indicator(self):
        """Test header model indicator"""
        with patch.object(st, 'session_state', self.mock_session_state):
            # Test fast mode indicator
            indicator = render_header_model_indicator()
            assert "🚀" in indicator
            assert "Fast" in indicator
            
            # Test premium mode indicator
            self.mock_session_state['model_preference'] = 'premium'
            indicator = render_header_model_indicator()
            assert "⭐" in indicator
            assert "Premium" in indicator
    
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.radio')
    def test_model_selector_rendering(self, mock_radio, mock_columns, mock_markdown):
        """Test model selector rendering"""
        with patch.object(st, 'session_state', self.mock_session_state):
            mock_columns.return_value = [Mock(), Mock(), Mock()]
            mock_radio.return_value = "⚡ Fast Mode"
            
            with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
                manager = ModelManager()
                
                # Mock the context manager for columns
                mock_col = Mock()
                mock_col.__enter__ = Mock(return_value=mock_col)
                mock_col.__exit__ = Mock(return_value=None)
                mock_columns.return_value = [mock_col, mock_col, mock_col]
                
                tier = render_model_selector(manager)
                assert tier == ModelTier.FAST


def run_model_switching_tests():
    """Run all model switching tests"""
    print("🧪 Running Model Switching and Persistence Tests...")
    
    # Test model switching
    test_switching = TestModelSwitching()
    test_switching.setup_method()
    
    try:
        test_switching.test_get_session_model_tier_default()
        print("✅ Default model tier test passed")
        
        test_switching.test_get_session_model_tier_premium()
        print("✅ Premium model tier test passed")
        
        test_switching.test_model_manager_tier_switching()
        print("✅ Model manager switching test passed")
        
        test_switching.test_model_config_properties()
        print("✅ Model config properties test passed")
        
    except Exception as e:
        print(f"❌ Model switching test failed: {e}")
        return False
    
    # Test UI components
    test_ui = TestModelUI()
    test_ui.setup_method()
    
    try:
        test_ui.test_header_model_indicator()
        print("✅ Header model indicator test passed")
        
    except Exception as e:
        print(f"❌ Model UI test failed: {e}")
        return False
    
    print("\n🎉 Core model switching tests passed!")
    print("📝 Note: Session persistence tests require full Streamlit environment")
    return True


if __name__ == "__main__":
    success = run_model_switching_tests()
    exit(0 if success else 1)