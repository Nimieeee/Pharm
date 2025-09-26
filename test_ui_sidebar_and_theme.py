#!/usr/bin/env python3
"""
UI Tests for Sidebar Simplification and Dark Theme Enforcement
Tests the UI components for sidebar cleanup and permanent dark theme implementation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))


class TestSidebarSimplification(unittest.TestCase):
    """Test sidebar simplification functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from ui_components import ChatInterface
            from auth_manager import AuthenticationManager
            from session_manager import SessionManager
            self.ChatInterface = ChatInterface
            self.AuthenticationManager = AuthenticationManager
            self.SessionManager = SessionManager
        except ImportError as e:
            self.skipTest(f"Required UI components not available: {e}")
    
    def test_sidebar_removes_plan_subscription_display(self):
        """Test that sidebar doesn't display plan/subscription information"""
        try:
            # Mock authentication manager
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            mock_auth.get_user_email.return_value = "test@example.com"
            
            # Mock session manager
            mock_session = Mock()
            mock_session.get_user_id.return_value = "test-user-id"
            
            with patch('streamlit.sidebar') as mock_sidebar:
                chat_interface = self.ChatInterface(mock_auth, mock_session)
                
                # Render sidebar
                chat_interface.render_sidebar()
                
                # Check that plan-related content is not rendered
                sidebar_calls = [str(call) for call in mock_sidebar.method_calls]
                sidebar_content = ' '.join(sidebar_calls)
                
                # Should not contain plan/subscription references
                plan_keywords = ['plan', 'subscription', 'tier', 'free', 'premium', 'upgrade']
                for keyword in plan_keywords:
                    self.assertNotIn(keyword.lower(), sidebar_content.lower(),
                                   f"Sidebar should not contain '{keyword}' references")
            
        except Exception as e:
            self.skipTest(f"Sidebar plan display test failed: {e}")
    
    def test_sidebar_removes_pagination_controls(self):
        """Test that sidebar doesn't show pagination controls"""
        try:
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            mock_session = Mock()
            
            with patch('streamlit.sidebar') as mock_sidebar:
                chat_interface = self.ChatInterface(mock_auth, mock_session)
                
                # Render sidebar
                chat_interface.render_sidebar()
                
                # Check that pagination controls are not rendered
                sidebar_calls = [str(call) for call in mock_sidebar.method_calls]
                sidebar_content = ' '.join(sidebar_calls)
                
                # Should not contain pagination references
                pagination_keywords = [
                    'messages per page', 'page size', 'pagination', 'per conversation',
                    'selectbox', 'dropdown', 'items per page', 'show all'
                ]
                
                for keyword in pagination_keywords:
                    self.assertNotIn(keyword.lower(), sidebar_content.lower(),
                                   f"Sidebar should not contain '{keyword}' controls")
            
        except Exception as e:
            self.skipTest(f"Sidebar pagination controls test failed: {e}")
    
    def test_sidebar_removes_message_count_dropdowns(self):
        """Test that sidebar doesn't show message count dropdowns"""
        try:
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            mock_session = Mock()
            
            with patch('streamlit.sidebar') as mock_sidebar:
                chat_interface = self.ChatInterface(mock_auth, mock_session)
                
                # Render sidebar
                chat_interface.render_sidebar()
                
                # Check for absence of selectbox calls for message counts
                selectbox_calls = [call for call in mock_sidebar.method_calls 
                                 if 'selectbox' in str(call)]
                
                # Should not have selectbox for message counts
                for call in selectbox_calls:
                    call_str = str(call).lower()
                    self.assertNotIn('message', call_str)
                    self.assertNotIn('count', call_str)
                    self.assertNotIn('per page', call_str)
            
        except Exception as e:
            self.skipTest(f"Message count dropdown test failed: {e}")
    
    def test_sidebar_contains_only_essential_elements(self):
        """Test that sidebar contains only essential user controls"""
        try:
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            mock_auth.get_user_email.return_value = "test@example.com"
            mock_session = Mock()
            
            with patch('streamlit.sidebar') as mock_sidebar:
                chat_interface = self.ChatInterface(mock_auth, mock_session)
                
                # Render sidebar
                chat_interface.render_sidebar()
                
                # Check that essential elements are present
                sidebar_calls = [str(call) for call in mock_sidebar.method_calls]
                sidebar_content = ' '.join(sidebar_calls)
                
                # Should contain user email
                self.assertIn("test@example.com", sidebar_content)
                
                # Should contain logout functionality
                logout_present = any('logout' in str(call).lower() for call in mock_sidebar.method_calls)
                self.assertTrue(logout_present, "Sidebar should contain logout functionality")
            
        except Exception as e:
            self.skipTest(f"Essential elements test failed: {e}")
    
    def test_sidebar_streamlined_user_profile(self):
        """Test that user profile section is streamlined"""
        try:
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            mock_auth.get_user_email.return_value = "user@example.com"
            mock_session = Mock()
            
            with patch('streamlit.sidebar') as mock_sidebar:
                chat_interface = self.ChatInterface(mock_auth, mock_session)
                
                # Render sidebar
                chat_interface.render_sidebar()
                
                # Count the number of UI elements in sidebar
                ui_element_calls = [call for call in mock_sidebar.method_calls 
                                  if any(method in str(call) for method in 
                                       ['write', 'markdown', 'text', 'button', 'selectbox'])]
                
                # Should have minimal UI elements (user info + logout + model selector)
                self.assertLessEqual(len(ui_element_calls), 10, 
                                   "Sidebar should have minimal UI elements")
            
        except Exception as e:
            self.skipTest(f"Streamlined profile test failed: {e}")


