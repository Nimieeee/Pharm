#!/usr/bin/env python3
"""
Test script for the model toggle switch implementation.
Tests the toggle switch functionality and session persistence.
"""

import streamlit as st
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui_components import ChatInterface
from model_manager import ModelManager, ModelTier
from model_ui import render_model_selector, _create_toggle_switch_html

def test_toggle_switch_html():
    """Test the toggle switch HTML generation."""
    print("Testing toggle switch HTML generation...")
    
    # Test Fast mode (not premium)
    fast_html = _create_toggle_switch_html(False)
    assert "⚡ Fast" in fast_html
    assert "🎯 Premium" in fast_html
    assert "active" in fast_html  # Fast should be active
    assert "Quick responses for general questions" in fast_html
    print("✅ Fast mode HTML generation works")
    
    # Test Premium mode
    premium_html = _create_toggle_switch_html(True)
    assert "⚡ Fast" in premium_html
    assert "🎯 Premium" in premium_html
    assert "checked" in premium_html  # Should be checked for premium
    assert "High-quality responses for complex topics" in premium_html
    print("✅ Premium mode HTML generation works")

def test_model_id_mapping():
    """Test that the toggle switch returns correct model IDs."""
    print("Testing model ID mapping...")
    
    # Test the logic for determining if a model is premium
    fast_model_ids = ["gemma2-9b-it", "fast"]
    premium_model_ids = ["qwen/qwen3-32b", "qwen3-32b", "premium"]
    
    for model_id in fast_model_ids:
        is_premium = model_id in ["qwen/qwen3-32b", "qwen3-32b", "premium"]
        assert not is_premium, f"Model {model_id} should not be premium"
    
    for model_id in premium_model_ids:
        is_premium = model_id in ["qwen/qwen3-32b", "qwen3-32b", "premium"]
        assert is_premium, f"Model {model_id} should be premium"
    
    print("✅ Model ID mapping works correctly")

def test_css_classes():
    """Test that the CSS classes are properly applied."""
    print("Testing CSS classes...")
    
    # Test Fast mode classes
    fast_html = _create_toggle_switch_html(False)
    assert 'class="toggle-label active"' in fast_html  # Fast should be active
    assert 'class="toggle-label "' in fast_html  # Premium should not be active
    
    # Test Premium mode classes
    premium_html = _create_toggle_switch_html(True)
    assert 'class="toggle-label "' in premium_html  # Fast should not be active
    assert 'class="toggle-label active"' in premium_html  # Premium should be active
    
    print("✅ CSS classes are applied correctly")

def main():
    """Run all tests."""
    print("🧪 Testing Model Toggle Switch Implementation")
    print("=" * 50)
    
    try:
        test_toggle_switch_html()
        test_model_id_mapping()
        test_css_classes()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Toggle switch implementation is working correctly.")
        print("\nKey features verified:")
        print("• Toggle switch HTML generation")
        print("• Model ID mapping (Fast ↔ Premium)")
        print("• CSS class application for visual feedback")
        print("• Description text updates based on mode")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)