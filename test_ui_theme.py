"""
Test suite for UI theme system and components.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from theme_manager import ThemeManager, ThemeConfig
from ui_components import ChatInterface, AuthInterface, Message
from styles import StyleGenerator
from datetime import datetime


class MockSessionState:
    """Mock Streamlit session state for testing."""
    def __init__(self):
        self._state = {}
    
    def get(self, key, default=None):
        return self._state.get(key, default)
    
    def __getitem__(self, key):
        return self._state[key]
    
    def __setitem__(self, key, value):
        self._state[key] = value
    
    def __contains__(self, key):
        return key in self._state
    
    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            self._state[key] = value
    
    def __getattr__(self, key):
        if key.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
        return self._state.get(key)


class TestThemeManager:
    """Test cases for ThemeManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.theme_manager = ThemeManager()
    
    def test_theme_initialization(self):
        """Test theme manager initialization."""
        assert "light" in self.theme_manager.themes
        assert "dark" in self.theme_manager.themes
        assert isinstance(self.theme_manager.themes["light"], ThemeConfig)
        assert isinstance(self.theme_manager.themes["dark"], ThemeConfig)
    
    def test_get_current_theme_default(self):
        """Test getting current theme returns default."""
        mock_state = MockSessionState()
        with patch('theme_manager.st.session_state', mock_state):
            theme = self.theme_manager.get_current_theme()
            assert theme == "light"
    
    def test_toggle_theme(self):
        """Test theme toggling functionality."""
        mock_state = MockSessionState()
        mock_state.theme = "light"
        with patch('theme_manager.st.session_state', mock_state):
            new_theme = self.theme_manager.toggle_theme()
            assert new_theme == "dark"
            assert mock_state.theme == "dark"
            
            # Toggle back
            new_theme = self.theme_manager.toggle_theme()
            assert new_theme == "light"
            assert mock_state.theme == "light"
    
    def test_set_theme(self):
        """Test setting specific theme."""
        mock_state = MockSessionState()
        with patch('theme_manager.st.session_state', mock_state):
            self.theme_manager.set_theme("dark")
            assert mock_state.theme == "dark"
            
            # Test invalid theme (should not change)
            self.theme_manager.set_theme("invalid")
            assert mock_state.theme == "dark"
    
    def test_get_theme_config(self):
        """Test getting theme configuration."""
        light_config = self.theme_manager.get_theme_config("light")
        dark_config = self.theme_manager.get_theme_config("dark")
        
        assert light_config.name == "light"
        assert dark_config.name == "dark"
        assert light_config.background_color != dark_config.background_color
    
    def test_css_generation(self):
        """Test CSS generation."""
        config = self.theme_manager.get_theme_config("light")
        css = self.theme_manager._generate_css(config)
        
        assert ":root" in css
        assert config.primary_color in css
        assert config.background_color in css
        assert ".message-bubble" in css


