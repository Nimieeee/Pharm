"""
Comprehensive UI Component Tests
Tests for theme switching, responsiveness, and UI component functionality
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from datetime import datetime
import sys
import os
import re

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from theme_manager import ThemeManager, ThemeConfig
from ui_components import ChatInterface, AuthInterface, Message, SettingsInterface, ResponsiveLayout


class TestThemeManager(unittest.TestCase):
    """Unit tests for ThemeManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.theme_manager = ThemeManager()
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_initialization(self, mock_session_state):
        """Test ThemeManager initialization"""
        theme_manager = ThemeManager()
        
        self.assertIsNotNone(theme_manager)
        self.assertIn("light", theme_manager.themes)
        self.assertIn("dark", theme_manager.themes)
        self.assertEqual(mock_session_state.get("theme", "light"), "light")
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_get_current_theme(self, mock_session_state):
        """Test getting current theme"""
        mock_session_state["theme"] = "dark"
        
        current_theme = self.theme_manager.get_current_theme()
        self.assertEqual(current_theme, "dark")
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_toggle_theme(self, mock_session_state):
        """Test theme toggling"""
        # Start with light theme
        mock_session_state["theme"] = "light"
        
        # Toggle to dark
        new_theme = self.theme_manager.toggle_theme()
        self.assertEqual(new_theme, "dark")
        self.assertEqual(mock_session_state["theme"], "dark")
        
        # Toggle back to light
        new_theme = self.theme_manager.toggle_theme()
        self.assertEqual(new_theme, "light")
        self.assertEqual(mock_session_state["theme"], "light")
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_set_theme(self, mock_session_state):
        """Test setting specific theme"""
        self.theme_manager.set_theme("dark")
        self.assertEqual(mock_session_state["theme"], "dark")
        
        # Test invalid theme (should not change)
        self.theme_manager.set_theme("invalid")
        self.assertEqual(mock_session_state["theme"], "dark")  # Should remain unchanged
    
    def test_get_theme_config(self):
        """Test getting theme configuration"""
        light_config = self.theme_manager.get_theme_config("light")
        dark_config = self.theme_manager.get_theme_config("dark")
        
        self.assertIsInstance(light_config, ThemeConfig)
        self.assertIsInstance(dark_config, ThemeConfig)
        
        self.assertEqual(light_config.name, "light")
        self.assertEqual(dark_config.name, "dark")
        
        # Verify different colors
        self.assertNotEqual(light_config.background_color, dark_config.background_color)
        self.assertNotEqual(light_config.text_color, dark_config.text_color)
    
    def test_css_generation(self):
        """Test CSS generation from theme config"""
        light_config = self.theme_manager.get_theme_config("light")
        css = self.theme_manager._generate_css(light_config)
        
        self.assertIsInstance(css, str)
        self.assertIn("<style>", css)
        self.assertIn("</style>", css)
        self.assertIn(":root", css)
        self.assertIn("--primary-color", css)
        self.assertIn("--background-color", css)
        self.assertIn("--text-color", css)
        
        # Verify responsive design elements
        self.assertIn("@media", css)
        self.assertIn("max-width", css)
        
        # Verify animations
        self.assertIn("@keyframes", css)
        self.assertIn("fadeIn", css)
    
    @patch('streamlit.markdown')
    def test_apply_theme(self, mock_markdown):
        """Test theme application"""
        self.theme_manager.apply_theme("light")
        
        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args
        
        # Verify CSS was passed to markdown
        self.assertIn("<style>", call_args[0][0])
        self.assertEqual(call_args[1]["unsafe_allow_html"], True)
    
    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.columns')
    @patch('streamlit.button')
    @patch('streamlit.rerun')
    def test_render_theme_toggle(self, mock_rerun, mock_button, mock_columns, mock_session_state):
        """Test theme toggle button rendering"""
        mock_session_state["theme"] = "light"
        
        # Mock columns
        mock_col1, mock_col2, mock_col3 = Mock(), Mock(), Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        
        # Mock button click
        mock_button.return_value = True
        
        self.theme_manager.render_theme_toggle()
        
        # Verify columns were created
        mock_columns.assert_called_once_with([1, 1, 1])
        
        # Verify button was created
        mock_button.assert_called_once()
        
        # Verify rerun was called (theme changed)
        mock_rerun.assert_called_once()


