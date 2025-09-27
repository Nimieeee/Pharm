# model_ui.py
import streamlit as st
from typing import Optional, Callable
from model_manager import ModelManager, ModelTier, ModelConfig, get_session_model_tier, set_session_model_tier

def render_model_selector(
    model_manager: ModelManager,
    on_change: Optional[Callable[[ModelTier], None]] = None,
    key: str = "model_selector"
) -> ModelTier:
    """
    Render model selection UI with toggle switch and persistence
    
    Args:
        model_manager: ModelManager instance
        on_change: Optional callback function when model changes
        key: Unique key for the widget
        
    Returns:
        Selected model tier
    """
    current_tier = get_session_model_tier()
    
    # Create columns for the toggle
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🤖 AI Model Selection")
        
        # Create toggle switch HTML
        is_premium = current_tier == ModelTier.PREMIUM
        toggle_html = _create_toggle_switch_html(is_premium)
        st.markdown(toggle_html, unsafe_allow_html=True)
        
        # Handle toggle state change with invisible checkbox
        toggle_key = f"{key}_toggle"
        if toggle_key not in st.session_state:
            st.session_state[toggle_key] = is_premium
        
        # Create invisible checkbox to capture state changes
        new_state = st.checkbox(
            "Toggle Model",
            value=st.session_state[toggle_key],
            key=f"{toggle_key}_checkbox",
            label_visibility="collapsed"
        )
        
        # Update session state and provide visual feedback
        if new_state != st.session_state[toggle_key]:
            st.session_state[toggle_key] = new_state
            new_tier = ModelTier.PREMIUM if new_state else ModelTier.FAST
            
            # Update model manager and session
            set_session_model_tier(new_tier)
            model_manager.set_current_model(new_tier)
            
            # Show success message
            model_name = "Premium" if new_state else "Fast"
            st.success(f"✅ Switched to {model_name} mode - preference saved!")
            
            if on_change:
                on_change(new_tier)
            
            # Force rerun to update UI
            st.rerun()
        
        # Display model information
        config = model_manager.get_model_config(current_tier)
        render_model_info(config)
    
    return current_tier

def render_current_model_indicator(current_tier: ModelTier) -> None:
    """
    Render a prominent indicator showing the currently active model
    
    Args:
        current_tier: Currently selected model tier
    """
    if current_tier == ModelTier.FAST:
        st.info("🚀 **Currently Active:** Fast Mode (Gemma2-9B-IT)")
    else:
        st.success("⭐ **Currently Active:** Premium Mode (Qwen3-32B)")

def render_model_info(config: ModelConfig) -> None:
    """
    Render detailed information about the selected model
    
    Args:
        config: ModelConfig to display
    """
    # Model info card
    with st.container():
        st.markdown(f"**{config.display_name}**")
        st.markdown(f"*{config.description}*")
        
        # Create metrics columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Speed",
                value=f"{config.speed_rating}/10",
                help="Response speed rating"
            )
        
        with col2:
            st.metric(
                label="Quality", 
                value=f"{config.quality_rating}/10",
                help="Response quality rating"
            )
        
        with col3:
            st.metric(
                label="Max Tokens",
                value=config.max_tokens,
                help="Maximum response length"
            )

def render_model_status_indicator(model_manager: ModelManager) -> None:
    """
    Render a compact status indicator showing the current active model
    
    Args:
        model_manager: ModelManager instance
    """
    current_config = model_manager.get_current_model()
    current_tier = get_session_model_tier()
    
    # Create a compact status indicator with better styling
    if current_tier == ModelTier.FAST:
        st.markdown(
            '<div style="background-color: #e8f5e8; padding: 8px 12px; border-radius: 20px; text-align: center; border: 1px solid #4caf50;">'
            '<strong>⚡ Fast Mode</strong>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="background-color: #e3f2fd; padding: 8px 12px; border-radius: 20px; text-align: center; border: 1px solid #2196f3;">'
            '<strong>🎯 Premium Mode</strong>'
            '</div>',
            unsafe_allow_html=True
        )

def render_header_model_indicator() -> str:
    """
    Render a minimal model indicator for the header
    
    Returns:
        HTML string for the model indicator
    """
    current_tier = get_session_model_tier()
    
    if current_tier == ModelTier.FAST:
        return "🚀 **Fast**"
    else:
        return "⭐ **Premium**"

def render_model_comparison() -> None:
    """Render a comparison table of available models"""
    st.markdown("### Model Comparison")
    
    # Create comparison data
    comparison_data = {
        "Feature": ["Speed", "Quality", "Max Tokens", "Best For"],
        "Fast Mode (Gemma2-9B-IT)": [
            "⚡⚡⚡⚡⚡ (9/10)",
            "⭐⭐⭐⭐ (7/10)", 
            "1,024 tokens",
            "Quick questions, general topics"
        ],
        "Premium Mode (Qwen3-32B)": [
            "⚡⚡⚡ (6/10)",
            "⭐⭐⭐⭐⭐ (9/10)",
            "2,048 tokens", 
            "Complex analysis, detailed explanations"
        ]
    }
    
    st.table(comparison_data)