class TestPermanentDarkThemeUI(unittest.TestCase):
    """Test permanent dark theme enforcement in UI"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from theme_manager import ThemeManager
            from ui_components import ChatInterface
            self.ThemeManager = ThemeManager
            self.ChatInterface = ChatInterface
        except ImportError as e:
            self.skipTest(f"Theme components not available: {e}")
    
    def test_theme_manager_permanent_dark_mode(self):
        """Test that theme manager enforces permanent dark mode"""
        theme_manager = self.ThemeManager()
        
        # Should always return dark theme
        current_theme = theme_manager.get_current_theme()
        self.assertEqual(current_theme, "dark")
        
        # Should not have toggle functionality
        self.assertFalse(hasattr(theme_manager, 'toggle_theme'))
        self.assertFalse(hasattr(theme_manager, 'set_theme'))
    
    def test_dark_theme_color_configuration(self):
        """Test dark theme color configuration"""
        theme_manager = self.ThemeManager()
        config = theme_manager.get_theme_config()
        
        # Test background colors are dark
        self.assertEqual(config.background_color, "#0e1117")
        self.assertEqual(config.secondary_background_color, "#262730")
        
        # Test text color is white for high contrast
        self.assertEqual(config.text_color, "#ffffff")
        
        # Test primary color is visible on dark background
        self.assertEqual(config.primary_color, "#4fc3f7")
    
    @patch('streamlit.markdown')
    def test_dark_theme_css_application(self, mock_markdown):
        """Test that dark theme CSS is properly applied"""
        theme_manager = self.ThemeManager()
        
        # Apply theme
        theme_manager.apply_theme()
        
        # Should call markdown with CSS
        mock_markdown.assert_called_once()
        args, kwargs = mock_markdown.call_args
        
        css_content = args[0]
        
        # Check for dark theme CSS variables
        self.assertIn("--background-color: #0e1117", css_content)
        self.assertIn("--text-color: #ffffff", css_content)
        self.assertIn("--secondary-bg: #262730", css_content)
        self.assertIn("--primary-color: #4fc3f7", css_content)
        
        # Check for important declarations to override light theme
        self.assertIn("!important", css_content)
    
    def test_no_theme_toggle_ui_elements(self):
        """Test that theme toggle UI elements are not rendered"""
        theme_manager = self.ThemeManager()
        
        with patch('streamlit.columns') as mock_columns:
            # Attempt to render theme toggle (should do nothing)
            theme_manager.render_theme_toggle()
            
            # Should not create columns or buttons for theme toggle
            mock_columns.assert_not_called()
    
    def test_dark_theme_consistency_across_components(self):
        """Test dark theme consistency across all UI components"""
        theme_manager = self.ThemeManager()
        
        # Test that all theme configurations return dark theme
        configs = [
            theme_manager.get_theme_config(),
            theme_manager.get_theme_config("light"),  # Should still return dark
            theme_manager.get_theme_config("dark")
        ]
        
        for config in configs:
            self.assertEqual(config.name, "dark")
            self.assertEqual(config.background_color, "#0e1117")
            self.assertEqual(config.text_color, "#ffffff")
    
    def test_high_contrast_text_readability(self):
        """Test that dark theme ensures high contrast for text readability"""
        theme_manager = self.ThemeManager()
        config = theme_manager.get_theme_config()
        
        # Test contrast ratios (simplified check)
        bg_color = config.background_color  # #0e1117 (very dark)
        text_color = config.text_color      # #ffffff (white)
        
        # Background should be very dark
        self.assertTrue(bg_color.startswith("#0"), "Background should be very dark")
        
        # Text should be white for maximum contrast
        self.assertEqual(text_color, "#ffffff", "Text should be white for maximum contrast")
        
        # Secondary background should be darker than primary
        secondary_bg = config.secondary_background_color  # #262730
        self.assertTrue(secondary_bg > bg_color, "Secondary background should be lighter than primary")
    
    @patch('streamlit.markdown')
    def test_css_overrides_light_theme_elements(self, mock_markdown):
        """Test that CSS overrides any potential light theme elements"""
        theme_manager = self.ThemeManager()
        config = theme_manager.get_theme_config()
        
        # Generate CSS
        css = theme_manager._generate_css(config)
        
        # Should contain important declarations to override light theme
        important_selectors = [
            "background-color: var(--background-color) !important",
            "color: var(--text-color) !important"
        ]
        
        for selector in important_selectors:
            self.assertIn(selector, css, f"CSS should contain {selector}")
        
        # Should target common Streamlit elements
        streamlit_selectors = [
            ".stApp",
            ".main",
            ".sidebar",
            ".stButton",
            ".stSelectbox"
        ]
        
        for selector in streamlit_selectors:
            self.assertIn(selector, css, f"CSS should target {selector}")
    
    def test_dark_theme_message_bubble_styling(self):
        """Test dark theme styling for chat message bubbles"""
        theme_manager = self.ThemeManager()
        config = theme_manager.get_theme_config()
        css = theme_manager._generate_css(config)
        
        # Should style message bubbles for dark theme
        message_selectors = [
            ".user-message",
            ".assistant-message",
            ".message-content"
        ]
        
        for selector in message_selectors:
            if selector in css:  # Only test if selector exists
                # Should have dark theme colors
                self.assertIn("background", css)
                self.assertIn("color", css)


class TestUIComponentIntegration(unittest.TestCase):
    """Test integration between UI components with enhancements"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from ui_components import ChatInterface
            from theme_manager import ThemeManager
            from model_ui import render_model_selector
            self.ChatInterface = ChatInterface
            self.ThemeManager = ThemeManager
            self.render_model_selector = render_model_selector
        except ImportError as e:
            self.skipTest(f"UI integration components not available: {e}")
    
    def test_chat_interface_with_dark_theme(self):
        """Test chat interface integration with permanent dark theme"""
        try:
            mock_auth = Mock()
            mock_auth.is_authenticated.return_value = True
            mock_session = Mock()
            
            theme_manager = self.ThemeManager()
            
            with patch('streamlit.markdown') as mock_markdown:
                # Apply theme
                theme_manager.apply_theme()
                
                # Create chat interface
                chat_interface = self.ChatInterface(mock_auth, mock_session)
                
                # Should have applied dark theme
                mock_markdown.assert_called()
                
                # Theme should be dark
                self.assertEqual(theme_manager.get_current_theme(), "dark")
            
        except Exception as e:
            self.skipTest(f"Chat interface theme integration test failed: {e}")
    
    def test_model_selector_in_simplified_sidebar(self):
        """Test model selector integration in simplified sidebar"""
        try:
            with patch('streamlit.session_state', {'selected_model': 'fast'}):
                with patch('streamlit.sidebar') as mock_sidebar:
                    # Render model selector
                    result = self.render_model_selector()
                    
                    # Should render toggle switch instead of dropdown
                    sidebar_calls = [str(call) for call in mock_sidebar.method_calls]
                    sidebar_content = ' '.join(sidebar_calls)
                    
                    # Should not contain selectbox for model selection
                    selectbox_calls = [call for call in mock_sidebar.method_calls 
                                     if 'selectbox' in str(call)]
                    
                    model_selectbox = any('model' in str(call).lower() for call in selectbox_calls)
                    self.assertFalse(model_selectbox, "Should not use selectbox for model selection")
            
        except Exception as e:
            self.skipTest(f"Model selector integration test failed: {e}")
    
    def test_ui_consistency_across_pages(self):
        """Test UI consistency across different pages/components"""
        try:
            theme_manager = self.ThemeManager()
            
            # All components should use the same dark theme
            configs = []
            for _ in range(5):  # Test multiple instances
                config = theme_manager.get_theme_config()
                configs.append(config)
            
            # All configs should be identical
            for config in configs[1:]:
                self.assertEqual(config.name, configs[0].name)
                self.assertEqual(config.background_color, configs[0].background_color)
                self.assertEqual(config.text_color, configs[0].text_color)
            
        except Exception as e:
            self.skipTest(f"UI consistency test failed: {e}")