class TestChatInterface(unittest.TestCase):
    """Unit tests for ChatInterface"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_theme_manager = Mock()
        self.chat_interface = ChatInterface(self.mock_theme_manager)
        
        # Create test messages
        self.test_messages = [
            Message(
                role="user",
                content="What is aspirin?",
                timestamp=datetime(2024, 1, 1, 12, 0, 0)
            ),
            Message(
                role="assistant",
                content="Aspirin is a **pain reliever** that works by inhibiting COX enzymes.",
                timestamp=datetime(2024, 1, 1, 12, 0, 30),
                model_used="gemma2-9b-it"
            )
        ]
    
    def test_initialization(self):
        """Test ChatInterface initialization"""
        self.assertIsNotNone(self.chat_interface)
        self.assertEqual(self.chat_interface.theme_manager, self.mock_theme_manager)
    
    @patch('streamlit.markdown')
    def test_render_message_bubble_user(self, mock_markdown):
        """Test rendering user message bubble"""
        user_message = self.test_messages[0]
        
        self.chat_interface.render_message_bubble(user_message)
        
        mock_markdown.assert_called_once()
        html_content = mock_markdown.call_args[0][0]
        
        # Verify user message styling
        self.assertIn("user-message", html_content)
        self.assertIn("You", html_content)
        self.assertIn("What is aspirin?", html_content)
        self.assertIn("12:00", html_content)  # Time formatting
    
    @patch('streamlit.markdown')
    def test_render_message_bubble_assistant(self, mock_markdown):
        """Test rendering assistant message bubble"""
        ai_message = self.test_messages[1]
        
        self.chat_interface.render_message_bubble(ai_message)
        
        mock_markdown.assert_called_once()
        html_content = mock_markdown.call_args[0][0]
        
        # Verify AI message styling
        self.assertIn("ai-message", html_content)
        self.assertIn("AI Assistant", html_content)
        self.assertIn("gemma2-9b-it", html_content)  # Model info
        self.assertIn("<strong>pain reliever</strong>", html_content)  # Markdown formatting
    
    def test_format_message_content(self):
        """Test message content formatting"""
        # Test markdown-like formatting
        content = "This is **bold** and *italic* and `code`"
        formatted = self.chat_interface._format_message_content(content)
        
        self.assertIn("<strong>bold</strong>", formatted)
        self.assertIn("<em>italic</em>", formatted)
        self.assertIn("<code>code</code>", formatted)
        
        # Test HTML escaping
        content = "This has <script>alert('xss')</script> tags"
        formatted = self.chat_interface._format_message_content(content)
        
        self.assertIn("&lt;script&gt;", formatted)
        self.assertIn("&lt;/script&gt;", formatted)
        
        # Test line breaks
        content = "Line 1\nLine 2"
        formatted = self.chat_interface._format_message_content(content)
        
        self.assertIn("Line 1<br>Line 2", formatted)
    
    @patch('streamlit.markdown')
    def test_render_chat_history_empty(self, mock_markdown):
        """Test rendering empty chat history"""
        self.chat_interface.render_chat_history([])
        
        # Should render welcome message
        mock_markdown.assert_called_once()
        html_content = mock_markdown.call_args[0][0]
        
        self.assertIn("Welcome", html_content)
        self.assertIn("pharmacology", html_content.lower())
    
    @patch('streamlit.markdown')
    def test_render_chat_history_with_messages(self, mock_markdown):
        """Test rendering chat history with messages"""
        self.chat_interface.render_chat_history(self.test_messages)
        
        # Should call markdown for each message
        self.assertEqual(mock_markdown.call_count, len(self.test_messages))
    
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    def test_render_message_input(self, mock_columns, mock_button, mock_text_input):
        """Test message input rendering"""
        # Mock columns
        mock_col1, mock_col2 = Mock(), Mock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Mock input and button
        mock_text_input.return_value = "Test message"
        mock_button.return_value = True
        
        result = self.chat_interface.render_message_input()
        
        # Verify components were created
        mock_columns.assert_called_once_with([4, 1])
        mock_text_input.assert_called_once()
        mock_button.assert_called_once()
        
        # Should return the input text
        self.assertEqual(result, "Test message")
    
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    def test_render_message_input_empty(self, mock_columns, mock_button, mock_text_input):
        """Test message input with empty input"""
        mock_columns.return_value = [Mock(), Mock()]
        mock_text_input.return_value = ""
        mock_button.return_value = True
        
        result = self.chat_interface.render_message_input()
        
        # Should return None for empty input
        self.assertIsNone(result)
    
    @patch('streamlit.markdown')
    def test_render_typing_indicator(self, mock_markdown):
        """Test typing indicator rendering"""
        self.chat_interface.render_typing_indicator()
        
        mock_markdown.assert_called_once()
        html_content = mock_markdown.call_args[0][0]
        
        self.assertIn("ai-message", html_content)
        self.assertIn("loading-dots", html_content)
        self.assertIn("Thinking", html_content)
    
    @patch('streamlit.checkbox')
    @patch('streamlit.markdown')
    @patch('streamlit.rerun')
    def test_render_model_selector(self, mock_rerun, mock_markdown, mock_checkbox):
        """Test model toggle switch rendering"""
        # Mock session state
        with patch('streamlit.session_state', {'model_toggle_switch': False}):
            available_models = [
                {"id": "gemma2-9b-it", "name": "Fast Model", "description": "Quick responses"},
                {"id": "qwen/qwen3-32b", "name": "Premium Model", "description": "High quality responses"}
            ]
            
            mock_checkbox.return_value = False  # Fast mode
            
            result = self.chat_interface.render_model_selector("gemma2-9b-it", available_models)
            
            # Verify toggle switch HTML was rendered
            mock_markdown.assert_called()
            html_calls = [call[0][0] for call in mock_markdown.call_args_list]
            toggle_html_found = any("toggle-switch" in html for html in html_calls if isinstance(html, str))
            self.assertTrue(toggle_html_found, "Toggle switch HTML should be rendered")
            
            # Should return the fast model ID
            self.assertEqual(result, "gemma2-9b-it")
    
    @patch('streamlit.markdown')
    def test_render_status_indicator(self, mock_markdown):
        """Test status indicator rendering"""
        self.chat_interface.render_status_indicator("online", "Connected to server")
        
        mock_markdown.assert_called_once()
        html_content = mock_markdown.call_args[0][0]
        
        self.assertIn("status-online", html_content)
        self.assertIn("Connected", html_content)
        self.assertIn("Connected to server", html_content)
    
    @patch('streamlit.button')
    @patch('streamlit.columns')
    def test_render_conversation_controls(self, mock_columns, mock_button):
        """Test conversation controls rendering"""
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        mock_button.side_effect = [True, False, False]  # Only clear button clicked
        
        controls = self.chat_interface.render_conversation_controls()
        
        # Verify all buttons were created
        self.assertEqual(mock_button.call_count, 3)
        
        # Verify return values
        self.assertTrue(controls["clear"])
        self.assertFalse(controls["export"])
        self.assertFalse(controls["settings"])


class TestAuthInterface(unittest.TestCase):
    """Unit tests for AuthInterface"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_theme_manager = Mock()
        self.auth_interface = AuthInterface(self.mock_theme_manager)
    
    @patch('streamlit.form')
    @patch('streamlit.text_input')
    @patch('streamlit.form_submit_button')
    @patch('streamlit.columns')
    @patch('streamlit.markdown')
    def test_render_login_form_login(self, mock_markdown, mock_columns, mock_submit, mock_input, mock_form):
        """Test login form rendering for login action"""
        # Mock form context
        mock_form.return_value.__enter__ = Mock()
        mock_form.return_value.__exit__ = Mock()
        
        # Mock columns
        mock_columns.return_value = [Mock(), Mock()]
        
        # Mock inputs
        mock_input.side_effect = ["test@example.com", "password123"]
        mock_submit.side_effect = [True, False]  # Login button clicked
        
        with patch('streamlit.form'):
            result = self.auth_interface.render_login_form()
        
        expected = {
            "action": "login",
            "email": "test@example.com",
            "password": "password123"
        }
        
        self.assertEqual(result, expected)
    
    @patch('streamlit.sidebar')
    @patch('streamlit.markdown')
    @patch('streamlit.button')
    def test_render_user_profile(self, mock_button, mock_markdown, mock_sidebar):
        """Test user profile rendering"""
        mock_button.return_value = True  # Logout clicked
        
        result = self.auth_interface.render_user_profile("test@example.com")
        
        # Verify profile was rendered
        mock_markdown.assert_called()
        mock_button.assert_called_once()
        
        # Should return True (logout clicked)
        self.assertTrue(result)


