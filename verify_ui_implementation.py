"""
Verification script for the responsive UI with theme support implementation.
This script validates that all components are working correctly.
"""
import sys
from datetime import datetime
from theme_manager import ThemeManager, ThemeConfig
from ui_components import ChatInterface, AuthInterface, SettingsInterface, Message
from styles import StyleGenerator
from ui_integration import PharmacologyUI


def verify_theme_manager():
    """Verify ThemeManager functionality."""
    print("🎨 Verifying ThemeManager...")
    
    theme_manager = ThemeManager()
    
    # Test theme configurations
    assert "light" in theme_manager.themes
    assert "dark" in theme_manager.themes
    
    # Test theme switching
    light_config = theme_manager.get_theme_config("light")
    dark_config = theme_manager.get_theme_config("dark")
    
    assert isinstance(light_config, ThemeConfig)
    assert isinstance(dark_config, ThemeConfig)
    assert light_config.background_color != dark_config.background_color
    
    # Test CSS generation
    css = theme_manager._generate_css(light_config)
    assert ":root" in css
    assert light_config.primary_color in css
    
    print("✅ ThemeManager verification passed")


def verify_ui_components():
    """Verify UI components functionality."""
    print("🧩 Verifying UI Components...")
    
    theme_manager = ThemeManager()
    chat_interface = ChatInterface(theme_manager)
    auth_interface = AuthInterface(theme_manager)
    settings_interface = SettingsInterface(theme_manager)
    
    # Test message formatting
    test_content = "This is **bold** and *italic* with `code`"
    formatted = chat_interface._format_message_content(test_content)
    assert "<strong>bold</strong>" in formatted
    assert "<em>italic</em>" in formatted
    assert "<code>code</code>" in formatted
    
    # Test HTML escaping
    dangerous_content = "<script>alert('xss')</script>"
    safe_content = chat_interface._format_message_content(dangerous_content)
    assert "&lt;script&gt;" in safe_content
    assert "<script>" not in safe_content
    
    # Test message creation
    message = Message(
        role="user",
        content="Test message",
        timestamp=datetime.now()
    )
    assert message.role == "user"
    assert message.content == "Test message"
    
    print("✅ UI Components verification passed")


def verify_style_generator():
    """Verify StyleGenerator functionality."""
    print("🎨 Verifying StyleGenerator...")
    
    # Test theme config
    config = ThemeConfig(
        name="test",
        primary_color="#1f77b4",
        background_color="#ffffff",
        secondary_background_color="#f8f9fa",
        text_color="#262730",
        accent_color="#ff6b6b",
        user_message_bg="#e3f2fd",
        ai_message_bg="#f5f5f5",
        border_color="#e0e0e0",
        shadow_color="rgba(0, 0, 0, 0.1)"
    )
    
    # Test all style generators
    base_styles = StyleGenerator.generate_base_styles(config)
    chat_styles = StyleGenerator.generate_chat_styles()
    form_styles = StyleGenerator.generate_form_styles()
    layout_styles = StyleGenerator.generate_layout_styles()
    responsive_styles = StyleGenerator.generate_responsive_styles()
    accessibility_styles = StyleGenerator.generate_accessibility_styles()
    
    # Verify CSS content
    assert ":root" in base_styles
    assert config.primary_color in base_styles
    assert ".message-bubble" in chat_styles
    assert ".stButton" in form_styles
    assert "@media" in responsive_styles
    assert "focus" in accessibility_styles
    
    print("✅ StyleGenerator verification passed")


def verify_responsive_design():
    """Verify responsive design features."""
    print("📱 Verifying Responsive Design...")
    
    from ui_components import ResponsiveLayout
    
    # Test layout configuration
    config = ResponsiveLayout.get_layout_config()
    required_keys = ["sidebar_width", "main_width", "mobile_breakpoint", "tablet_breakpoint"]
    
    for key in required_keys:
        assert key in config
    
    assert config["mobile_breakpoint"] == 768
    assert config["tablet_breakpoint"] == 1024
    
    # Test responsive CSS
    responsive_css = ResponsiveLayout.apply_responsive_css()
    assert "@media" in responsive_css
    assert "max-width: 480px" in responsive_css
    
    print("✅ Responsive Design verification passed")


def verify_integration():
    """Verify the complete UI integration."""
    print("🔗 Verifying UI Integration...")
    
    # Test PharmacologyUI initialization
    ui = PharmacologyUI()
    
    assert ui.theme_manager is not None
    assert ui.chat_interface is not None
    assert ui.auth_interface is not None
    assert ui.settings_interface is not None
    
    # Test message creation
    message = ui.create_message("user", "Test message", "test-model")
    assert message.role == "user"
    assert message.content == "Test message"
    assert message.model_used == "test-model"
    
    # Test theme retrieval
    current_theme = ui.get_current_theme()
    assert current_theme in ["light", "dark"]
    
    print("✅ UI Integration verification passed")


def verify_accessibility_features():
    """Verify accessibility features."""
    print("♿ Verifying Accessibility Features...")
    
    accessibility_css = StyleGenerator.generate_accessibility_styles()
    
    # Check for accessibility features
    accessibility_features = [
        "focus",  # Focus indicators
        "prefers-reduced-motion",  # Reduced motion support
        "prefers-contrast",  # High contrast support
        ".sr-only",  # Screen reader only content
        ".skip-link"  # Skip navigation link
    ]
    
    for feature in accessibility_features:
        assert feature in accessibility_css, f"Missing accessibility feature: {feature}"
    
    print("✅ Accessibility Features verification passed")


def verify_theme_consistency():
    """Verify theme consistency across components."""
    print("🎯 Verifying Theme Consistency...")
    
    theme_manager = ThemeManager()
    
    # Test both themes have all required properties
    for theme_name in ["light", "dark"]:
        config = theme_manager.get_theme_config(theme_name)
        
        required_properties = [
            "name", "primary_color", "background_color", "secondary_background_color",
            "text_color", "accent_color", "user_message_bg", "ai_message_bg",
            "border_color", "shadow_color"
        ]
        
        for prop in required_properties:
            assert hasattr(config, prop), f"Missing property {prop} in {theme_name} theme"
            assert getattr(config, prop) is not None, f"Property {prop} is None in {theme_name} theme"
    
    # Test color format consistency
    light_config = theme_manager.get_theme_config("light")
    dark_config = theme_manager.get_theme_config("dark")
    
    # Colors should be different between themes
    assert light_config.background_color != dark_config.background_color
    assert light_config.text_color != dark_config.text_color
    
    print("✅ Theme Consistency verification passed")


def main():
    """Run all verification tests."""
    print("🚀 Starting UI Implementation Verification...\n")
    
    try:
        verify_theme_manager()
        verify_ui_components()
        verify_style_generator()
        verify_responsive_design()
        verify_integration()
        verify_accessibility_features()
        verify_theme_consistency()
        
        print("\n🎉 All verifications passed! The responsive UI with theme support is working correctly.")
        print("\n📋 Implementation Summary:")
        print("✅ ThemeManager - Light/dark mode switching")
        print("✅ UI Components - Chat interface, auth, settings")
        print("✅ Responsive Design - Mobile, tablet, desktop layouts")
        print("✅ Custom CSS - Beautiful styling for all components")
        print("✅ Message Bubbles - Distinct user vs AI styling")
        print("✅ Accessibility - Focus indicators, reduced motion, high contrast")
        print("✅ Integration - Complete UI system ready for use")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)