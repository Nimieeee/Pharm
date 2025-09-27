#!/usr/bin/env python3
"""
Demo script for the model toggle switch implementation.
Run with: streamlit run model_toggle_demo.py
"""

import streamlit as st
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui_components import ChatInterface
from theme_manager import ThemeManager
from model_manager import ModelManager, ModelTier, get_session_model_tier, set_session_model_tier
from model_ui import render_model_selector

def main():
    """Main demo function."""
    st.set_page_config(
        page_title="Model Toggle Switch Demo",
        page_icon="🔄",
        layout="wide"
    )
    
    # Initialize theme manager and apply styles
    theme_manager = ThemeManager()
    theme_manager.apply_theme()
    
    st.title("🔄 Model Toggle Switch Demo")
    st.markdown("---")
    
    # Initialize model manager
    try:
        model_manager = ModelManager()
    except ValueError as e:
        st.error(f"Failed to initialize ModelManager: {e}")
        st.info("Please set your GROQ_API_KEY environment variable")
        return
    
    # Demo 1: UI Components Toggle Switch
    st.header("1. UI Components Toggle Switch")
    st.markdown("This demonstrates the toggle switch in the ChatInterface component:")
    
    # Create ChatInterface
    chat_interface = ChatInterface(theme_manager)
    
    # Available models for the demo
    available_models = [
        {"id": "gemma2-9b-it", "name": "Fast Mode", "description": "Quick responses"},
        {"id": "qwen/qwen3-32b", "name": "Premium Mode", "description": "High quality responses"}
    ]
    
    # Get current model from session state
    current_model = st.session_state.get("selected_model", "gemma2-9b-it")
    
    # Render the toggle switch
    selected_model = chat_interface.render_model_selector(current_model, available_models)
    
    # Show the result
    st.info(f"Selected Model: **{selected_model}**")
    
    st.markdown("---")
    
    # Demo 2: Model UI Toggle Switch
    st.header("2. Model UI Toggle Switch")
    st.markdown("This demonstrates the enhanced model selector with detailed information:")
    
    # Render the enhanced model selector
    selected_tier = render_model_selector(model_manager, key="demo_selector")
    
    # Show current configuration
    config = model_manager.get_model_config(selected_tier)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Speed Rating", f"{config.speed_rating}/10")
    with col2:
        st.metric("Quality Rating", f"{config.quality_rating}/10")
    with col3:
        st.metric("Max Tokens", config.max_tokens)
    
    st.markdown("---")
    
    # Demo 3: Session Persistence
    st.header("3. Session Persistence")
    st.markdown("Your model selection is automatically saved:")
    
    current_tier = get_session_model_tier()
    st.success(f"Current session preference: **{current_tier.value.title()} Mode**")
    
    # Show session state
    with st.expander("Session State Details"):
        st.json({
            "selected_model": st.session_state.get("selected_model", "Not set"),
            "model_toggle_switch": st.session_state.get("model_toggle_switch", "Not set"),
            "current_tier": current_tier.value
        })
    
    st.markdown("---")
    
    # Demo 4: Visual Feedback
    st.header("4. Visual Feedback")
    st.markdown("The toggle switch provides immediate visual feedback:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Fast Mode Features:**")
        st.markdown("• ⚡ Quick responses")
        st.markdown("• 🚀 High speed (9/10)")
        st.markdown("• 📝 1,024 max tokens")
        st.markdown("• 💡 Good for general questions")
    
    with col2:
        st.markdown("**Premium Mode Features:**")
        st.markdown("• 🎯 Detailed responses")
        st.markdown("• ⭐ High quality (9/10)")
        st.markdown("• 📚 2,048 max tokens")
        st.markdown("• 🧠 Good for complex topics")
    
    # Footer
    st.markdown("---")
    st.markdown("**Implementation Features:**")
    st.markdown("✅ Toggle switch replaces dropdown")
    st.markdown("✅ Clear Fast/Premium labels")
    st.markdown("✅ Visual feedback and state management")
    st.markdown("✅ Session persistence")
    st.markdown("✅ Immediate model switching")

if __name__ == "__main__":
    main()