class TestResponsiveLayout(unittest.TestCase):
    """Unit tests for ResponsiveLayout"""
    
    def test_get_layout_config(self):
        """Test layout configuration"""
        config = ResponsiveLayout.get_layout_config()
        
        self.assertIsInstance(config, dict)
        self.assertIn("sidebar_width", config)
        self.assertIn("main_width", config)
        self.assertIn("mobile_breakpoint", config)
        self.assertIn("tablet_breakpoint", config)
        
        # Verify reasonable values
        self.assertGreater(config["sidebar_width"], 0)
        self.assertGreater(config["main_width"], 0)
        self.assertLess(config["mobile_breakpoint"], config["tablet_breakpoint"])
    
    def test_apply_responsive_css(self):
        """Test responsive CSS generation"""
        css = ResponsiveLayout.apply_responsive_css()
        
        self.assertIsInstance(css, str)
        self.assertIn("<style>", css)
        self.assertIn("</style>", css)
        
        # Verify responsive breakpoints
        self.assertIn("@media (max-width: 480px)", css)
        self.assertIn("@media (max-width: 768px)", css)
        self.assertIn("@media (min-width: 1024px)", css)
        
        # Verify mobile optimizations
        self.assertIn("font-size: 16px", css)  # Prevent iOS zoom
        self.assertIn("padding", css)
    
    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.columns')
    @patch('streamlit.button')
    @patch('streamlit.markdown')
    def test_render_mobile_header(self, mock_markdown, mock_button, mock_columns, mock_session_state):
        """Test mobile header rendering"""
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        mock_button.return_value = True
        
        ResponsiveLayout.render_mobile_header()
        
        # Verify components were created
        mock_columns.assert_called_once_with([1, 2, 1])
        mock_button.assert_called_once()
        mock_markdown.assert_called_once()
        
        # Verify session state was updated
        self.assertTrue(mock_session_state.get("show_sidebar", False))


