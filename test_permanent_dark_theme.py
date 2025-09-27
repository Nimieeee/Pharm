"""
Test permanent dark theme implementation
"""
import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from theme_manager import ThemeManager


class TestPermanentDarkTheme(unittest.TestCase):
    """Test permanent dark theme enforcement"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.theme_manager = ThemeManager()
    
    def test_permanent_dark_theme_initialization(self):
        """Test that theme manager always initializes with dark theme"""
        theme_manager = ThemeManager()
        
        # Should have dark theme configuration
        self.assertEqual(theme_manager.dark_theme.name, "dark")
        self.assertEqual(theme_manager.get_current_theme(), "dark")
    
    def test_get_current_theme_always_dark(self):
        """Test that get_current_theme always returns 'dark'"""
        theme = self.theme_manager.get_current_theme()
        self.assertEqual(theme, "dark")
    
    def test_get_theme_config_always_dark(self):
        """Test that get_theme_config always returns dark theme config"""
        config = self.theme_manager.get_theme_config()
        self.assertEqual(config.name, "dark")
        
        # Test with explicit theme name (should still return dark)
        config_light = self.theme_manager.get_theme_config("light")
        self.assertEqual(config_light.name, "dark")
    
    def test_dark_theme_colors_high_contrast(self):
        """Test that dark theme uses high contrast colors"""
        config = self.theme_manager.get_theme_config()
        
        # Check background is dark
        self.assertEqual(config.background_color, "#0e1117")
        
        # Check text is white for maximum contrast
        self.assertEqual(config.text_color, "#ffffff")
        
        # Check secondary background is darker
        self.assertEqual(config.secondary_background_color, "#262730")
        
        # Check primary color is visible on dark background
        self.assertEqual(config.primary_color, "#4fc3f7")
    
    def test_theme_toggle_removed(self):
        """Test that theme toggle functionality is removed"""
        # render_theme_toggle should do nothing
        with patch('streamlit.columns') as mock_columns:
            self.theme_manager.render_theme_toggle()
            # Should not create columns or buttons
            mock_columns.assert_not_called()
    
    @patch('streamlit.markdown')
    def test_apply_theme_uses_dark_theme(self, mock_markdown):
        """Test that apply_theme always uses dark theme"""
        self.theme_manager.apply_theme()
        
        # Should call markdown with CSS
        mock_markdown.assert_called_once()
        args, kwargs = mock_markdown.call_args
        
        # Check that CSS contains dark theme variables
        css_content = args[0]
        self.assertIn("--background-color: #0e1117", css_content)
        self.assertIn("--text-color: #ffffff", css_content)
        self.assertIn("--secondary-bg: #262730", css_content)
    
    def test_no_toggle_theme_method(self):
        """Test that toggle_theme method is removed"""
        # Should not have toggle_theme method
        self.assertFalse(hasattr(self.theme_manager, 'toggle_theme'))
    
    def test_no_set_theme_method(self):
        """Test that set_theme method is removed"""
        # Should not have set_theme method
        self.assertFalse(hasattr(self.theme_manager, 'set_theme'))
    
    def test_css_enforces_dark_theme(self):
        """Test that generated CSS enforces dark theme on all elements"""
        config = self.theme_manager.get_theme_config()
        css = self.theme_manager._generate_css(config)
        
        # Check for important declarations to override any light theme
        self.assertIn("!important", css)
        
        # Check for dark theme enforcement
        self.assertIn("background-color: var(--background-color) !important", css)
        self.assertIn("color: var(--text-color) !important", css)
        
        # Check for high contrast text
        self.assertIn("color: var(--text-color) !important", css)


if __name__ == "__main__":
    unittest.main()