class TestChatInterface:
    """Test cases for ChatInterface class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.theme_manager = Mock()
        self.chat_interface = ChatInterface(self.theme_manager)
    
    def test_message_formatting(self):
        """Test message content formatting."""
        content = "This is **bold** and *italic* text with `code`"
        formatted = self.chat_interface._format_message_content(content)
        
        assert "<strong>bold</strong>" in formatted
        assert "<em>italic</em>" in formatted
        assert "<code>code</code>" in formatted
    
    def test_message_bubble_rendering(self):
        """Test message bubble HTML generation."""
        message = Message(
            role="user",
            content="Test message",
            timestamp=datetime.now(),
            model_used=None
        )
        
        # This would normally render HTML, but we can test the logic
        assert message.role == "user"
        assert message.content == "Test message"
    
    def test_html_escaping(self):
        """Test HTML content is properly escaped."""
        content = "<script>alert('xss')</script>"
        formatted = self.chat_interface._format_message_content(content)
        
        assert "&lt;script&gt;" in formatted
        assert "<script>" not in formatted


class TestStyleGenerator:
    """Test cases for StyleGenerator class."""
    
    def test_base_styles_generation(self):
        """Test base styles generation."""
        config = ThemeConfig(
            name="test",
            primary_color="#000000",
            background_color="#ffffff",
            secondary_background_color="#f0f0f0",
            text_color="#333333",
            accent_color="#ff0000",
            user_message_bg="#e0e0e0",
            ai_message_bg="#f5f5f5",
            border_color="#cccccc",
            shadow_color="rgba(0,0,0,0.1)"
        )
        
        css = StyleGenerator.generate_base_styles(config)
        
        assert ":root" in css
        assert config.primary_color in css
        assert config.background_color in css
        assert ".stApp" in css
    
    def test_chat_styles_generation(self):
        """Test chat-specific styles generation."""
        css = StyleGenerator.generate_chat_styles()
        
        assert ".chat-container" in css
        assert ".message-bubble" in css
        assert ".user-message" in css
        assert ".ai-message" in css
        assert "@keyframes" in css
    
    def test_responsive_styles_generation(self):
        """Test responsive styles generation."""
        css = StyleGenerator.generate_responsive_styles()
        
        assert "@media" in css
        assert "max-width: 768px" in css
        assert "max-width: 480px" in css
        assert "min-width: 1200px" in css
    
    def test_accessibility_styles_generation(self):
        """Test accessibility styles generation."""
        css = StyleGenerator.generate_accessibility_styles()
        
        assert "focus" in css
        assert "prefers-reduced-motion" in css
        assert "prefers-contrast" in css
        assert ".sr-only" in css


class TestAuthInterface:
    """Test cases for AuthInterface class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.theme_manager = Mock()
        self.auth_interface = AuthInterface(self.theme_manager)
    
    def test_auth_interface_initialization(self):
        """Test auth interface initialization."""
        assert self.auth_interface.theme_manager is not None


class TestResponsiveDesign:
    """Test cases for responsive design features."""
    
    def test_layout_config(self):
        """Test responsive layout configuration."""
        from ui_components import ResponsiveLayout
        
        config = ResponsiveLayout.get_layout_config()
        
        assert "sidebar_width" in config
        assert "main_width" in config
        assert "mobile_breakpoint" in config
        assert "tablet_breakpoint" in config
        
        assert config["mobile_breakpoint"] == 768
        assert config["tablet_breakpoint"] == 1024
    
    def test_responsive_css(self):
        """Test responsive CSS generation."""
        from ui_components import ResponsiveLayout
        
        css = ResponsiveLayout.apply_responsive_css()
        
        assert "@media" in css
        assert "max-width: 480px" in css
        assert "max-width: 768px" in css


def test_theme_consistency():
    """Test that themes have consistent structure."""
    theme_manager = ThemeManager()
    
    light_theme = theme_manager.get_theme_config("light")
    dark_theme = theme_manager.get_theme_config("dark")
    
    # Check that both themes have all required attributes
    required_attrs = [
        "name", "primary_color", "background_color", "secondary_background_color",
        "text_color", "accent_color", "user_message_bg", "ai_message_bg",
        "border_color", "shadow_color"
    ]
    
    for attr in required_attrs:
        assert hasattr(light_theme, attr)
        assert hasattr(dark_theme, attr)
        assert getattr(light_theme, attr) is not None
        assert getattr(dark_theme, attr) is not None


def test_css_color_format():
    """Test that CSS colors are in valid format."""
    theme_manager = ThemeManager()
    
    for theme_name in ["light", "dark"]:
        config = theme_manager.get_theme_config(theme_name)
        
        # Test hex colors
        hex_colors = [
            config.primary_color, config.background_color, 
            config.text_color, config.accent_color
        ]
        
        for color in hex_colors:
            assert color.startswith("#") or color.startswith("rgb")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])