class TestUIIntegration(unittest.TestCase):
    """Integration tests for UI components"""
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_theme_chat_integration(self, mock_session_state):
        """Test theme manager integration with chat interface"""
        theme_manager = ThemeManager()
        chat_interface = ChatInterface(theme_manager)
        
        # Test theme switching affects chat interface
        theme_manager.set_theme("dark")
        dark_config = theme_manager.get_theme_config()
        
        self.assertEqual(dark_config.name, "dark")
        self.assertEqual(mock_session_state["theme"], "dark")
        
        # Chat interface should use the theme manager
        self.assertEqual(chat_interface.theme_manager, theme_manager)
    
    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.markdown')
    def test_responsive_theme_application(self, mock_markdown, mock_session_state):
        """Test responsive design with theme application"""
        theme_manager = ThemeManager()
        
        # Apply theme
        theme_manager.apply_theme("light")
        
        # Verify CSS includes responsive elements
        css_content = mock_markdown.call_args[0][0]
        
        # Should include both theme and responsive styles
        self.assertIn("--primary-color", css_content)
        self.assertIn("@media", css_content)
        self.assertIn("max-width", css_content)
    
    def test_ui_component_consistency(self):
        """Test consistency across UI components"""
        theme_manager = ThemeManager()
        chat_interface = ChatInterface(theme_manager)
        auth_interface = AuthInterface(theme_manager)
        
        # All components should use the same theme manager
        self.assertEqual(chat_interface.theme_manager, theme_manager)
        self.assertEqual(auth_interface.theme_manager, theme_manager)
        
        # All components should be properly initialized
        self.assertIsNotNone(chat_interface)
        self.assertIsNotNone(auth_interface)


def run_ui_comprehensive_tests():
    """Run all UI component tests"""
    print("🎨 Running Comprehensive UI Component Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestThemeManager,
        TestChatInterface,
        TestAuthInterface,
        TestResponsiveLayout,
        TestUIIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All UI component tests passed!")
        print("\nUI Features Tested:")
        print("• Theme switching (light/dark mode)")
        print("• CSS generation and application")
        print("• Chat interface components")
        print("• Message formatting and display")
        print("• Authentication interface")
        print("• Responsive design utilities")
        print("• Mobile-optimized layouts")
        print("• Component integration")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False


if __name__ == "__main__":
    success = run_ui_comprehensive_tests()
    exit(0 if success else 1)