def render_model_settings_sidebar(model_manager: ModelManager) -> None:
    """
    Render enhanced model settings in the sidebar with persistence indicators
    
    Args:
        model_manager: ModelManager instance
    """
    with st.sidebar:
        st.markdown("## ⚙️ Model Settings")
        
        # Current model indicator with visual status
        current_config = model_manager.get_current_model()
        current_tier = get_session_model_tier()
        
        if current_tier == ModelTier.FAST:
            st.success(f"🚀 **Active:** {current_config.display_name}")
        else:
            st.info(f"⭐ **Active:** {current_config.display_name}")
        
        # Show if preference is saved
        if 'user_session' in st.session_state and st.session_state.user_session:
            st.caption("💾 Preference saved to your account")
        
        # Quick model switcher with toggle switch
        st.markdown("### Quick Switch")
        
        # Create compact toggle switch for sidebar
        is_premium = current_tier == ModelTier.PREMIUM
        sidebar_toggle_html = f"""
        <div class="sidebar-model-toggle">
            <div class="model-toggle-labels">
                <span class="toggle-label {'active' if not is_premium else ''}">⚡ Fast</span>
                <div class="toggle-switch-wrapper">
                    <label class="toggle-switch">
                        <input type="checkbox" {'checked' if is_premium else ''} onchange="
                            const checkbox = document.querySelector('[data-testid=\\'stCheckbox\\'][data-baseweb=\\'checkbox\\']:last-of-type input');
                            if (checkbox) checkbox.click();
                        ">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <span class="toggle-label {'active' if is_premium else ''}">🎯 Premium</span>
            </div>
        </div>
        """
        st.markdown(sidebar_toggle_html, unsafe_allow_html=True)
        
        # Handle toggle state change
        sidebar_toggle_key = "sidebar_model_toggle"
        if sidebar_toggle_key not in st.session_state:
            st.session_state[sidebar_toggle_key] = is_premium
        
        new_state = st.checkbox(
            "Sidebar Toggle Model",
            value=st.session_state[sidebar_toggle_key],
            key=f"{sidebar_toggle_key}_checkbox",
            label_visibility="collapsed"
        )
        
        if new_state != st.session_state[sidebar_toggle_key]:
            st.session_state[sidebar_toggle_key] = new_state
            new_tier = ModelTier.PREMIUM if new_state else ModelTier.FAST
            
            set_session_model_tier(new_tier)
            model_manager.set_current_model(new_tier)
            
            model_name = "Premium" if new_state else "Fast"
            st.success(f"Switched to {model_name} mode!")
            st.rerun()
        
        # Model comparison
        st.markdown("### Model Comparison")
        
        # Create comparison metrics
        fast_config = model_manager.get_model_config(ModelTier.FAST)
        premium_config = model_manager.get_model_config(ModelTier.PREMIUM)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**⚡ Fast Mode**")
            st.metric("Speed", f"{fast_config.speed_rating}/10")
            st.metric("Quality", f"{fast_config.quality_rating}/10")
            st.caption(f"Max: {fast_config.max_tokens} tokens")
        
        with col2:
            st.markdown("**🎯 Premium Mode**")
            st.metric("Speed", f"{premium_config.speed_rating}/10")
            st.metric("Quality", f"{premium_config.quality_rating}/10")
            st.caption(f"Max: {premium_config.max_tokens} tokens")
        
        # Advanced settings (expandable)
        with st.expander("Advanced Settings"):
            st.markdown("**Temperature:** 0.0 (Deterministic)")
            st.markdown(f"**Current Model ID:** `{current_config.model_id}`")
            st.markdown("**Persistence:** Preferences saved to database")
            
            # Show session info
            if 'user_session' in st.session_state and st.session_state.user_session:
                user_session = st.session_state.user_session
                st.markdown(f"**User:** {user_session.email}")
                st.markdown(f"**Model Pref:** {user_session.model_preference}")

def render_model_selection_modal() -> Optional[ModelTier]:
    """
    Render a modal dialog for model selection
    
    Returns:
        Selected model tier or None if cancelled
    """
    if "show_model_modal" not in st.session_state:
        st.session_state.show_model_modal = False
    
    if st.session_state.show_model_modal:
        with st.container():
            st.markdown("### Choose Your AI Model")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⚡ Fast Mode\n\nQuick responses for general questions", use_container_width=True):
                    st.session_state.show_model_modal = False
                    return ModelTier.FAST
            
            with col2:
                if st.button("🎯 Premium Mode\n\nDetailed analysis for complex topics", use_container_width=True):
                    st.session_state.show_model_modal = False
                    return ModelTier.PREMIUM
            
            if st.button("Cancel"):
                st.session_state.show_model_modal = False
    
    return None

def show_model_selection_modal():
    """Show the model selection modal"""
    st.session_state.show_model_modal = True

def _create_toggle_switch_html(is_premium: bool) -> str:
    """Create HTML for the toggle switch with labels."""
    checked = "checked" if is_premium else ""
    
    return f"""
    <div class="model-toggle-container">
        <div class="model-toggle-labels">
            <span class="toggle-label {'active' if not is_premium else ''}">⚡ Fast</span>
            <div class="toggle-switch-wrapper">
                <label class="toggle-switch">
                    <input type="checkbox" {checked} onchange="
                        const checkbox = document.querySelector('[data-testid=\\'stCheckbox\\'] input');
                        if (checkbox) checkbox.click();
                    ">
                    <span class="toggle-slider"></span>
                </label>
            </div>
            <span class="toggle-label {'active' if is_premium else ''}">🎯 Premium</span>
        </div>
        <div class="model-description">
            {'High-quality responses for complex topics' if is_premium else 'Quick responses for general questions'}
        </div>
    </div>
    """