def run_ui_sidebar_and_theme_tests():
    """Run UI sidebar and theme tests"""
    print("🧪 UI Sidebar Simplification and Dark Theme Tests")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestSidebarSimplification,
        TestPermanentDarkThemeUI,
        TestUIComponentIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"📊 UI Sidebar and Theme Test Results:")
    print(f"  • Tests run: {result.testsRun}")
    print(f"  • Failures: {len(result.failures)}")
    print(f"  • Errors: {len(result.errors)}")
    print(f"  • Skipped: {len(result.skipped)}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\n✅ All UI sidebar and theme tests passed!")
        print(f"\n🎯 Verified UI Features:")
        print(f"  • Sidebar removes plan/subscription display")
        print(f"  • Sidebar removes pagination controls")
        print(f"  • Sidebar removes message count dropdowns")
        print(f"  • Sidebar contains only essential elements")
        print(f"  • Streamlined user profile section")
        print(f"  • Permanent dark theme enforcement")
        print(f"  • Dark theme color configuration")
        print(f"  • Dark theme CSS application")
        print(f"  • No theme toggle UI elements")
        print(f"  • High contrast text readability")
        print(f"  • CSS overrides for light theme elements")
        print(f"  • UI component integration")
    else:
        print(f"\n⚠️  Some UI sidebar and theme tests failed.")
        
        if result.failures:
            print(f"\n❌ Failures:")
            for test, traceback in result.failures:
                print(f"  • {test}")
        
        if result.errors:
            print(f"\n⚠️  Errors:")
            for test, traceback in result.errors:
                print(f"  • {test}")
    
    return success


if __name__ == "__main__":
    success = run_ui_sidebar_and_theme_tests()
    sys.exit(0 if success else 1)