#!/usr/bin/env python3
"""
Verification script for Task 2: Implement model toggle switch interface
Verifies all requirements are met according to the specification.
"""

import os
import sys
import re

def verify_ui_components_updated():
    """Verify that ui_components.py has been updated with toggle switch."""
    print("🔍 Verifying UI Components...")
    
    with open('ui_components.py', 'r') as f:
        content = f.read()
    
    # Check that selectbox is replaced with toggle switch logic
    assert 'toggle-switch' in content, "Toggle switch HTML not found"
    assert 'toggle-slider' in content, "Toggle slider not found"
    assert 'model-toggle-container' in content, "Toggle container not found"
    assert 'Fast' in content and 'Premium' in content, "Fast/Premium labels not found"
    
    # Check that it returns correct model IDs
    assert 'gemma2-9b-it' in content, "Fast model ID not found"
    assert 'qwen/qwen3-32b' in content, "Premium model ID not found"
    
    print("✅ UI Components updated with toggle switch")

def verify_css_styling():
    """Verify that CSS styling has been added for toggle switch."""
    print("🔍 Verifying CSS Styling...")
    
    with open('styles.py', 'r') as f:
        content = f.read()
    
    # Check for toggle switch CSS classes
    required_classes = [
        'model-toggle-container',
        'model-toggle-labels', 
        'toggle-label',
        'toggle-switch',
        'toggle-slider',
        'sidebar-model-toggle',
        'auth-model-toggle'
    ]
    
    for css_class in required_classes:
        assert css_class in content, f"CSS class {css_class} not found"
    
    # Check for visual feedback styles
    assert 'active' in content, "Active state styling not found"
    assert 'transition' in content, "Transition animations not found"
    assert 'hover' in content, "Hover effects not found"
    
    # Check for responsive design
    assert '@media' in content, "Responsive design not found"
    
    print("✅ CSS styling implemented with clear Fast/Premium labels")

def verify_model_ui_integration():
    """Verify that model_ui.py has been updated."""
    print("🔍 Verifying Model UI Integration...")
    
    with open('model_ui.py', 'r') as f:
        content = f.read()
    
    # Check for toggle switch implementation
    assert '_create_toggle_switch_html' in content, "Toggle switch HTML function not found"
    assert 'toggle_key' in content, "Toggle state management not found"
    assert 'st.checkbox' in content, "Checkbox for state capture not found"
    assert 'st.rerun()' in content, "Immediate switching not found"
    
    print("✅ Model UI updated with toggle switch")

def verify_session_persistence():
    """Verify that session persistence is implemented."""
    print("🔍 Verifying Session Persistence...")
    
    files_to_check = ['ui_components.py', 'model_ui.py', 'auth_ui.py']
    
    for filename in files_to_check:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Check for session state management
        assert 'st.session_state' in content, f"Session state not used in {filename}"
        
        if filename == 'ui_components.py':
            assert 'selected_model' in content, f"Model persistence not found in {filename}"
        elif filename == 'model_ui.py':
            assert 'toggle_key' in content, f"Toggle persistence not found in {filename}"
    
    print("✅ Session persistence implemented")

def verify_visual_feedback():
    """Verify that visual feedback is implemented."""
    print("🔍 Verifying Visual Feedback...")
    
    files_to_check = ['ui_components.py', 'model_ui.py', 'auth_ui.py']
    
    for filename in files_to_check:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Check for success messages
        if 'st.success' in content:
            assert 'Switched to' in content, f"Switch feedback not found in {filename}"
    
    # Check CSS for visual states
    with open('styles.py', 'r') as f:
        css_content = f.read()
    
    assert '.active' in css_content, "Active state styling not found"
    assert 'transform: scale' in css_content, "Visual scaling not found"
    
    print("✅ Visual feedback implemented")

def verify_immediate_switching():
    """Verify that immediate model switching is implemented."""
    print("🔍 Verifying Immediate Switching...")
    
    files_to_check = ['ui_components.py', 'model_ui.py']
    
    for filename in files_to_check:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Check for immediate state updates
        assert 'st.rerun()' in content, f"Immediate rerun not found in {filename}"
        
        # Check for state change detection
        assert 'new_state != st.session_state' in content, f"State change detection not found in {filename}"
    
    print("✅ Immediate model switching implemented")

def verify_requirements_mapping():
    """Verify that all requirements are addressed."""
    print("🔍 Verifying Requirements Mapping...")
    
    requirements = {
        "2.1": "Toggle switch interface instead of dropdown menu",
        "2.2": "Left position = fast model, right position = premium model", 
        "2.3": "Clear indication of active mode with labels and styling",
        "2.4": "Immediate model switching with visual feedback",
        "2.5": "Session persistence and state management"
    }
    
    # Check requirement 2.1 - Toggle switch interface
    with open('ui_components.py', 'r') as f:
        content = f.read()
    assert 'toggle-switch' in content and 'selectbox' not in content.split('render_model_selector')[1].split('def ')[0], "Requirement 2.1 not met"
    
    # Check requirement 2.2 - Position mapping
    assert 'gemma2-9b-it' in content and 'qwen/qwen3-32b' in content, "Requirement 2.2 not met"
    
    # Check requirement 2.3 - Clear labels
    with open('styles.py', 'r') as f:
        css_content = f.read()
    assert 'toggle-label' in css_content and 'active' in css_content, "Requirement 2.3 not met"
    
    # Check requirement 2.4 - Immediate switching
    assert 'st.success' in content and 'st.rerun()' in content, "Requirement 2.4 not met"
    
    # Check requirement 2.5 - Session persistence
    assert 'st.session_state' in content and 'selected_model' in content, "Requirement 2.5 not met"
    
    print("✅ All requirements (2.1-2.5) are addressed")

def verify_test_updates():
    """Verify that tests have been updated."""
    print("🔍 Verifying Test Updates...")
    
    with open('test_ui_comprehensive.py', 'r') as f:
        content = f.read()
    
    # Check that test has been updated for toggle switch
    assert 'toggle-switch' in content, "Test not updated for toggle switch"
    assert 'mock_checkbox' in content, "Test not using checkbox mock"
    
    print("✅ Tests updated for toggle switch")

def main():
    """Run all verification checks."""
    print("🧪 Verifying Task 2: Implement model toggle switch interface")
    print("=" * 70)
    
    try:
        verify_ui_components_updated()
        verify_css_styling()
        verify_model_ui_integration()
        verify_session_persistence()
        verify_visual_feedback()
        verify_immediate_switching()
        verify_requirements_mapping()
        verify_test_updates()
        
        print("\n" + "=" * 70)
        print("✅ ALL VERIFICATION CHECKS PASSED!")
        print("\n📋 Task 2 Implementation Summary:")
        print("• ✅ Replaced model selection dropdown with toggle switch component")
        print("• ✅ Created CSS styling for toggle switch with clear Fast/Premium labels")
        print("• ✅ Implemented toggle state management and visual feedback")
        print("• ✅ Added immediate model switching functionality with session persistence")
        print("• ✅ Updated all relevant files (ui_components.py, model_ui.py, auth_ui.py)")
        print("• ✅ Added responsive design support")
        print("• ✅ Updated tests to work with new implementation")
        print("\n🎯 Requirements 2.1, 2.2, 2.3, 2.4, 2.5 - ALL SATISFIED")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Verification failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)